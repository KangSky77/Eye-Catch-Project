"""Result explanations keep fixed meanings, and missing mandatory gates recover."""
import asyncio
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
import torch

from app.api import routes
from app.schemas.ai import ChatRequest
from app.services import eye_validator as ev, explain_check, llm


@pytest.fixture(scope='module')
def fixed_result_lines():
    if not shutil.which('node'):
        pytest.skip('Node is required to read the report translations')
    script = (
        "const fs=require('fs'),vm=require('vm'),c={window:{},document:{}};vm.createContext(c);"
        "for(const f of ['data.js','app-report-text.js'])vm.runInContext(fs.readFileSync('static/'+f,'utf8'),c);"
        "const t=vm.runInContext('translations',c);process.stdout.write(JSON.stringify(Object.fromEntries("
        "Object.entries(t).map(([lang,v])=>[lang,[v.find_cat_risk,"
        "v.find_ams_abnormal.replace('{eye}',v.ams_result_left),v.tri_now]]))))"
    )
    result = subprocess.run(['node','-e',script], cwd=Path(__file__).parents[1],
                            capture_output=True,text=True,encoding='utf-8',check=True)
    return json.loads(result.stdout)


@pytest.mark.anyio
@pytest.mark.parametrize('lang,reversed_text', [
    ('ko', '수정체 혼탁은 없습니다. 왼쪽 눈 격자 왜곡은 없습니다. 안과에 빨리 갈 필요는 없습니다.'),
    ('en', 'The photo shows no cloudiness. The left-eye Amsler grid showed no distortion. You do not need to see an eye doctor soon.'),
    ('es', 'El cristalino está sin opacidad. La rejilla del ojo izquierdo está sin distorsión. No necesita ir al oftalmólogo pronto.'),
    ('fr', 'Le cristallin est sans opacité. La grille de l’œil gauche est sans distorsion. Vous ne devez pas consulter un ophtalmologue rapidement.'),
    ('ja', '水晶体の混濁はありません。左目の格子のゆがみはありません。早めに眼科へ行く必要はありません。'),
    ('zh', '晶状体不混浊。左眼网格不扭曲。不必尽快去眼科。'),
])
async def test_negated_findings_never_reach_result_explanation(monkeypatch, lang, reversed_text, fixed_result_lines):
    calls = []
    async def reversed_model(*args, **kwargs):
        calls.append(True)
        yield reversed_text
    monkeypatch.setattr(llm, 'sanitized_stream', reversed_model)
    # These original/plain pairs are human-reviewed. An arbitrary model output
    # cannot override them, regardless of which vocabulary the model uses.
    originals = fixed_result_lines[lang]
    expected = await explain_check.fallback_text(originals, lang)
    result = ''.join([c async for c in llm.chat_with_gemma_stream(
        'Explain', 'context', lang, explain_results=True,
        explain_required=['cat_risk', 'ams_left', 'tri_now'], explain_fallback=originals)])
    assert result == expected
    assert reversed_text not in result
    assert calls == []


@pytest.mark.anyio
@pytest.mark.parametrize('required', [[], ['cat_risk']])
@pytest.mark.parametrize('lines', [[], ['  ']])
async def test_missing_report_does_not_fall_back_to_free_generation(monkeypatch, required, lines):
    async def forbidden(*args, **kwargs):
        pytest.fail('Missing result facts must not trigger free generation')
        yield ''
    monkeypatch.setattr(llm, 'sanitized_stream', forbidden)
    result = ''.join([c async for c in llm.chat_with_gemma_stream(
        'Explain', 'untrusted context', 'en', explain_results=True,
        explain_required=required, explain_fallback=lines)])
    assert result == llm.ERROR_MARKER + 'EXPLANATION_UNAVAILABLE'


