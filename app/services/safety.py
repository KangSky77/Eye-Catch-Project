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
    r"(?:진단|확진)(?:입니다|됩니다|된다|받으셨)",
    # 맨 'you have'는 "If you have pain…", "you have not had an exam…" 같은 평범한 조언까지 지웠다.
    r"\byou\s+(?:(?:may|might|probably|likely|clearly)\s+)?have\s+(?:an?\s+)?(?:\w+\s+){0,2}?"
    r"(?:cataracts?|glaucoma|macular|amd|retinopathy|disease|degeneration|infection|complication)",
    r"\bdiagnos(?:ed|is)\s+(?:with|of)\b",
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
    re.compile(r"검진을?\s*계속|계속\s*(?:정기\s*)?검진"),
    # 다른 언어 — 2026-09-23 영어 소견이 '2년 내 검진 없음'인 사람에게 "Continue with regular eye check-ups"를 썼다.
    re.compile(r"\bcontinu\w*\s+(?:with\s+)?(?:your\s+)?(?:regular|routine|annual|periodic)?\s*(?:eye\s+)?"
               r"(?:check-?ups?|exams?|examinations?|screenings?|visits?)", re.I),
    re.compile(r"\b(?:your|the)\s+(?:last|previous|recent|past)\s+(?:eye\s+)?(?:check-?up|exam|examination|screening)", re.I),
    re.compile(r"\bsince\s+you\s+(?:have\s+|recently\s+)?had\s+(?:an?\s+)?(?:eye\s+)?(?:check-?up|exam)", re.I),
    re.compile(r"\bkeep\s+up\s+(?:with\s+)?your\s+(?:regular\s+)?(?:eye\s+)?(?:check-?ups|exams)", re.I),
    re.compile(r"contin[úu]\w*\s+con\s+sus\s+revisiones|su\s+[úu]ltima\s+revisi[óo]n", re.I),
    re.compile(r"continuez\s+(?:vos|les)\s+(?:examens|contr[ôo]les)|votre\s+dernier\s+(?:examen|contr[ôo]le)", re.I),
    re.compile(r"前回の(?:検診|検査|眼科)|引き続き.{0,8}(?:検診|検査)"),
    re.compile(r"上次(?:的)?(?:眼科)?检查|继续.{0,6}(?:定期)?检查"),
]
# '없다'는 뜻이 같은 문장 안에 있으면 위 표현이 걸려도 올바른 문장이다.
_EXAM_NEGATED = re.compile(r"없|못\s*했|않[은았으]|미[실시]|안\s*받"
                           r"|\b(?:no|not|never|haven't|hasn't|without|overdue|missed)\b"
                           r"|\bnunca\b|\bsin\b|\bjamais\b|\bsans\b|受けていない|していない|没有|未曾", re.I)

# 문진 항목이 '최근 검진 없음'을 뜻하는지 (6개 언어의 sym_chk_recent 문구)
_NO_RECENT_EXAM_ITEM = re.compile(
    r"검진\s*없음|No exam in|Sin revisión|Aucun examen|検診なし|未做过检查", re.I)

_NO_HYPERTENSION_ITEM = re.compile(r"^Hypertension:\s*no$", re.I)
_NO_DIABETES_ITEM = re.compile(r"^Diabetes:\s*no$", re.I)
_PERSONAL_BP_ADVICE = re.compile(
    r"혈압\s*(?:을|을\s*꾸준히)?\s*(?:관리|조절|조정|유지|낮추)"
    r"|(?:manage|control|monitor|keep\s+track\s+of|lower)\s+(?:your\s+)?blood\s+pressure"
    r"|keep\s+(?:your\s+)?blood\s+pressure\s+(?:under\s+control|stable|in\s+check)"
    r"|(?:gestione|controle|surveillez|contrôlez|g[eé]rez)\s+(?:su|votre)\s+(?:presi[oó]n\s+arterial|tension\s+art[eé]rielle)"
    r"|血圧(?:を)?(?:管理|コントロール)|控制血压|管理血压", re.I)
