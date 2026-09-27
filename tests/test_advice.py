"""AI 소견 '고르기' 방식(app/services/advice.py) 회귀 테스트.

2026-09-27: 자유 작문 방식은 e2b·e4b 모두 20번 중 3번꼴로 문진 사실을 잘못 옮겼다.
고르기 방식에서는 AI가 검수된 선택지 id만 고르고 문장은 서버가 조립한다.
"""
import itertools

import pytest

from app.core.config import settings
from app.services import advice, llm, safety

LANGS = advice.LANGS


def _all_items():
    for cat in (advice.EXAMS, advice.CARE, advice.CLOSING, advice.POST_ACTION, advice.POST_CARE, advice.POST_CLOSING):
        yield from cat.items()


def test_모든_조언_문장이_6개_언어로_있다():
    for key, item in _all_items():
        for part in ("line", "why", "name"):
            if part in item:
                assert set(item[part]) == set(LANGS), f"{key}.{part}"
                assert all(v.strip() for v in item[part].values()), f"{key}.{part}"
    assert set(advice.EXAM_LINE) == set(LANGS)


def _facts(**kw):
    base = dict(symptoms=[], flag_codes=[], symptom_codes=[], cataract_code="normal", amsler_abnormal=False, triage_level="monitor")
    base.update(kw)
    return advice.facts_from(**base)


def test_당뇨가_있으면_혈당_조언만_생활관리_선택지로_남는다():
    f = _facts(flag_codes=["risk_diabetes", "sym_dr_fundus", "sym_chk_recent", "age_60s"], symptom_codes=["retinopathy"], triage_level="weeks")
    opts = advice.options_for(f)
    assert "glucose" in opts["care"]
    assert "eye_rest" not in opts["care"], "특정 조언이 있으면 일반론은 빠진다"
    assert "diabetic_yearly" in opts["closing"] and "exam_overdue" in opts["closing"]
    assert "oct" in opts["exams"]


def test_아니오라고_답한_위험요인의_조언은_선택지에_없다():
    # flag_codes가 모순돼도(예전 캐시 등) 'Diabetes: no'가 이긴다
    f = _facts(symptoms=["Hypertension: no", "Diabetes: no"], flag_codes=["risk_diabetes", "sym_cat_glare"])
    opts = advice.options_for(f)
    assert "glucose" not in opts["care"] and "blood_pressure" not in opts["care"]
    assert "diabetic_yearly" not in opts["closing"]
    assert "night_driving" in opts["care"]


def test_빠른진료_권장이면_마무리도_진료를_앞세운다():
    f = _facts(cataract_code="risk", triage_level="now")
    assert advice.options_for(f)["closing"] == ["visit_soon", "warning_signs"]


def test_수술직후는_권장조치를_AI가_아니라_앱이_정한다():
    f = _facts(symptoms=["Eye surgery: recent / 최근 4주 이내"], cataract_code="postop", triage_level="confirm")
    opts = advice.options_for(f)
    assert "exams" not in opts
    text = advice.compose({"care": "prepare_questions", "closing": "post_limit"}, f, "ko")
    assert text.split("<<<SUMMARY>>>")[1].strip().splitlines()[0] == advice.POST_ACTION["confirm"]["line"]["ko"]


def test_선택지_밖의_값이나_중복은_받지_않는다():
    f = _facts(flag_codes=["risk_diabetes"])
    opts = advice.options_for(f)
    assert advice.validate_choice({"exams": ["oct", "oct"], "care": "glucose", "closing": opts["closing"][0]}, f, opts) is None
    assert advice.validate_choice({"exams": ["oct", "iop"], "care": "quit_smoking", "closing": opts["closing"][0]}, f, opts) is None
    assert advice.validate_choice("not json", f, opts) is None
    ok = advice.validate_choice({"exams": ["oct", "iop", "oct"], "care": "glucose", "closing": opts["closing"][0]}, f, opts)
    assert ok == {"exams": ["oct", "iop"], "care": "glucose", "closing": opts["closing"][0]}


