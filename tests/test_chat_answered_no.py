"""챗봇이 문진 '아니오' 항목을 조언하지 않게 하는 장치와, 사실 필터 안내 문구의 조건."""
import pytest

from app.services import llm

CTX = "[권장 조치] 수 주 내 안과 검진을 권합니다"


@pytest.mark.parametrize("lang", ["ko", "en"])
def test_아니오라고_답한_항목은_관리수칙_예시에서_빠진다(lang):
    prompt = llm._build_chat_prompt("눈 건강 관리 방법", CTX, lang,
                                    facts=["Diabetes: no", "Hypertension: no", "Smoking: no"])
    for word in (["혈당", "혈압 관리", "금연"] if lang == "ko" else ["blood sugar/pressure management", "smoking cessation"]):
        assert f"{word}" not in prompt.split("관리 수칙" if lang == "ko" else "general eye health care tips")[1].split("\n")[0]
    assert ("'아니오'라고 답했습니다" if lang == "ko" else "answered 'no'") in prompt


def test_답하지_않았거나_예인_항목은_예시에_남는다():
    prompt = llm._build_chat_prompt("눈 건강 관리 방법", CTX, "ko", facts=["Diabetes: yes"])
    assert "금연, 혈당·혈압 관리" in prompt
    assert "'아니오'라고 답했습니다" not in prompt
    only_bp = llm._build_chat_prompt("눈 건강 관리 방법", CTX, "ko", facts=["Hypertension: no"])
    assert "혈당 관리" in only_bp and "혈당·혈압" not in only_bp.split("관리 수칙")[1].split("\n")[0]


def _fake(chunks, reasons):
    async def fake(prompt, facts=None, filtered_reasons=None, **kwargs):
        if filtered_reasons is not None:
            filtered_reasons.update(reasons)
        for c in chunks:
            yield c
    return fake


@pytest.mark.anyio
async def test_일부만_지워졌으면_안내_문구를_붙이지_않는다(monkeypatch):
    """7번 중 7번 붙던 문구 — 남은 답은 멀쩡하니 사용자가 뭔가 잘못한 것처럼 보이게 하지 않는다."""
    monkeypatch.setattr(llm, "sanitized_stream", _fake(["자외선 차단 선글라스를 쓰세요."], {"contradicts_facts"}))
    out = "".join([c async for c in llm.chat_with_gemma_stream("관리", CTX, "ko", facts=["Hypertension: no"])])
    assert out == "자외선 차단 선글라스를 쓰세요."


@pytest.mark.anyio
async def test_전부_지워졌으면_빈_화면_대신_안내_문구를_보여준다(monkeypatch):
    monkeypatch.setattr(llm, "sanitized_stream", _fake([llm.ERROR_MARKER + "AI_FILTER_EMPTY"], {"contradicts_facts"}))
    out = "".join([c async for c in llm.chat_with_gemma_stream("관리", CTX, "ko", facts=["Hypertension: no"])])
    assert out == llm.FACT_FILTER_NOTICE["ko"]
    assert "다시 확인" not in out


def test_안내_문구는_6개_언어이고_사용자_탓으로_읽히지_않는다():
    assert set(llm.FACT_FILTER_NOTICE) == {"ko", "en", "es", "fr", "ja", "zh"}
    assert "check the answers" not in llm.FACT_FILTER_NOTICE["en"]
