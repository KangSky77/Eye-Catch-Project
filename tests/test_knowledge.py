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


# ---------------------------------------------------------------------------
# 참고지식을 data/medical_knowledge.json으로 분리한 뒤의 로더 검증.
# 의학 문장을 손으로 고치다 파일을 깨뜨리면 서버 기동 시점에 바로 알아야 한다
# (조용히 빈 지식으로 굴러가면 LLM 환각 위험이 그대로 커진다).
# ---------------------------------------------------------------------------
import json

import pytest


def test_JSON파일에서_로드되고_필수항목이_있다():
    assert knowledge.KB_PATH.exists(), "data/medical_knowledge.json이 저장소에 있어야 함"
    for key in knowledge.REQUIRED_KEYS:
        assert key in knowledge.KB, f"필수 참고지식 누락: {key}"


def test_프론트가_보내는_질환코드와_짝이_맞는다():
    """static/data.js의 `disease:` 값이 전부 KB에 있어야 소견서에 지식이 주입된다."""
    import re

    data_js = (knowledge.KB_PATH.parents[1] / "static" / "data.js").read_text(encoding="utf-8")
    codes = set(re.findall(r"disease:\s*'([a-z]+)'", data_js))
    assert codes, "data.js에서 disease 코드를 찾지 못함 — 정규식이 낡았는지 확인"
    assert codes <= set(knowledge.KB), f"KB에 없는 질환 코드: {codes - set(knowledge.KB)}"


def _write(tmp_path, payload):
    p = tmp_path / "kb.json"
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return p


def test_파일이_없으면_기동실패(tmp_path):
    with pytest.raises(RuntimeError, match="없습니다"):
        knowledge._load_kb(tmp_path / "there_is_no_such_file.json")


def test_문법오류는_기동실패(tmp_path):
    p = tmp_path / "kb.json"
    p.write_text("{ 이건 JSON이 아님 ", encoding="utf-8")
    with pytest.raises(RuntimeError, match="문법 오류"):
        knowledge._load_kb(p)


def test_필수항목_누락은_기동실패(tmp_path):
    partial = {k: knowledge.KB[k] for k in ("cataract", "general")}
    with pytest.raises(RuntimeError, match="필수 항목"):
        knowledge._load_kb(_write(tmp_path, partial))


def test_빈_문장은_기동실패(tmp_path):
    broken = json.loads(json.dumps(knowledge.KB))
    broken["glaucoma"]["text"] = "   "
    with pytest.raises(RuntimeError, match="비어 있습니다"):
        knowledge._load_kb(_write(tmp_path, broken))


def test_keywords_타입오류는_기동실패(tmp_path):
    broken = json.loads(json.dumps(knowledge.KB))
    broken["macular"]["keywords"] = "황반"      # 리스트여야 하는데 문자열
    with pytest.raises(RuntimeError, match="문자열 목록"):
        knowledge._load_kb(_write(tmp_path, broken))
