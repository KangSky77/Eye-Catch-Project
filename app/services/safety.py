"""
LLM 출력 안전 필터
================================================================
왜 필요한가 (실제 재현된 사고):
    외부 리뷰에서 Gemma가 이런 문장을 생성한 것이 확인됐다.

        "암슬러 격자가 정상이므로 녹내장과 관련된 심각한 황반부 문제 가능성이 낮다"

    한 문장에 오류가 셋이다.
      1) 암슬러는 황반(중심시야) 자가검사인데 녹내장 결론을 냈다 — 질환을 섞었다
      2) 정상 결과로 질환 가능성을 '배제'했다 — 스크리닝 검사로는 배제할 수 없다
      3) 모델 softmax 점수를 질병 발생 확률처럼 해석했다 — 보정된 확률이 아니다

    RAG는 '무엇을 참고할지'만 주입할 뿐, 모델이 질환 간 인과를 지어내는 것은 막지 못한다.
    프롬프트의 "확정 진단을 하지 말라"는 지시도 이런 유형의 오류는 막지 못했다.

대응 구조 (2단 방어):
    1단 — LLM에게 애초에 해석을 시키지 않는다.
           검사 결과 해석은 프론트가 코드로 결정론적으로 생성하고(app-findings.js),
           LLM은 '생활 관리 조언'만 쓴다. 수치도 프롬프트에 넣지 않는다.
    2단 — 그래도 새어 나온 위험 표현을 이 모듈이 걸러낸다.
           위반이 발견되면 해당 문장을 버린다. 전부 버려지면 LLM 섹션 자체를 비운다.
           (틀린 의학 문장을 보여주느니 아무것도 안 보여주는 쪽이 안전하다)
"""
import re

# 질환명 — 한 문장에 둘 이상 나오면 질환 간 관계를 지어냈을 가능성이 높다
DISEASE_TERMS = {
    "cataract": ["백내장", "cataract", "catarata", "cataracte", "白内障", "白内障"],
    "macular": ["황반", "macular", "macula", "AMD", "黄斑", "黄斑"],
    "glaucoma": ["녹내장", "glaucoma", "glaucome", "緑内障", "青光眼"],
    "retinopathy": ["망막병증", "retinopathy", "retinopatía", "rétinopathie", "網膜症", "视网膜病变"],
}

# 스크리닝 결과로는 할 수 없는 '배제' 표현
EXCLUSION_PATTERNS = [
    # 조사를 고정하면 "가능성은 낮습니다"가 그대로 빠져나간다(2026-09-15 실측).
    r"가능성[이은도가]?\s*(?:매우\s*)?낮", r"위험[이은도가]?\s*(?:매우\s*)?낮", r"아닐\s*가능성",
    r"배제(?:할\s*수\s*있|됩니다|된다)", r"걱정하지\s*않으셔도", r"안심하셔도",
    r"정상입니다", r"이상\s*없습니다",
    r"\bunlikely\b", r"\brule[sd]?\s+out\b", r"\bno\s+need\s+to\s+worry\b",
    r"\blow\s+(?:risk|likelihood|probability)\b", r"\bnot\s+at\s+risk\b",
    r"心配(?:は)?(?:いりません|ありません)", r"可能性(?:は)?低",
    r"不必担心", r"可能性(?:很)?低",
    r"\bpoco\s+probable\b", r"\bpeu\s+probable\b",
]

# 보정되지 않은 softmax 점수를 '확률'로 말하는 표현 (수치 언급 자체를 금지)
PROBABILITY_PATTERNS = [
    r"\d+\s*(?:\.\d+)?\s*%",
    r"확률(?:이|은|로|가)", r"\bprobability\b", r"\bchance\s+of\b",
]

# 확정 진단 표현
DIAGNOSIS_PATTERNS = [
    r"(?:진단|확진)(?:입니다|됩니다|된다|받으셨)", r"\byou\s+have\b", r"\bdiagnos(?:ed|is)\s+(?:with|of)\b",
    r"確定診断", r"确诊",
]

_EXCL = [re.compile(p, re.I) for p in EXCLUSION_PATTERNS]
_PROB = [re.compile(p, re.I) for p in PROBABILITY_PATTERNS]
_DIAG = [re.compile(p, re.I) for p in DIAGNOSIS_PATTERNS]