PERSONAS = [
    dict(flag_codes=["risk_diabetes", "sym_dr_fundus", "sym_chk_recent", "age_60s"], symptoms=["Hypertension: no", "Diabetes: yes"], symptom_codes=["retinopathy"], triage_level="weeks"),
    dict(flag_codes=["sym_cat_glare", "sym_cat_foggy", "sym_chk_recent", "age_50s"], symptoms=["Hypertension: no", "Diabetes: no"], symptom_codes=["cataract"], triage_level="weeks"),
    dict(flag_codes=["risk_smoking", "risk_hypertension", "sym_gla_iop", "age_40s"], symptom_codes=["glaucoma"], triage_level="monitor"),
    dict(flag_codes=["age_20s"], triage_level="monitor"),
    dict(amsler_abnormal=True, cataract_code="risk", triage_level="now", flag_codes=["age_70s"]),
    dict(symptoms=["Eye surgery: recent / 최근 4주 이내"], cataract_code="postop", triage_level="now"),
    dict(symptoms=["Eye surgery: recent / 최근 4주 이내"], cataract_code="postop", triage_level="monitor"),
]


@pytest.mark.parametrize("persona", PERSONAS)
def test_어떤_선택이든_3줄이고_안전필터를_통과한다(persona):
    """선택 가능한 모든 조합 × 6개 언어 — 조립된 문장이 필터에 걸리면 문장 자체를 고쳐야 한다."""
    f = _facts(**persona)
    opts = advice.options_for(f)
    exam_pairs = [None] if f.postop else list(itertools.permutations(opts["exams"], 2))
    for pair, care, closing in itertools.product(exam_pairs, opts["care"], opts["closing"]):
        choice = {"care": care, "closing": closing, **({} if pair is None else {"exams": list(pair)})}
        for lang in LANGS:
            text = advice.compose(choice, f, lang)
            detail, summary = text.split("<<<SUMMARY>>>")
            lines = summary.strip().splitlines()
            assert len(lines) == 3
            for sentence in safety.SENT_SPLIT.split(text.replace("<<<SUMMARY>>>", "\n")):
                if sentence.strip():
                    assert safety.check_sentence(sentence.strip(), persona.get("symptoms", [])) is None, (lang, sentence)


def test_모르는_언어는_영어로_조립한다():
    f = _facts(flag_codes=["age_30s"])
    opts = advice.options_for(f)
    assert "At the eye clinic" in advice.compose(advice.fallback_choice(f, opts), f, "de")


def test_샘플링_온도를_명시한다():
    assert llm._ollama_payload("p", stream=False)["options"]["temperature"] == settings.ollama_temperature
    assert settings.ollama_temperature <= 0.3
    assert "format" in llm._ollama_payload("p", stream=False, fmt={"type": "object"})


async def _collect(**kw):
    return "".join([c async for c in llm.get_gemma_opinion_stream(
        "-", "-", ["Diabetes: yes"], "ko", symptom_codes=["retinopathy"], triage_level="weeks",
        flag_codes=["risk_diabetes", "age_60s"], **kw) if c != llm.KEEPALIVE])


@pytest.mark.anyio
async def test_형식이_틀리면_한번_더_묻고_그래도_틀리면_규칙으로_고른다(monkeypatch):
    monkeypatch.setattr(llm.settings, "opinion_mode", "choice")
    calls = []
    async def bad_then_good(prompt, schema):
        calls.append(schema)
        return None if len(calls) == 1 else {"exams": ["dilated_fundus", "oct"], "care": "glucose", "closing": "diabetic_yearly"}
    monkeypatch.setattr(llm, "generate_json", bad_then_good)
    out = await _collect()
    assert len(calls) == 2
    assert advice.CARE["glucose"]["line"]["ko"] in out
    assert out.count("<<<SUMMARY>>>") == 1

    async def always_bad(prompt, schema):
        return {"care": "made_up"}
    monkeypatch.setattr(llm, "generate_json", always_bad)
    out = await _collect()
    assert "<<<SUMMARY>>>" in out and llm.ERROR_MARKER not in out


@pytest.mark.anyio
async def test_AI서버에_연결할_수_없으면_규칙_선택을_AI소견으로_내보내지_않는다(monkeypatch):
    monkeypatch.setattr(llm.settings, "opinion_mode", "choice")
    async def down(prompt, schema):
        raise ConnectionError("ollama down")
    monkeypatch.setattr(llm, "generate_json", down)
    out = await _collect()
    assert out.startswith(llm.ERROR_MARKER)
