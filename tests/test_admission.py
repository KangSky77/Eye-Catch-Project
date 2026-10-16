"""Admission fairness, expiration, job lifetime and server enforcement."""
import asyncio
from collections import OrderedDict
from types import SimpleNamespace

import httpx
import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from app.services.admission import Admission, AdmissionUploadGate, COOKIE, require_admission


def test_hundred_visitors_get_two_seats_and_fifo_survives_refresh():
    queue = Admission()
    tokens = [queue.join(None)[0] for _ in range(100)]
    assert [queue.status(t)["state"] for t in tokens[:3]] == ["active", "active", "waiting"]
    assert queue.join(tokens[20])[0] == tokens[20]
    assert queue.status(tokens[20])["position"] == 19
    queue.release(tokens[0])
    assert queue.status(tokens[2])["state"] == "active"
    assert queue.status(tokens[3])["position"] == 1
    assert queue.join(None)[1]["position"] == 98
    assert queue.status(tokens[99])["active"] == 2


def test_closed_or_idle_visitor_expires_and_fresh_waiter_enters():
    now = [0.0]
    queue = Admission(capacity=1, clock=lambda: now[0])
    first, _ = queue.join(None)
    waiting, _ = queue.join(None)
    for t in (50, 100):
        now[0] = t
        assert queue.status(waiting)["state"] == "waiting"
    now[0] = 121
    assert queue.status(waiting)["state"] == "active"
    assert queue.status(first)["state"] == "idle"


def test_expired_waiter_cannot_jump_a_fresh_waiter():
    now = [0.0]
    queue = Admission(capacity=1, clock=lambda: now[0])
    first, _ = queue.join(None)
    stale, _ = queue.join(None)
    now[0] = 50
    fresh, _ = queue.join(None)
    now[0] = 61
    queue.release(first)
    assert queue.status(stale)["state"] == "idle"
    assert queue.status(fresh)["state"] == "active"


def test_active_job_keeps_seat_and_finish_waits_until_work_ends():
    now = [0.0]
    queue = Admission(capacity=1, clock=lambda: now[0])
    token, _ = queue.join(None)
    with queue.job(token):
        now[0] = 500
        waiting, status = queue.join(None)
        assert status["state"] == "waiting"
        queue.release(token)
        assert queue.status(waiting)["state"] == "waiting"
    assert queue.status(waiting)["state"] == "active"


def test_duplicate_work_and_unknown_cookies_are_rejected():
    queue = Admission()
    token, _ = queue.join(None)
    with queue.job(token):
        with pytest.raises(HTTPException) as error:
            with queue.job(token):
                pass
        assert error.value.status_code == 409
    with pytest.raises(HTTPException) as error:
        with queue.job("forged"):
            pass
    assert error.value.status_code == 429
    with queue.job(token):
        pass


def test_experimental_model_explanation_also_requires_a_seat(monkeypatch):
    from app.core.config import settings
    queue = Admission()
    monkeypatch.setattr(settings, 'explain_mode', 'ai_checked')
    assert queue.status(None)['explanation_requires_seat'] is True
    monkeypatch.setattr(settings, 'explain_mode', 'fixed')
    assert queue.status(None)['explanation_requires_seat'] is False


def test_queue_size_is_bounded():
    queue = Admission(capacity=1, max_waiting=2)
    for _ in range(3):
        queue.join(None)
    with pytest.raises(HTTPException) as error:
        queue.join(None)
    assert error.value.status_code == 503


@pytest.fixture
def admitted_app(monkeypatch):
    from app.main import app
    store = app.state.admission
    monkeypatch.setattr(store, "enabled", True)
    monkeypatch.setattr(store, "visitors", OrderedDict())
    return app


def test_entry_is_small_and_api_bypass_is_rejected(admitted_app, monkeypatch):
    import app.api.routes as routes
    def should_not_run(*args):
        pytest.fail("waiting visitor reached expensive inference")
    monkeypatch.setattr(routes, "predict_cataract", should_not_run)
    clients = [TestClient(admitted_app) for _ in range(3)]
    first, second, third = clients
    assert 'data-waiting-entry' in third.get('/').text
    assert 'html2pdf' not in third.get('/').text
    for c in clients:
        c.post('/api/admission/join')
    assert third.get('/api/admission/status').json()['position'] == 1
    assert third.get('/app', follow_redirects=False).status_code == 303
    assert third.post('/api/analyze-eye', content=b'not even multipart').status_code == 429
    payload = {'cataract_res': 'synthetic', 'amsler_res': 'not performed'}
    assert third.post('/api/get-ai-opinion', json=payload).status_code == 429
    token = third.cookies[COOKIE]
    third.get('/')
    assert third.post('/api/admission/join').cookies[COOKIE] == token
    first.post('/api/admission/leave')
    assert third.get('/api/admission/status').json()['state'] == 'active'
    assert 'app-core.js' in third.get('/app').text
    cookie = second.post('/api/admission/join').headers['set-cookie']
    assert 'HttpOnly' in cookie and 'SameSite=lax' in cookie


def test_fixed_emergency_advice_does_not_wait_for_admission(admitted_app):
    c = TestClient(admitted_app)
    response = c.post('/api/get-ai-opinion', json={
        'lang': 'ko', 'cataract_res': 'synthetic', 'amsler_res': 'not performed',
        'red_flags': ['rf_sudden_loss'], 'triage_level': 'urgent'})
    assert response.status_code == 200
    assert '지금 바로' in response.text


def test_reviewed_score_explanation_needs_no_visit_even_when_queue_is_full(admitted_app):
    queue = admitted_app.state.admission
    for _ in range(queue.capacity):
        queue.join(None)
    response = TestClient(admitted_app).post('/api/chat-with-gemma', json={
        'user_msg': 'AI 특징 점수 0/100의 의미', 'lang': 'ko', 'context': ''})
    assert response.status_code == 200
    assert '질병에 걸릴 확률이 아니라' in response.text
    assert '눈 전체의 건강 상태를 평가하는 점수도 아닙니다' in response.text


@pytest.mark.anyio
async def test_upload_gate_rejects_before_reading_any_body():
    queue = Admission()
    async def inner(scope, receive, send):
        pytest.fail('unadmitted request was forwarded')
    gate = AdmissionUploadGate(inner, queue)
    async def receive():
        pytest.fail('unadmitted upload body was read')
    messages = []
    async def send(message):
        messages.append(message)
    await gate({'type': 'http', 'method': 'POST', 'path': '/api/analyze-eye',
                'headers': [], 'app': SimpleNamespace(state=SimpleNamespace(admission=queue))}, receive, send)
    assert messages[0]['status'] == 429


@pytest.mark.anyio
async def test_streaming_dependency_pins_seat_until_response_finishes():
    now = [0.0]
    app = FastAPI()
    app.state.admission = Admission(capacity=1, clock=lambda: now[0])
    token, _ = app.state.admission.join(None)
    started, finish = asyncio.Event(), asyncio.Event()
    @app.get('/slow', dependencies=[Depends(require_admission)])
    async def slow():
        async def body():
            started.set()
            yield 'start'
            await finish.wait()
            yield 'end'
        return StreamingResponse(body())
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test',
                                 cookies={COOKIE: token}) as c:
        request = asyncio.create_task(c.get('/slow'))
        await started.wait()
        now[0] = 500
        waiting, _ = app.state.admission.join(None)
        app.state.admission.release(token)
        assert app.state.admission.status(waiting)['state'] == 'waiting'
        finish.set()
        response = await request
        assert response.text == 'startend'
        assert app.state.admission.status(waiting)['state'] == 'active'
