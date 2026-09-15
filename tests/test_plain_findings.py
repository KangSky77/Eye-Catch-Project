"""검사 요약 해석의 '쉬운 말' 변환 — 검증을 통과한 줄만 화면에 나가야 한다.

이 기능은 LLM에게 해석을 맡기지 않는다. 확정된 문장의 말투만 바꾸게 하고,
새 숫자·새 질환명·확률/배제/진단 표현이 끼어들면 그 줄은 원문으로 되돌린다.
"""
import pytest

from app.services import plain_language as pl

KO_AMSLER = ("암슬러 격자 자가검사에서 좌우 모두 뚜렷한 왜곡·암점 응답이 없었습니다. "
             "이 검사는 황반(중심시야)만 확인하므로, 다른 부위나 다른 질환은 평가하지 않습니다.")
KO_CATARACT = "백내장 AI가 수정체 혼탁으로 보이는 특징을 강하게 감지했습니다. 확진은 안과의 세극등 현미경 검사로만 가능합니다."


def test_말투만_바꾼_문장은_통과한다():
    assert pl.check_rewrite(KO_CATARACT, "백내장 AI가 사진에서 수정체가 뿌옇게 보이는 특징을 강하게 찾았습니다. 확진은 안과 세극등 검사로만 할 수 있습니다.") is None


@pytest.mark.parametrize("candidate,reason", [
    ("백내장 AI가 혼탁 특징을 강하게 감지했습니다. 확률은 87%입니다.", "new_number"),
    ("백내장 AI가 혼탁 특징을 감지했습니다. 녹내장일 수도 있습니다.", "new_disease"),
    ("사진에서 뿌연 특징을 찾았습니다.", "dropped_disease"),
])
def test_사실이_바뀌면_거부한다(candidate, reason):
    assert pl.check_rewrite(KO_CATARACT, candidate) == reason


def test_안심시키거나_배제하는_문장은_거부한다():
    # safety.check_sentence가 잡는 표현 — 사유 문자열은 safety 쪽 분류를 그대로 쓴다
    assert pl.check_rewrite(KO_AMSLER, "암슬러 검사가 정상이므로 황반변성 가능성은 낮습니다.") is not None


def test_설명을_덧붙이면_거부한다():
    long_text = KO_CATARACT + " 백내장은 나이가 들면 수정체가 단백질 변성으로 뿌예지는 질환이고, 수술로 인공수정체를 넣어 치료합니다. 수술은 보통 20분 정도 걸립니다."
    assert pl.check_rewrite(KO_CATARACT, long_text) in ("too_long", "new_number")


def test_빈_문장은_거부한다():
    assert pl.check_rewrite(KO_CATARACT, "   ") == "empty"


@pytest.mark.parametrize("raw,expected", [
    ("1. 첫째 줄\n2. 둘째 줄", ["첫째 줄", "둘째 줄"]),
    ("- 첫째 줄\n- 둘째 줄", ["첫째 줄", "둘째 줄"]),
    ("1. 첫째 줄", None),                      # 줄 수가 모자라면 통째로 원문
    ("1. 첫\n2. 둘\n3. 셋", None),              # 줄이 늘어나도 원문
])
def test_번호_목록_파싱(raw, expected):
    assert pl.parse_numbered(raw, 2) == expected


@pytest.mark.anyio
async def test_검증_통과분만_바뀌고_나머지는_원문이다(monkeypatch):
    async def fake(prompt):
        # 1번은 말투만 바꾼 정상 변환, 2번은 없던 숫자를 지어낸 변환
        return "1. 암슬러 격자 검사에서 양쪽 눈 모두 뚜렷한 휘어짐이나 빈 곳이 없었습니다. 이 검사는 황반만 봅니다.\n2. 백내장 AI가 혼탁 특징을 강하게 찾았습니다. 확률 87%입니다."
    monkeypatch.setattr("app.services.llm.generate_ollama", fake)
    out = await pl.rewrite_findings([KO_AMSLER, KO_CATARACT], "ko")
    assert out[0]["rewritten"] is True and "황반" in out[0]["text"]
    assert out[1] == {"text": KO_CATARACT, "rewritten": False}


@pytest.mark.anyio
async def test_LLM_실패는_전부_원문으로_돌아간다(monkeypatch):
    async def boom(prompt):
        raise RuntimeError("ollama down")
    monkeypatch.setattr("app.services.llm.generate_ollama", boom)
    out = await pl.rewrite_findings([KO_CATARACT], "ko")
    assert out == [{"text": KO_CATARACT, "rewritten": False}]


@pytest.mark.anyio
async def test_줄_수가_다르면_한_줄도_바꾸지_않는다(monkeypatch):
    async def fake(prompt):
        return "1. 두 문장을 하나로 합쳐버린 요약입니다."
    monkeypatch.setattr("app.services.llm.generate_ollama", fake)
    out = await pl.rewrite_findings([KO_AMSLER, KO_CATARACT], "ko")
    assert [o["rewritten"] for o in out] == [False, False]
