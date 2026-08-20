"""LLM 출력 안전 필터 회귀 테스트.

핵심 케이스는 외부 리뷰에서 **실제로 재현된** Gemma 답변이다:
    "암슬러 격자가 정상이므로 녹내장과 관련된 심각한 황반부 문제 가능성이 낮다"
이 문장이 다시 통과하면 안 된다.
"""
import pytest

from app.services import safety

# 리뷰에서 실제 재현된 사고 문장 + 같은 유형의 변형
REAL_INCIDENT = "암슬러 격자가 정상이므로 녹내장과 관련된 심각한 황반부 문제 가능성이 낮습니다."

UNSAFE = [
    # (문장, 기대 사유)
    (REAL_INCIDENT, None),                                            # 사유는 아래에서 별도 확인
    ("백내장 확률이 87%로 매우 높습니다.", "probability"),
    ("모델이 계산한 확률이 높게 나왔습니다.", "probability"),
    ("검사 결과 녹내장 가능성이 낮으니 안심하셔도 됩니다.", "exclusion"),
    ("암슬러가 정상이므로 황반변성은 배제할 수 있습니다.", "exclusion"),
    ("걱정하지 않으셔도 됩니다.", "exclusion"),
    ("백내장으로 진단됩니다.", "diagnosis"),
    ("Your cataract probability is 87%.", "probability"),
    ("Glaucoma is unlikely based on this result.", "exclusion"),
    ("There is no need to worry about macular degeneration.", "exclusion"),
    ("You have cataracts.", "diagnosis"),
    ("The Amsler result rules out glaucoma.", "exclusion"),
    ("緑内障の可能性は低いです。", "exclusion"),
    ("青光眼的可能性很低。", "exclusion"),
]

SAFE = [
    "환자분, 안과 방문 전에 몇 가지 준비하시면 좋겠습니다.",
    "안과에서는 세극등 현미경 검사와 안압 측정을 받게 되실 수 있습니다.",
    "외출 시 자외선 차단 선글라스를 착용하시면 도움이 됩니다.",
    "금연과 혈당 관리는 눈 건강 유지에 중요합니다.",
    "At the clinic you may receive a slit-lamp exam and an OCT scan.",
    "Wearing UV-blocking sunglasses outdoors can help protect your eyes.",
    "정기적인 안과 검진을 받으시는 것을 권해 드립니다.",
]


def test_리뷰에서_재현된_실제_오류문장이_차단됨():
    why = safety.check_sentence(REAL_INCIDENT)
    assert why is not None, "리뷰가 재현한 의료 오류 문장이 필터를 통과했습니다"
    # 이 문장은 '배제 표현'과 '질환 교차' 둘 다에 해당한다
    assert why in ("exclusion", "cross_disease")


@pytest.mark.parametrize("sentence,expected", [(s, e) for s, e in UNSAFE if e])
def test_위험문장이_사유와_함께_차단됨(sentence, expected):
    assert safety.check_sentence(sentence) == expected


@pytest.mark.parametrize("sentence", SAFE)
def test_안전한_생활조언은_통과(sentence):
    assert safety.check_sentence(sentence) is None, f"정상 문장이 차단됨: {sentence}"


def test_질환_교차_언급_차단():
    # 한 문장에 질환 둘 → 관계를 지어냈을 가능성
    assert safety.check_sentence("백내장과 녹내장을 함께 확인해야 합니다.") == "cross_disease"
    # 하나만 언급하는 것은 정상
    assert safety.check_sentence("백내장은 수정체가 혼탁해지는 질환입니다.") is None


def test_sanitize가_위험문장만_제거하고_나머지는_보존():
    text = ("환자분, 안녕하세요. "
            "백내장 확률이 87%로 높습니다. "
            "안과에서 세극등 검사를 받아보세요. "
            "녹내장 가능성은 낮으니 안심하셔도 됩니다. "
            "금연을 권해 드립니다.")
    clean, reasons = safety.sanitize(text)
    assert "87%" not in clean
    assert "안심하셔도" not in clean
    assert "세극등" in clean            # 쓸 만한 조언은 살아남아야 한다
    assert "금연" in clean
    assert set(reasons) == {"probability", "exclusion"}


def test_전부_위험하면_빈_문자열():
    # 틀린 의학 문장을 보여주느니 아무것도 안 보여주는 쪽이 안전하다
    clean, reasons = safety.sanitize("백내장 확률이 90%입니다. 녹내장은 배제할 수 있습니다.")
    assert clean == ""
    assert len(reasons) == 2


def test_빈_입력_안전():
    assert safety.sanitize("") == ("", [])
    assert safety.sanitize(None) == ("", [])


@pytest.mark.anyio
async def test_스트림_필터가_위험문장을_내보내지_않음(monkeypatch):
    """실제 스트리밍 경로에서도 걸러지는지 — 토큰이 쪼개져 도착해도 문장 단위로 판정."""
    from app.services import llm

    async def fake(prompt):
        # 토큰 경계를 일부러 문장 중간에 두어 버퍼링이 동작하는지 확인
        for tok in ["환자분, 안녕하세요. ", "백내장 ", "확률이 ", "87%입니다. ",
                    "세극등 검사를 ", "받아보세요."]:
            yield tok

    monkeypatch.setattr(llm, "stream_with_keepalive", fake)
    out = "".join([c async for c in llm.sanitized_stream("p")])
    assert "87%" not in out
    assert "안녕하세요" in out
    assert "세극등" in out


@pytest.mark.anyio
async def test_스트림_필터가_오류마커와_하트비트는_통과시킴(monkeypatch):
    from app.services import llm

    async def fake(prompt):
        yield llm.KEEPALIVE
        yield llm.ERROR_MARKER + "AI_SERVER_ERROR"

    monkeypatch.setattr(llm, "stream_with_keepalive", fake)
    out = [c async for c in llm.sanitized_stream("p")]
    assert out[0] == llm.KEEPALIVE
    assert out[1].startswith(llm.ERROR_MARKER)


def test_소견서_프롬프트가_해석을_금지함():
    from app.services import llm
    ko = llm._build_opinion_prompt("경계 단계", "정상", ["빛 번짐"], "ko")
    assert "해석하거나" in ko and "금지" in ko
    assert "확률" in ko                      # '확률이라는 단어를 쓰지 말라'는 지시로 등장
    en = llm._build_opinion_prompt("borderline", "normal", [], "en")
    assert "Do NOT interpret" in en
    assert "cannot rule out" in en
