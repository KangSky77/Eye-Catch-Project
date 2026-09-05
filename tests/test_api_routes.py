"""API 엔드포인트 — 서비스 계층은 모킹하고 라우팅·직렬화·에러 처리만 검증.

주의: routes.py는 `from app.services.vision import predict_cataract`처럼 이름을
직접 가져오므로, 패치는 app.api.routes 모듈의 바인딩에 해야 적용된다.
"""
import pytest

import app.api.routes as routes
from tests.conftest import make_image_bytes


def test_healthz는_항상_liveness를_반환한다(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_readyz는_모델이_없으면_503(client, monkeypatch):
    from app.services import vision
    monkeypatch.setattr(vision, "weights_loaded", False)
    r = client.get("/readyz")
    assert r.status_code == 503
    assert r.json() == {"status": "not_ready", "model": "unavailable"}


def test_readyz는_모델이_로드되면_200(client, monkeypatch):
    from app.services import vision
    from app.services import eye_validator
    monkeypatch.setattr(vision, "weights_loaded", True)
    monkeypatch.setattr(eye_validator, "is_ready", lambda: True)
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "model": "ready"}


CANNED = {
    "probability": 3.2, "result": "백내장 의심 소견 없음", "result_code": "normal",
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


def test_흔들린_사진은_판정대신_재촬영을_요청한다():
    """초점이 나간 사진은 사람도 판독할 수 없다.
    실측(눈 사진 141장, 크기 비례 모션 블러): 임계 0.030에서 심한 흔들림(3.5%)의
    74%를 잡고 멀쩡한 사진 거부는 2.1%."""
    from PIL import Image, ImageDraw, ImageFilter
    from app.services import vision

    # 눈처럼 '경계가 뚜렷한 구조'를 가진 그림으로 검사한다.
    # 랜덤 노이즈는 선명도가 15를 넘어(실제 눈 사진 중앙값 0.175) 기준이 되지 못한다.
    eye = Image.new("RGB", (224, 224), (120, 95, 80))
    d = ImageDraw.Draw(eye)
    d.ellipse([60, 60, 164, 164], fill=(70, 60, 55))     # 홍채
    d.ellipse([95, 95, 129, 129], fill=(20, 18, 16))     # 동공
    d.rectangle([0, 0, 224, 40], fill=(180, 160, 140))   # 눈꺼풀

    assert vision._sharpness(eye) >= vision.BLUR_MIN_SHARPNESS

    # 흔들린 사진 — 경계가 뭉개지면 게이트에 걸린다
    blurred = eye.filter(ImageFilter.GaussianBlur(radius=4))
    assert vision._sharpness(blurred) < vision.BLUR_MIN_SHARPNESS

    # 흐려질수록 선명도는 단조 감소해야 한다
    vals = [vision._sharpness(eye.filter(ImageFilter.GaussianBlur(radius=r))) for r in (0, 1, 2)]
    assert vals[0] > vals[1] > vals[2]


def test_단색_이미지는_선명도0으로_처리된다():
    """대비가 없으면 라플라시안 분산도 0이라 0으로 나눌 뻔한다.
    눈 사진이 아니므로 어차피 걸러져야 한다."""
    from PIL import Image
    from app.services import vision
    assert vision._sharpness(Image.new("RGB", (200, 200), (128, 128, 128))) == 0.0


def test_흔들림을_반사보다_먼저_판정한다():
    """흔들려서 뿌연 것을 '반사'라고 안내하면 엉뚱한 재촬영을 시키게 된다."""
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "app" / "services" / "vision.py").read_text(encoding="utf-8")
    assert src.index('"blurry"') < src.index('"hold"')