@pytest.mark.anyio
async def test_fixed_explanation_does_not_wait_for_busy_model(monkeypatch):
    slots = asyncio.Semaphore(1)
    await slots.acquire()
    monkeypatch.setattr(routes, '_llm_slots', slots)
    req = ChatRequest(user_msg='Explain', explain_results=True, lang='en',
                      explain_fallback=['Reported findings.', 'Recommended action.'])
    response = await routes.chat_with_gemma(req)
    try:
        assert await asyncio.wait_for(anext(response.body_iterator), 0.2) == 'Reported findings. Recommended action.'
        assert slots.locked()
    finally:
        await response.body_iterator.aclose()
        slots.release()


def test_complete_report_payload_has_a_bounded_size():
    ChatRequest(user_msg='Explain', explain_results=True, explain_fallback=['x' * 2000] * 20)
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ChatRequest(user_msg='Explain', explain_fallback=['x' * 2001])
    with pytest.raises(ValidationError):
        ChatRequest(user_msg='Explain', explain_fallback=['x'] * 21)


@pytest.fixture
def isolated_validator(monkeypatch, tmp_path):
    centroid = tmp_path / 'centroid.npy'
    np.save(centroid, np.ones(512, dtype=np.float32))
    gate = tmp_path / 'gate.npz'
    monkeypatch.setattr(ev, '_CENTROID_PATH', centroid)
    monkeypatch.setattr(ev, '_GATE_PATH', gate)
    monkeypatch.setattr(ev, 'device', torch.device('cpu'))
    for key, value in {'_loaded':False, '_net':None, '_centroid':None, '_gate_w':None,
                       '_gate_b':0.0, '_gate_thr':None, '_open_w':None, '_open_cnn':None}.items():
        monkeypatch.setattr(ev, key, value)
    calls = []
    class Backbone(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.layer3 = torch.nn.Identity()
            self.layer4 = torch.nn.Identity()
    def load_backbone(**kwargs):
        calls.append(True)
        return Backbone()
    def load_open_gate():
        ev._open_w = torch.ones(512)
        return True
    monkeypatch.setattr(ev.models, 'resnet18', load_backbone)
    monkeypatch.setattr(ev, '_load_open_gate', load_open_gate)
    return gate, calls


def write_gate(path, **overrides):
    values = {'w':np.ones(512, dtype=np.float32), 'b':np.array([0.0]), 'threshold':np.array(0.5)}
    values.update(overrides)
    np.savez(path, **values)


def test_missing_base_gate_recovers_after_file_arrives_without_restart(isolated_validator):
    gate, calls = isolated_validator
    assert ev.warmup() is False
    assert ev.is_ready() is False
    assert ev.check_eye(None) == (None, None)
    assert ev._loaded is False
    assert calls == [], 'Do not repeatedly load the backbone while the mandatory gate is missing'
    write_gate(gate)
    assert ev.is_ready() is True
    assert ev._loaded is True and ev._gate_w is not None
    assert ev._try_load() is True
    assert len(calls) == 1, 'Only a successful complete load is cached'


@pytest.mark.parametrize('bad', [
    {'w':np.ones(511)}, {'w':np.full(512, np.nan)}, {'b':np.array([np.nan])},
    {'threshold':np.array(0.0)}, {'threshold':np.array(1.0)}, {'threshold':np.array(np.nan)},
])
def test_invalid_base_gate_fails_closed_and_retries_when_repaired(isolated_validator, bad):
    gate, calls = isolated_validator
    write_gate(gate, **bad)
    assert ev._try_load() is False
    assert ev._loaded is False and ev._gate_w is None
    assert ev.check_eye(None) == (None, None)
    assert calls == []
    write_gate(gate)
    assert ev.is_ready() is True


def test_corrupt_base_gate_is_not_cached(isolated_validator):
    gate, calls = isolated_validator
    gate.write_bytes(b'not a numpy archive')
    assert ev.is_ready() is False
    assert ev._loaded is False
    write_gate(gate)
    assert ev.is_ready() is True
    assert len(calls) == 1
