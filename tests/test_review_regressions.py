"""Regressions reproduced during the September 5 full review."""
import asyncio

import pytest
from fastapi import HTTPException
from PIL import Image

from app.api import routes
from app.services import vision, eye_validator, llm


@pytest.mark.anyio
async def test_readiness_requires_eye_validator(monkeypatch):
    monkeypatch.setattr(vision, 'weights_loaded', True)
    monkeypatch.setattr(eye_validator, 'is_ready', lambda: False)
    result = await routes.readyz()
    assert getattr(result, 'status_code', 200) == 503


def test_each_eye_must_pass_sharpness(monkeypatch):
    img = Image.new('RGB', (32, 32))
    monkeypatch.setattr(vision, 'weights_loaded', True)
    monkeypatch.setattr(vision.eye_detector, 'extract_eye_crops', lambda _: [img, img])
    scores = iter([0.2, 0.001])
    monkeypatch.setattr(vision, '_sharpness', lambda _: next(scores))
    monkeypatch.setattr(eye_validator, 'check_eye', lambda _: (True, 0.99))
    def forbidden(_):
        pytest.fail('Blurry eye must not reach classification')
    monkeypatch.setattr(vision, '_predict_single', forbidden)
    assert vision.predict_cataract(img)['result_code'] == 'blurry'


@pytest.mark.anyio
async def test_decode_waits_for_inference_slot(monkeypatch):
    slots = asyncio.Semaphore(1)
    await slots.acquire()
    calls = []
    async def decode(_):
        calls.append(True)
        return Image.new('RGB', (8, 8))
    monkeypatch.setattr(routes, '_inference_slots', slots)
    monkeypatch.setattr(routes, 'validate_and_read_image', decode)
    task = asyncio.create_task(routes.analyze_eye(None))
    try:
        await asyncio.sleep(0.02)
        assert not calls
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    assert slots.locked()  # cancellation must not release somebody else's slot


@pytest.mark.anyio
async def test_llm_queue_emits_keepalive_and_cleans_cancelled_waiter(monkeypatch):
    slots = asyncio.Semaphore(1)
    await slots.acquire()
    monkeypatch.setattr(routes, '_llm_slots', slots)
    monkeypatch.setattr(routes, 'KEEPALIVE_INTERVAL', 0.01, raising=False)
    started = []
    async def source():
        started.append(True)
        yield 'text'
    stream = routes._limited_stream(source())
    try:
        assert await asyncio.wait_for(anext(stream), 0.3) == llm.KEEPALIVE
        assert not started
    finally:
        await stream.aclose()
    slots.release()
    await asyncio.wait_for(slots.acquire(), 0.1)
    assert slots.locked()


@pytest.mark.anyio
async def test_fully_filtered_opinion_is_an_error(monkeypatch):
    async def source(_):
        yield '정상입니다.\n'
    monkeypatch.setattr(llm, 'stream_with_keepalive', source)
    result = ''.join([part async for part in llm.sanitized_stream('test')])
    assert llm.ERROR_MARKER in result


def test_env_backups_are_ignored():
    import subprocess
    result = subprocess.run(['git', 'check-ignore', '.env.bak.20260904'],
                            capture_output=True, text=True)
    assert result.returncode == 0
