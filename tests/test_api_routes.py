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
        return "야간 운전 시 빛 번짐이 있나요?", "yesno"
    monkeypatch.setattr(routes, "generate_next_question", fake)
    r = client.post("/api/generate-next-question", json={"cataract_res": "정상", "amsler_res": "정상"})
    assert r.json() == {"question": "야간 운전 시 빛 번짐이 있나요?", "answer_type": "yesno"}


def test_generate_next_question_서술형이면_answer_type이_text(client, monkeypatch):
    # 프론트가 이 값을 보고 네/아니오 버튼 대신 자유 입력칸을 띄운다.
    # 이 계약이 깨지면 사용자가 답할 수 없는 질문 앞에서 문진이 멈춘다.
    async def fake(*a, **kw):
        return "시력 변화를 자세히 설명해 주시겠어요?", "text"
    monkeypatch.setattr(routes, "generate_next_question", fake)
    r = client.post("/api/generate-next-question", json={"cataract_res": "정상", "amsler_res": "정상"})
    assert r.json()["answer_type"] == "text"


@pytest.mark.parametrize("params", [
    {"lat": 91, "lng": 127.0},      # 위도 상한 초과
    {"lat": -91, "lng": 127.0},
    {"lat": 37.5, "lng": 181},      # 경도 상한 초과
    {"lat": 37.5, "lng": -181},
])
def test_nearby_clinics_좌표범위_밖은_422(client, params):
    # 범위 밖 좌표를 그대로 통과시키면 카카오/Overpass로 무의미한 외부 요청이 나간다
    r = client.get("/api/nearby-clinics", params=params)
    assert r.status_code == 422


def test_nearby_clinics_정상좌표는_서비스로_전달(client, monkeypatch):
    async def fake(lat, lng):
        return {"source": "none", "clinics": [], "reason": "no_key", "echo": [lat, lng]}
    monkeypatch.setattr(routes, "search_eye_clinics", fake)
    r = client.get("/api/nearby-clinics", params={"lat": 37.5, "lng": 127.0})
    assert r.status_code == 200
    assert r.json()["echo"] == [37.5, 127.0]


def test_반사가_강하면_판정대신_보류를_돌려준다():
    """플래시 반사가 눈동자를 덮으면 모델이 그것을 수정체 혼탁으로 읽는다.
    실측(정상 눈 60장): 반사점 반경 10%에서 33%, 14%에서 70%가 '위험'으로 뒤집혔다.
    그래서 판정을 내리지 않고 재촬영을 요청한다."""
    from PIL import Image, ImageDraw
    from app.services import vision

    # 중앙에 순백 반사점이 있는 합성 눈 사진
    img = Image.new("RGB", (300, 300), (90, 70, 60))
    d = ImageDraw.Draw(img)
    d.ellipse([120, 120, 180, 180], fill=(255, 255, 255))
    assert vision._glare_fraction(img) >= vision.GLARE_MAX_FRACTION

    # 반사가 없는 사진은 게이트에 걸리지 않는다
    plain = Image.new("RGB", (300, 300), (90, 70, 60))
    assert vision._glare_fraction(plain) < vision.GLARE_MAX_FRACTION


def test_반사지표는_회백색_혼탁을_포화로_세지_않는다():
    """백내장의 수정체 혼탁은 회백색이라 포화(255)까지 가지 않는다.
    이 구분이 무너지면 진짜 백내장 사진이 재촬영 요청으로 반려된다."""
    from PIL import Image, ImageDraw
    from app.services import vision

    img = Image.new("RGB", (300, 300), (90, 70, 60))
    ImageDraw.Draw(img).ellipse([100, 100, 200, 200], fill=(205, 205, 200))  # 회백색
    assert vision._glare_fraction(img) < vision.GLARE_MAX_FRACTION
