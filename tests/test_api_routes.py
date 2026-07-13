"""API 엔드포인트 — 서비스 계층은 모킹하고 라우팅·직렬화·에러 처리만 검증.

주의: routes.py는 `from app.services.vision import predict_cataract`처럼 이름을
직접 가져오므로, 패치는 app.api.routes 모듈의 바인딩에 해야 적용된다.
"""
import pytest

import app.api.routes as routes
from tests.conftest import make_image_bytes


CANNED = {
    "probability": 3.2, "result": "특이 소견 없음 (정상)", "result_code": "normal",
    "mode": "eye", "eyes_detected": 0, "eye_probs": [3.2],
    "eyes": [{"side": "single", "probability": 3.2, "code": "normal"}],
    "asymmetric": False,
}


def test_analyze_eye_성공_응답형태(client, monkeypatch):
    monkeypatch.setattr(routes, "predict_cataract", lambda img: dict(CANNED))
    r = client.post("/api/analyze-eye", files={"file": ("e.jpg", make_image_bytes(), "image/jpeg")})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["result_code"] == "normal"
    assert body["eyes"][0]["side"] == "single"
    assert body["eye_score"] is None      # invalid 판정이 아닐 때는 미포함(None)


def test_analyze_eye_텍스트파일_400(client):
    r = client.post("/api/analyze-eye", files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_save_diagnosis_DB실패는_soft_fail(client, monkeypatch):
    # DB가 죽어도 200 + skipped — 앱 전체가 죽거나 내부 에러가 노출되면 안 됨
    async def broken(*a, **kw):
        raise RuntimeError("db down: host=secret-internal-host")
    monkeypatch.setattr(routes, "save_diagnosis", broken)
    r = client.post("/api/save-diagnosis", json={"cataract_result": "정상", "amsler_result": "정상"})
    assert r.status_code == 200
    assert r.json() == {"status": "skipped"}
    assert "secret-internal-host" not in r.text   # 내부 정보 비노출


def test_save_diagnosis_성공(client, monkeypatch):
    async def ok(*a, **kw):
        return 7
    monkeypatch.setattr(routes, "save_diagnosis", ok)
    r = client.post("/api/save-diagnosis", json={"cataract_result": "정상", "amsler_result": "정상"})
    assert r.json() == {"status": "saved", "id": 7}


def test_get_ai_opinion_스트리밍(client, monkeypatch):
    async def fake_stream(*a, **kw):
        yield "환자분"
        yield ", 안녕하세요"
    monkeypatch.setattr(routes, "get_gemma_opinion_stream", fake_stream)
    r = client.post("/api/get-ai-opinion", json={"cataract_res": "정상", "amsler_res": "정상"})
    assert r.status_code == 200
    assert r.text == "환자분, 안녕하세요"


def test_get_ai_opinion_110자_판독문자열_422아님(client, monkeypatch):
    # fr/es 경계+두눈 문자열(최대 110자) 회귀 방지 — API 레벨에서도 통과해야 함
    async def fake_stream(*a, **kw):
        yield "ok"
    monkeypatch.setattr(routes, "get_gemma_opinion_stream", fake_stream)
    r = client.post("/api/get-ai-opinion", json={"cataract_res": "R" * 110, "amsler_res": "normal"})
    assert r.status_code == 200


def test_get_ai_opinion_상한초과는_422(client):
    r = client.post("/api/get-ai-opinion", json={"cataract_res": "R" * 250, "amsler_res": "normal"})
    assert r.status_code == 422


def test_generate_next_question(client, monkeypatch):
    async def fake(*a, **kw):
        return "야간 운전 시 빛 번짐이 있나요?"
    monkeypatch.setattr(routes, "generate_next_question", fake)
    r = client.post("/api/generate-next-question", json={"cataract_res": "정상", "amsler_res": "정상"})
    assert r.json() == {"question": "야간 운전 시 빛 번짐이 있나요?"}
