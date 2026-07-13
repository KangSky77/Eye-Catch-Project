"""RAG 참고지식 검색 — 결과 코드/키워드에 맞는 지식이 골라지는지."""
from app.services import knowledge


def test_위험판정은_백내장_지식():
    got = knowledge.retrieve_for_opinion(cataract_code="risk")
    assert any("백내장" in s["title"] for s in got)


def test_경계판정도_백내장_지식():
    # 경계(borderline)에도 지식을 줘야 소견서가 '왜 재검이 필요한지' 설명 가능
    got = knowledge.retrieve_for_opinion(cataract_code="borderline")
    assert any("백내장" in s["title"] for s in got)


def test_이상없으면_일반관리_지식():
    got = knowledge.retrieve_for_opinion()
    assert len(got) == 1
    assert "일반" in got[0]["title"]


def test_암슬러이상은_황반_지식():
    got = knowledge.retrieve_for_opinion(amsler_abnormal=True)
    assert any("황반" in s["title"] for s in got)


def test_증상코드_중복없이_병합():
    got = knowledge.retrieve_for_opinion(
        cataract_code="risk", symptom_codes=["glaucoma", "cataract", "없는코드"]
    )
    titles = [s["title"] for s in got]
    assert len(titles) == len(set(titles))          # 중복 없음
    assert any("녹내장" in t for t in titles)


def test_챗봇_키워드검색_한영():
    got_ko = knowledge.retrieve_for_chat("밤에 빛 번짐이 심하고 눈부심이 있어요")
    assert any("백내장" in s["title"] for s in got_ko)
    got_en = knowledge.retrieve_for_chat("my vision is blurry with glare")
    assert any("Cataract" in s["title"] for s in got_en)


def test_챗봇_무관한질문은_일반지식_폴백():
    got = knowledge.retrieve_for_chat("오늘 점심 뭐 먹지")
    assert len(got) == 1
    assert "일반" in got[0]["title"]


def test_참고블록_포맷():
    ref = knowledge.format_reference(knowledge.retrieve_for_opinion(cataract_code="risk"))
    assert ref.startswith("[참고 의학 정보")
    assert "백내장" in ref
    assert knowledge.format_reference([]) == ""