_PERSONAL_GLUCOSE_ADVICE = re.compile(
    r"혈당\s*(?:을)?\s*(?:관리|조절|조정|유지|낮추)"
    r"|(?:manage|control|monitor|lower)\s+(?:your\s+)?blood\s+(?:sugar|glucose)"
    r"|血糖(?:を)?(?:管理|コントロール)|控制血糖|管理血糖", re.I)


# 밤·어두운 곳에서 선글라스·색 렌즈 권유. 2026-09-23 실사용 테스트에서 "밤 운전 눈부심을 줄이는 방법"에
# 선글라스를 권했다 — 야간에는 시야가 더 어두워져 위험하다. 문제 문장 자체에는 '밤'이 없고 질문에 있었으므로,
# 질문이 밤·어둠에 관한 것이면(night_context) 문장에 '밤'이 없어도 거른다. 하지 말라는 문장은 남긴다.
_TINT = re.compile(r"선글라스|색안경|착색\s*렌즈|틴트\s*렌즈|sunglass|tinted|gafas de sol|lunettes de soleil|verres teint"
                   r"|(?:yellow|amber)\s+(?:lenses|glasses)|lentes? amarill[oa]s?|verres jaunes"
                   r"|サングラス|色付き|黄色い?レンズ|墨镜|太阳镜|有色镜片|黄色镜片", re.I)
_NIGHT = re.compile(r"밤|야간|어두운|어두울|\bnight|\bdark|noche|nocturn|oscur|nuit|sombre|夜|暗い|暗所|晚上|夜间|夜晚|黑暗|昏暗", re.I)
_TINT_DIRECT_WARNING = re.compile(
    r"(?:avoid|don't|do not|never|not\s+recommend)\s+(?:(?:wear|wearing|use|using|put\s+on)\s+)?"
    r"(?:sunglass|tinted|(?:yellow|amber)\s+(?:lenses|glasses))"
    r"|(?:evite|nunca|évitez|jamais)\s+(?:(?:usar|utiliser|porter|les|des)\s+){0,2}"
    r"(?:gafas de sol|lunettes de soleil|verres teint)"
    r"|(?:避免|不要|切勿)(?:佩戴|戴|使用)?(?:墨镜|太阳镜|有色镜片)"
    r"|(?:선글라스|색안경|착색\s*렌즈|サングラス|色付き|墨镜|太阳镜|有色镜片)"
    r"[^.!?。！？,，:：;；]{0,24}(?:쓰지\s*마|하지\s*마|말아|피하|삼가|권하지\s*않|권장하지\s*않|避け|しないで|ないでください)", re.I)
_TINT_LONG_WARNING = re.compile(
    r"(?:선글라스|색안경|착색\s*렌즈|색이\s*들어간\s*렌즈)"
    r"[^.!?。！？,，;；]{0,120}(?:절대\s*)?(?:권하지\s*않|추천하지\s*않|권장하지\s*않)", re.I)


# 운전 중 눈을 감으라는 조언. 2026-09-23 재테스트: '밤 운전 눈부심' 질문에 "운전 환경의 조명을 확인하고
# 주기적으로 눈을 감거나 깜박여 눈에 휴식을 주는 것이 도움이 됩니다"가 나왔다(프롬프트의 '눈 휴식' 조언을
# 운전 상황에 끼워 넣음). 하지 말라는 문장("운전 중에는 눈을 감지 마세요")은 남긴다.
_DRIVING = re.compile(r"운전|driv|conduc|conduis|conduire|運転|开车|驾驶", re.I)
_EYES_CLOSED = re.compile(r"눈(?:을)?(?:\s+(?:잠시|자주|주기적으로|가끔|몇\s*초(?:간)?|계속))*\s*감"
                          r"|(?:close|shut)\s+(?:your\s+)?eyes|cierr\w*\s+los\s+ojos|ferm\w*\s+les\s+yeux"
                          r"|目を閉じ|闭上眼|闭眼", re.I)
