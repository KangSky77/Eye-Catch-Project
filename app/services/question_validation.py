"""Format, script and yes/no validation shared by generated questions."""

import re

# 화면에는 '네/아니오' 버튼뿐이라, 서술형 질문이 나오면 사용자가 답할 방법이 없다.
# 프롬프트로 제약을 걸어도 LLM이 가끔 어기므로 서버에서 한 번 더 거른다.
# 걸러진 질문은 버리지 않고 answer_type='text'로 넘겨 자유 입력칸으로 받는다.
#
# 판별의 핵심은 '의문사가 들어 있는가'다 — 의문사가 있으면 예/아니오로 답이 성립하지 않는다.
# 2026-09-17: "두 눈 중 어느 눈이 유독 더 뿌옇게 보이나요?"가 통과해 네/아니오 버튼만 떴다.
# 굳어진 표현('어느 정도')만 막고 있어서 의문사 '어느' 자체는 그대로 통과했다.

# 라틴 문자권 의문사 — 단어 경계로 찾는다("somewhat"의 what처럼 낱말 속에 묻힌 것은 제외).
_OPEN_ENDED_WORDS = re.compile(
    r"\b("
    r"what|which|when|where|why|who|whose|whom|how|describe|explain|tell me"
    r"|qué|cuál|cuándo|dónde|quién|cómo|cuánto|describa|explique"
    r"|quel|quelle|quand|où|pourquoi|comment|combien|décrivez|expliquez"
    r")\b",
    re.IGNORECASE,
)

# 한국어·일본어·중국어 — 띄어쓰기가 낱말 경계가 아니라 부분 문자열로 찾는다.
_OPEN_ENDED_SUBSTRINGS = (
    # 한국어 의문사
    "어느", "어떤", "어떠", "어떻", "무슨", "무엇", "언제", "어디", "왜 ", "누구", "누가",
    "몇", "며칠",
    # 한국어 서술형 요구
    "설명해", "말씀해", "말해 주", "얼마나", "묘사", "알려주세요", "알려 주세요", "적어주",
    # 일본어
    "どちら", "いつ", "どこ", "なぜ", "何", "いくつ", "どの", "どれ",
    "詳しく", "説明", "教えてください",
    # 중국어
    "哪", "什么", "为什么", "几", "如何", "多久", "详细", "描述",
    # 선택형 질문은 예/아니오로 어느 쪽인지 전달할 수 없어 자유 입력으로 받는다.
    "one eye or both", "one or both eyes", "한쪽인가요", "한쪽 눈인가요",
    "한쪽 눈 또는 양쪽", "한쪽 눈이나 양쪽", "한쪽 눈과 양쪽",
)

# 의문사가 '-든/-라도'와 붙으면 '아무거나'라는 뜻이라 예/아니오로 답할 수 있다.
# (예: "어느 쪽이든 불편하신가요?" / "어떤 증상이라도 있으신가요?")
_INCLUSIVE_FORM = re.compile(
    r"(어느|어떤|무슨|무엇|언제|어디|누구|몇)[^?!.]{0,8}?(이든지|이든|든지|든|이라도|라도)"
)

# '몇'과 '며칠'은 의문사("몇 시간 보시나요")로도, 막연한 수("최근 몇 년 사이", "며칠 전")로도
# 쓰인다. 아래 형태는 후자가 확실하므로 의문사로 세지 않는다.
_VAGUE_COUNT = re.compile(r"(최근|지난|근래)\s*(몇|며칠)|며칠\s*(전|째|사이|간)")


# 생성된 질문 길이 상한. app/schemas/ai.py의 ChatHistoryItem.q(max_length=500)와 맞춘다 —
# 맞춤 질문은 다음 회차 요청에 chat_history로 되돌아오므로 이 상한을 넘으면 422가 난다.
MAX_QUESTION_CHARS = 500


# 두 상황을 '또는'으로 묶은 질문 — "밤 운전이나 계단 오르기가 힘드신가요?"
# (2026-09-23 실사용 테스트). 운전을 안 하는 사람은 네/아니오 어느 쪽으로도 답할 수 없다.
# 프롬프트로 막아도 모델이 가끔 어기므로 한 번 다시 생성하게 한다.
# 한국어는 '-이나/-거나' 뒤에 띄어쓰기가 올 때만 센다('-나요?' 어미와 구분).
_COMPOUND_QUESTION = re.compile(
    r"\S(이나|거나)\s|또는|혹은"
    r"|\b(or|o|u|ou)\b"
    r"|または|あるいは|或者|还是",
    re.IGNORECASE,
)


def _is_compound_question(q: str) -> bool:
    return bool(_COMPOUND_QUESTION.search(q or ""))


def _is_yes_no_question(q: str) -> bool:
    """네/아니오로 답할 수 있는 질문인지 대략 판별한다(보수적: 애매하면 거부)."""
    if not q or not q.strip():
        return False
    low = q.strip().lower()
    low = _INCLUSIVE_FORM.sub("", low)      # '어느 쪽이든' 같은 허용형을 먼저 지운다
    low = _VAGUE_COUNT.sub("", low)
    if _OPEN_ENDED_WORDS.search(low):
        return False
    return not any(m in low for m in _OPEN_ENDED_SUBSTRINGS)

def _valid_question_output(q: str, lang: str, chat_history: list) -> bool:
    """Reject obvious format/language failures; this is not a semantic medical review."""
    if not q or len(q) > MAX_QUESTION_CHARS:
        return False
    # A diagnosis paragraph or a numbered list must never become a yes/no question.
    if not q.endswith(("?", "？")) or q.count("?") + q.count("？") != 1:
        return False
    if re.search(r"[\r\n。！!]|\.\s|^\s*(?:\d+[.)]|[-*#])", q):
        return False
    hangul = bool(re.search(r"[가-힣]", q))
    kana = bool(re.search(r"[ぁ-ゖァ-ヺ]", q))
    han = bool(re.search(r"[\u4e00-\u9fff]", q))
    if lang == "ko":
        language_ok = hangul and not kana
    elif lang == "ja":
        language_ok = kana and not hangul
    elif lang == "zh":
        language_ok = han and not hangul and not kana
    else:
        # Script checks cannot distinguish English, French and Spanish reliably.
        language_ok = bool(re.search(r"[A-Za-zÀ-ÿ]", q)) and not (hangul or kana or han)
    normalized = lambda text: re.sub(r"[\W_]", "", text.casefold())
    return language_ok and all(normalized(q) != normalized(item.q) for item in chat_history)