# 문장 분리 — 한국어 마침표/일본어 구두점/영문 종결부호.
# 공개 이름으로 둔다: llm.py의 스트리밍 필터(sanitized_stream)가 같은 규칙으로 문장을
# 잘라야 하는데, 예전에는 비공개 이름(_SENT_SPLIT)을 밖에서 참조하고 있었다.
# 여기서만 규칙을 고치면 스트리밍·일괄(sanitize) 양쪽이 함께 바뀐다.
SENT_SPLIT = re.compile(r"(?<=[.!?。！？])\s+|\n+")
_SENT_SPLIT = SENT_SPLIT   # 이전 이름 호환(외부 참조가 남아 있어도 깨지지 않도록)


def _diseases_in(sentence: str) -> set:
    found = set()
    low = sentence.lower()
    for key, terms in DISEASE_TERMS.items():
        if any(t.lower() in low for t in terms):
            found.add(key)
    return found


# 문진에서 '최근 검진 없음'이 잡혔는데 소견이 있지도 않은 검진 이력을 전제로 쓰는 경우.
#
# 왜 필터가 필요한가: 프롬프트로 "'없음'을 '있음'으로 뒤집지 말라"고 못 박아도 소형 모델은
# 여덟 번에 한 번꼴로 "2년 동안의 검진 기록을 바탕으로"처럼 되돌린다(2026-09-18 실측).
# 리포트 세 줄 위에 "2년 내 검진 없음"이 그대로 적혀 있어서 사용자는 모순을 바로 본다.
#
# 부정형("검진 기록이 없으므로", "검진을 받지 못했")은 맞는 문장이므로 지우면 안 된다.
# 그래서 '있다고 단정하는 형태'만 좁게 고른다.
_CLAIMS_PAST_EXAM = [
    re.compile(r"검진\s*(?:이력|기록)[이은가를을]?\s*(?:있|바탕|토대)"),
    re.compile(r"(?:전에|년\s*전에?|이전에)\s*(?:받으신|받았던)?\s*검진"),
    re.compile(r"검진(?:을|를)?\s*받으셨"),
    re.compile(r"(?:마지막|지난)\s*검진(?:은|이|에서)"),
]
# '없다'는 뜻이 같은 문장 안에 있으면 위 표현이 걸려도 올바른 문장이다.
_EXAM_NEGATED = re.compile(r"없|못\s*했|않[은았으]|미[실시]|안\s*받")

# 문진 항목이 '최근 검진 없음'을 뜻하는지 (6개 언어의 sym_chk_recent 문구)
_NO_RECENT_EXAM_ITEM = re.compile(
    r"검진\s*없음|No exam in|Sin revisión|Aucun examen|検診なし|未做过检查", re.I)


def contradicts_facts(sentence: str, facts: list[str] | None) -> bool:
    """문진에서 확인된 사실과 정면으로 어긋나는 문장인가."""
    if not facts:
        return False
    if not any(_NO_RECENT_EXAM_ITEM.search(f or "") for f in facts):
        return False
    if _EXAM_NEGATED.search(sentence):
        return False
    return any(p.search(sentence) for p in _CLAIMS_PAST_EXAM)


def check_sentence(sentence: str, facts: list[str] | None = None) -> str | None:
    """위반 사유를 반환. 문제없으면 None.

    facts: 문진에서 확인된 항목. 넘기면 그 사실과 어긋나는 문장도 걸러낸다."""
    if contradicts_facts(sentence, facts):
        return "contradicts_facts"    # 없는 이력을 지어냄
    if any(p.search(sentence) for p in _PROB):
        return "probability"          # 보정되지 않은 점수를 확률로 말함
    if any(p.search(sentence) for p in _EXCL):
        return "exclusion"            # 스크리닝으로 배제 불가
    if any(p.search(sentence) for p in _DIAG):
        return "diagnosis"            # 확정 진단
    if len(_diseases_in(sentence)) >= 2:
        return "cross_disease"        # 한 문장에서 질환 간 관계를 지어냄
    return None


def sanitize(text: str, facts: list[str] | None = None) -> tuple[str, list[str]]:
    """위험 문장을 제거한 본문과 제거 사유 목록을 반환.

    문장 단위로 버리는 이유: 한 문장이 틀렸다고 전체를 버리면 쓸 만한 생활 조언까지
    사라지고, 반대로 통째로 통과시키면 틀린 의학 문장이 그대로 노출된다.
    """
    kept, reasons = [], []
    for raw in SENT_SPLIT.split(text or ""):
        s = raw.strip()
        if not s:
            continue
        why = check_sentence(s, facts)
        if why:
            reasons.append(why)
        else:
            kept.append(s)
    return " ".join(kept).strip(), reasons
