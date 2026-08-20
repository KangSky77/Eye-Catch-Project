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
    r"가능성이\s*(?:매우\s*)?낮", r"위험이\s*(?:매우\s*)?낮", r"아닐\s*가능성",
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

# 문장 분리 — 한국어 마침표/일본어 구두점/영문 종결부호
_SENT_SPLIT = re.compile(r"(?<=[.!?。！？])\s+|\n+")


def _diseases_in(sentence: str) -> set:
    found = set()
    low = sentence.lower()
    for key, terms in DISEASE_TERMS.items():
        if any(t.lower() in low for t in terms):
            found.add(key)
    return found


def check_sentence(sentence: str) -> str | None:
    """위반 사유를 반환. 문제없으면 None."""
    if any(p.search(sentence) for p in _PROB):
        return "probability"          # 보정되지 않은 점수를 확률로 말함
    if any(p.search(sentence) for p in _EXCL):
        return "exclusion"            # 스크리닝으로 배제 불가
    if any(p.search(sentence) for p in _DIAG):
        return "diagnosis"            # 확정 진단
    if len(_diseases_in(sentence)) >= 2:
        return "cross_disease"        # 한 문장에서 질환 간 관계를 지어냄
    return None


def sanitize(text: str) -> tuple[str, list[str]]:
    """위험 문장을 제거한 본문과 제거 사유 목록을 반환.

    문장 단위로 버리는 이유: 한 문장이 틀렸다고 전체를 버리면 쓸 만한 생활 조언까지
    사라지고, 반대로 통째로 통과시키면 틀린 의학 문장이 그대로 노출된다.
    """
    kept, reasons = [], []
    for raw in _SENT_SPLIT.split(text or ""):
        s = raw.strip()
        if not s:
            continue
        why = check_sentence(s)
        if why:
            reasons.append(why)
        else:
            kept.append(s)
    return " ".join(kept).strip(), reasons
