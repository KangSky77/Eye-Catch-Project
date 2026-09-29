"""결과 설명 빠짐 검사(explain_check) — AI 설명이 비정상 소견·권장 시기를 빠뜨리면 고정 문장으로 바꾼다."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.services import explain_check, llm
from app.services.explain_check import missing_items

ROOT = Path(__file__).parents[1]
LANGS = ["ko", "en", "es", "fr", "ja", "zh"]
KEYS = ["find_cat_risk", "find_cat_borderline", "find_ams_abnormal", "tri_now", "tri_weeks",
        "eye_left", "eye_right", "ams_result_left", "ams_result_right"]


@pytest.fixture(scope="module")
def translations():
    if not shutil.which("node"):
        pytest.skip("node가 없어 번역 문자열을 읽을 수 없다")
    script = (
        "const fs=require('fs'),vm=require('vm');const c={window:{},document:{}};vm.createContext(c);"
        "for(const f of ['data.js','app-report-text.js'])vm.runInContext(fs.readFileSync('static/'+f,'utf8'),c);"
        f"const k={json.dumps(KEYS)};"
        "process.stdout.write(JSON.stringify(Object.fromEntries(Object.entries(vm.runInContext('translations',c))"
        ".map(([l,t])=>[l,Object.fromEntries(k.map(x=>[x,t[x]]))]))))"
    )
    out = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(out.stdout)


@pytest.mark.anyio
@pytest.mark.parametrize("lang", LANGS)
async def test_fixed_fallback_passes_its_own_check_in_every_language(lang, translations):
    """대체 문장이 검사를 통과하지 못하면 어휘 목록에 그 언어의 표현이 빠진 것이다."""
    t = translations[lang]
    for photo, cat_code, tri in [("find_cat_risk", "cat_risk", "tri_now"), ("find_cat_borderline", "cat_borderline", "tri_weeks")]:
        for eye_key, ams_code in [("eye_left", "ams_left"), ("eye_right", "ams_right")]:
            lines = [t[photo], t["find_ams_abnormal"].replace("{eye}", t[eye_key]), t[tri]]
            text = await explain_check.fallback_text(lines, lang)
            assert missing_items(text, [cat_code, ams_code, tri], lang) == [], (lang, text)


@pytest.mark.parametrize("text,lang", [
    # 실측(2026-09-29 e2b)에서 격자 이상을 빠뜨린 답
    ("AI가 수정체 혼탁으로 보이는 특징을 감지했으며 문진에서 뿌옇게 보이는 증상이 확인되었습니다. "
     "이 결과는 안과의 세극등 현미경 검사로만 확진이 가능합니다. 따라서 빠른 시일 내에 안과 진료를 받는 것이 권장됩니다.", "ko"),
])
def test_missing_amsler_is_caught(text, lang):
    assert missing_items(text, ["cat_risk", "ams_left", "tri_now"], lang) == ["ams_left"]


def test_missing_timing_is_caught():
    """'안과 검사가 필요합니다'만 있고 '빠른 시일 내'가 빠진 답 — 실측 3번."""
    text = ("AI가 수정체 혼탁의 특징을 강하게 감지했으며 왼쪽 눈 암슬러 격자에서 이상 응답이 확인되었습니다. "
            "확진을 위해서는 안과 세극등 현미경 검사나 안저 검사가 필요합니다.")
    assert missing_items(text, ["cat_risk", "ams_left", "tri_now"], "ko") == ["tri_now"]


def test_wrong_eye_is_caught():
    text = "오른쪽 눈의 암슬러 격자에서 이상 응답이 있었습니다. 백내장 특징도 감지됐습니다. 빠른 시일 내 안과 진료를 권합니다."
    assert missing_items(text, ["cat_risk", "ams_left", "tri_now"], "ko") == ["ams_left"]


@pytest.mark.parametrize("text,lang", [
    ("암슬러 격자에서 왼쪽 눈은 정상으로 나왔습니다.", "ko"),
    ("The Amsler grid was normal in the left eye.", "en"),
    ("左目のアムスラー格子は正常でした。", "ja"),
])
def test_abnormal_amsler_result_cannot_be_reversed_to_normal(text, lang):
    assert missing_items(text, ["ams_left"], lang) == ["ams_left:reversed"]


@pytest.mark.parametrize("text,lang", [
    ("백내장 AI가 수정체 혼탁 특징을 감지하지 않았습니다. 빠른 시일 내 안과 진료를 권합니다.", "ko"),
    ("사진상 수정체는 정상입니다. 빠른 시일 내 안과 진료를 권합니다.", "ko"),
    ("The photo shows a normal lens. See an ophthalmologist soon.", "en"),
])
def test_reversed_cataract_finding_is_caught(text, lang):
    assert missing_items(text, ["cat_risk", "tri_now"], lang) == ["cat_risk:reversed"]


@pytest.mark.parametrize("text,lang", [
    # 'abnormal' 안의 'normal'을 뒤집힘으로 읽던 오탐(영어 실측 5번 중 2번)
    ("The AI detected features consistent with lens clouding, and the Amsler grid showed an abnormal response "
     "in the left eye. You are recommended to see an ophthalmologist soon.", "en"),
    ("수정체 혼탁 특징과 왼쪽 눈 암슬러 격자의 비정상 응답이 있었습니다. 빠른 시일 내 안과 진료를 권합니다.", "ko"),
])
def test_abnormal_is_not_read_as_normal(text, lang):
    assert missing_items(text, ["cat_risk", "ams_left", "tri_now"], lang) == []


async def _fake_stream(text):
    async def fake(prompt, facts=None, **kwargs):
        yield llm.KEEPALIVE
        yield text
    return fake


@pytest.mark.anyio
async def test_incomplete_explanation_is_replaced_by_fixed_wording(monkeypatch):
    monkeypatch.setattr(llm, "sanitized_stream", await _fake_stream("백내장 특징이 감지됐습니다. 안과 검사가 필요합니다."))
    lines = ["백내장 AI가 수정체 혼탁으로 보이는 특징을 강하게 감지했습니다. 확진은 안과의 세극등 현미경 검사로만 가능합니다.",
             "빠른 시일 내 안과 진료를 권합니다"]
    out = [c async for c in llm.chat_with_gemma_stream("x", "ctx", "ko", explain_results=True,
                                                       explain_required=["cat_risk", "tri_now"], explain_fallback=lines)]
    body = "".join(out)
    assert "강하게" in body and body.endswith("빠른 시일 내 안과 진료를 권합니다.")


@pytest.mark.anyio
async def test_even_plausible_model_explanation_is_not_used(monkeypatch):
    answer = "백내장 특징이 강하게 감지됐습니다. 빠른 시일 내 안과 진료를 받으세요."
    monkeypatch.setattr(llm, "sanitized_stream", await _fake_stream(answer))
    out = [c async for c in llm.chat_with_gemma_stream("x", "ctx", "ko", explain_results=True,
                                                       explain_required=["cat_risk", "tri_now"], explain_fallback=["고정"])]
    assert out == ['고정.']


@pytest.mark.anyio
async def test_ai_failure_still_shows_fixed_wording(monkeypatch):
    async def failing(prompt, facts=None, **kwargs):
        yield llm.ERROR_MARKER + "AI_FILTER_EMPTY"
    monkeypatch.setattr(llm, "sanitized_stream", failing)
    out = [c async for c in llm.chat_with_gemma_stream("x", "ctx", "ko", explain_results=True,
                                                       explain_required=["tri_now"], explain_fallback=["빠른 시일 내 안과 진료를 권합니다"])]
    assert out == ["빠른 시일 내 안과 진료를 권합니다."]