_EYE_CLOSE_WARNING = re.compile(r"눈을?\s*감지\s*마|감으면\s*안|(?:avoid|do\s+not|don't|never)\s+(?:closing|close|shutting|shut)\s+(?:your\s+)?eyes"
                                r"|目を閉じない|目を閉じてはいけ|不要闭眼|不要闭上眼", re.I)

_MAX_HEADLIGHTS = re.compile(
    r"전조등.{0,12}(?:최대|최고|가장\s*밝)|(?:상향등|하이빔).{0,10}(?:항상|계속)"
    r"|(?:always|constantly|at\s+all\s+times).{0,20}(?:high\s+beams?|headlights?)"
    r"|(?:high\s+beams?|headlights?).{0,20}(?:always|at\s+full|maximum)", re.I)
_HEADLIGHT_WARNING = re.compile(r"(?:최대|최고|항상|계속).{0,12}(?:켜지\s*마|사용하지\s*마|피하)"
                                r"|(?:do\s+not|don't|never|avoid).{0,20}(?:high\s+beams?|maximum\s+headlights?)", re.I)


def advises_closing_eyes_while_driving(sentence: str, driving_context: bool = False) -> bool:
    return bool((driving_context or _DRIVING.search(sentence)) and _EYES_CLOSED.search(sentence)
                and not _EYE_CLOSE_WARNING.search(sentence))


def advises_maximum_headlights(sentence: str, driving_context: bool = False) -> bool:
    return bool((driving_context or _DRIVING.search(sentence)) and _MAX_HEADLIGHTS.search(sentence)
                and not _HEADLIGHT_WARNING.search(sentence))


def mentions_driving(text: str) -> bool:
    return bool(_DRIVING.search(text or ""))


def mentions_night(text: str) -> bool:
    return bool(_NIGHT.search(text or ""))


def recommends_tint_at_night(sentence: str, night_context: bool = False) -> bool:
    if not _TINT.search(sentence) or _TINT_DIRECT_WARNING.search(sentence) or _TINT_LONG_WARNING.search(sentence):
        return False
    return night_context or bool(_NIGHT.search(sentence))


def contradicts_facts(sentence: str, facts: list[str] | None) -> bool:
    """문진에서 확인된 사실과 정면으로 어긋나는 문장인가."""
    if not facts:
        return False
    if any(_NO_HYPERTENSION_ITEM.search(f or "") for f in facts) and _PERSONAL_BP_ADVICE.search(sentence):
        return True
    if any(_NO_DIABETES_ITEM.search(f or "") for f in facts) and _PERSONAL_GLUCOSE_ADVICE.search(sentence):
        return True
    if not any(_NO_RECENT_EXAM_ITEM.search(f or "") for f in facts):
        return False
    # A negation in an earlier clause must not excuse a contradictory claim in
    # the next one: "No recent exam; continue with regular check-ups."
    clauses = re.split(r"[,，;；]", sentence)
    return any(any(p.search(clause) for p in _CLAIMS_PAST_EXAM)
               and not _EXAM_NEGATED.search(clause) for clause in clauses)


def check_sentence(sentence: str, facts: list[str] | None = None, night_context: bool = False,
                   driving_context: bool = False) -> str | None:
    """위반 사유를 반환. 문제없으면 None.

    facts: 문진에서 확인된 항목. 넘기면 그 사실과 어긋나는 문장도 걸러낸다.
    night_context: 질문이 밤·어둠에 관한 것이면 선글라스 권유를 문장에 '밤'이 없어도 거른다."""
    if contradicts_facts(sentence, facts):
        return "contradicts_facts"    # 없는 이력을 지어냄
    if recommends_tint_at_night(sentence, night_context):
        return "night_tint"           # 야간 선글라스·색 렌즈 권유
    if advises_closing_eyes_while_driving(sentence, driving_context):
        return "driving_eyes_closed"  # 운전 중 눈 감기 권유
    if advises_maximum_headlights(sentence, driving_context):
        return "driving_max_headlights"  # 다른 운전자 눈부심 위험
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
