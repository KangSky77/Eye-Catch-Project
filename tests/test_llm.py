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


def test_편측백내장_지시문은_asymmetric일때만():
    base = ("판독", "정상", [], "ko")
    with_asym = llm._build_opinion_prompt(*base, eye_asymmetric=True)
    without = llm._build_opinion_prompt(*base, eye_asymmetric=False)
    assert "편측" in with_asym
    assert "편측" not in without


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
