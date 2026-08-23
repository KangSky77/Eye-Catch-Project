"""LLM 서비스 — 프롬프트 생성(순수 함수)과 스트림 오류 처리/폴백. Ollama는 모킹."""
import pytest

from app.services import llm
from app.schemas.ai import ChatHistoryItem


def test_소견서_프롬프트_한국어():
    p = llm._build_opinion_prompt("백내장 위험 87%", "정상", ["눈부심"], "ko")
    assert "한국어" in p
    assert "백내장 위험 87%" in p
    assert "눈부심" in p


def test_소견서_프롬프트_영어_및_비지원언어_폴백():
    p_en = llm._build_opinion_prompt("risk 87%", "normal", [], "en")
    assert "ONLY in English" in p_en
    # 지원 목록에 없는 언어 코드는 영어로 폴백
    p_unknown = llm._build_opinion_prompt("risk 87%", "normal", [], "de")
    assert "ONLY in English" in p_unknown


def test_LLM에게는_편측_해석을_시키지_않는다():
    """설계 변경(2026-08-20): 의학적 해석은 전부 코드가 결정론적으로 생성한다.

    LLM에게 해석을 맡겼더니 "암슬러가 정상이므로 녹내장 가능성이 낮다"는 문장이
    실제로 나왔기 때문에, 편측 여부도 프롬프트에 넣지 않는다."""
    base = ("판독", "정상", [], "ko")
    with_asym = llm._build_opinion_prompt(*base, eye_asymmetric=True)
    without = llm._build_opinion_prompt(*base, eye_asymmetric=False)
    assert with_asym == without, "편측 여부가 프롬프트를 바꾸면 안 됩니다(해석은 코드 담당)"
    assert "해석하거나" in with_asym and "금지" in with_asym


def test_참고지식_블록_주입():
    p = llm._build_opinion_prompt("판독", "정상", [], "ko", reference="[참고 의학 정보] 백내장은 ...")
    assert "[참고 의학 정보]" in p


@pytest.mark.anyio
async def test_스트림_정상토큰_통과(monkeypatch):
    async def fake_ollama(prompt):
        yield "안녕"
        yield "하세요"
    monkeypatch.setattr(llm, "stream_ollama", fake_ollama)
    out = [tok async for tok in llm.stream_with_keepalive("p")]
    assert out == ["안녕", "하세요"]


@pytest.mark.anyio
async def test_스트림_오류는_마커로_구분(monkeypatch):
    # 오류가 '정상 소견 텍스트'처럼 보이면 프론트가 DB에 저장해버림 — 마커로 구분해야 함
    async def broken(prompt):
        raise ConnectionError("ollama down at localhost:11434")
        yield  # pragma: no cover — async generator로 만들기 위한 형식
    monkeypatch.setattr(llm, "stream_ollama", broken)
    out = [tok async for tok in llm.stream_with_keepalive("p")]
    assert out == [llm.ERROR_MARKER + "AI_SERVER_ERROR"]
    # 내부 주소 등 예외 상세가 클라이언트로 새지 않아야 함
    assert "11434" not in "".join(out)


@pytest.mark.anyio
async def test_동적문진_실패시_빈문자열_폴백(monkeypatch):
    # 빈 문자열이면 프론트가 선택 언어의 기본 질문으로 대체 — 한국어 고정 반환하면 안 됨
    async def broken(prompt):
        raise ConnectionError("down")
    monkeypatch.setattr(llm, "generate_ollama", broken)
    q = await llm.generate_next_question("en", "normal", "normal", [])
    assert q == ""


@pytest.mark.anyio
async def test_동적문진_문진내역이_프롬프트에_포함(monkeypatch):
    captured = {}
    async def capture(prompt):
        captured["prompt"] = prompt
        return "다음 질문?"
    monkeypatch.setattr(llm, "generate_ollama", capture)
    history = [ChatHistoryItem(q="눈부심이 있나요?", a="네, 밤에 심해요")]
    q = await llm.generate_next_question("ko", "위험 87%", "정상", history)
    assert q == "다음 질문?"
    assert "눈부심이 있나요?" in captured["prompt"]
    assert "네, 밤에 심해요" in captured["prompt"]


# ------------------------------------------------------------------
# 동적 문진 질문은 '네/아니오' 버튼 두 개로만 답할 수 있다.
# 서술형이 나오면 사용자가 답할 방법이 없어 문진이 그 자리에서 멈춘다.
# ------------------------------------------------------------------
def test_서술형_질문은_걸러진다():
    from app.services.llm import _is_yes_no_question
    개방형 = [
        "시력 변화에 대해 자세히 설명해 주시겠어요?",
        "눈이 얼마나 불편하신지 말씀해 주세요.",
        "증상이 어떻게 나타나나요?",
        "Could you describe your vision changes?",
        "How often does this happen?",
        "どのくらい見えにくいですか？",
        "请详细说明您的症状。",
        "",
    ]
    for q in 개방형:
        assert not _is_yes_no_question(q), f"서술형인데 통과됨: {q!r}"


def test_예아니오_질문은_통과된다():
    from app.services.llm import _is_yes_no_question
    폐쇄형 = [
        "밝은 곳에서 눈이 부시는 느낌이 있나요?",
        "야간 운전이 예전보다 힘드신가요?",
        "Do bright lights feel glaring to you?",
        "夜間の運転は以前より大変ですか？",
    ]
    for q in 폐쇄형:
        assert _is_yes_no_question(q), f"예/아니오 질문인데 거부됨: {q!r}"


def test_질문_프롬프트에_예아니오_제약이_들어있다():
    from app.services.llm import _build_next_question_prompt
    ko = _build_next_question_prompt("ko", "정상", "정상", "-")
    assert "'네'" in ko and "'아니오'" in ko
    assert "서술형" in ko
    en = _build_next_question_prompt("en", "normal", "normal", "-")
    assert "Yes" in en and "No" in en
    assert "Open-ended questions are forbidden" in en
