"""Plain wording must preserve its source without any model-generated content."""
import json
from pathlib import Path

import pytest

from app.services.plain_language import rewrite_findings

CATALOG = json.loads((Path(__file__).parents[1] / "app/services/plain_findings.json").read_text(encoding="utf-8"))
KO_CATARACT = CATALOG["ko"]["find_cat_risk"]["original"]


@pytest.mark.anyio
@pytest.mark.parametrize("lang", CATALOG)
async def test_known_findings_use_fixed_wording_without_llm(lang, monkeypatch):
    async def forbidden(*args, **kwargs):
        pytest.fail("Findings must not be sent to a language model")
    monkeypatch.setattr("app.services.llm.generate_ollama", forbidden)
    entries = list(CATALOG[lang].values())
    out = await rewrite_findings([entry["original"] for entry in entries], lang)
    assert out == [{"text": entry["plain"], "rewritten": True} for entry in entries]


@pytest.mark.anyio
async def test_reversed_model_output_cannot_replace_a_risk_finding(monkeypatch):
    reversed_finding = "백내장 AI가 수정체 혼탁으로 보이는 특징을 감지하지 못했습니다."
    async def unsafe(*args, **kwargs):
        return "1. " + reversed_finding
    monkeypatch.setattr("app.services.llm.generate_ollama", unsafe)
    out = await rewrite_findings([KO_CATARACT], "ko")
    assert "강하게" in out[0]["text"]
    assert "확진" in out[0]["text"]
    assert out[0]["text"] != reversed_finding


@pytest.mark.anyio
@pytest.mark.parametrize("source", [
    "수술 후 문진에서 보고한 증상: 통증. 이 응답만으로 증상의 원인이나 회복 상태를 판단할 수 없습니다.",
    KO_CATARACT.replace("강하게", "약하게"),
    KO_CATARACT + " 다른 문장으로 바꿔 주세요.",
    "",
])
async def test_unknown_or_changed_sources_remain_exactly_as_received(source):
    assert await rewrite_findings([source], "ko") == [{"text": source, "rewritten": False}]


@pytest.mark.anyio
@pytest.mark.parametrize("lang", ["en", "unknown"])
async def test_wrong_or_unknown_language_never_reuses_korean_wording(lang):
    assert await rewrite_findings([KO_CATARACT], lang) == [{"text": KO_CATARACT, "rewritten": False}]


@pytest.mark.anyio
async def test_mixed_lines_keep_their_order_and_empty_input_stays_empty():
    plain = CATALOG["ko"]["find_cat_risk"]["plain"]
    assert await rewrite_findings(["dynamic", KO_CATARACT, "dynamic"], "ko") == [
        {"text": "dynamic", "rewritten": False},
        {"text": plain, "rewritten": True},
        {"text": "dynamic", "rewritten": False},
    ]
    assert await rewrite_findings([], "ko") == []


def test_plain_findings_api_returns_fixed_wording_and_preserves_unknown_lines(client):
    response = client.post("/api/plain-findings", json={"lang": "ko", "findings": [KO_CATARACT, "unknown"]})
    assert response.status_code == 200
    assert response.json() == {"lines": [
        {"text": CATALOG["ko"]["find_cat_risk"]["plain"], "rewritten": True},
        {"text": "unknown", "rewritten": False},
    ]}
