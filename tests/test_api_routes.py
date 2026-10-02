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
    monkeypatch.setattr(routes.eye_detector, "is_ready", lambda: True)
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "model": "ready"}


def test_readyz는_얼굴검출기가_없으면_503(client, monkeypatch):
    monkeypatch.setattr(routes.vision, "weights_loaded", True)
    monkeypatch.setattr(routes.eye_validator, "is_ready", lambda: True)
    monkeypatch.setattr(routes.eye_detector, "is_ready", lambda: False)
    assert client.get("/readyz").status_code == 503


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
    # 기준 목록은 항상 있는 필드다 — 판독기가 알려주지 않으면 빈 목록(화면이 요약을 숨긴다)
    assert body["checks"] == []


def test_tiny_upload_returns_resolution_code_without_inference(client, monkeypatch):
    monkeypatch.setattr(routes.vision, "weights_loaded", True)
    monkeypatch.setattr(routes.eye_detector, "extract_eye_crops", lambda _: pytest.fail("too small for detector"))
    r = client.post("/api/analyze-eye", files={"file": ("tiny.png", make_image_bytes(18, 14, fmt="PNG"), "image/png")})
    assert r.status_code == 200
    assert r.json()["result_code"] == "low_resolution"
    assert r.json()["eyes"] == [] and r.json()["eye_probs"] == []
    # 화면은 왜 막혔는지를 기준별로 보여준다 — 판정이 없을 때도 기준 목록은 와야 한다
    assert {c["key"]: c["ok"] for c in r.json()["checks"]}["resolution"] is False


def test_analyze_eye_텍스트파일_400(client):
    r = client.post("/api/analyze-eye", files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_original_compression_flag_cannot_be_lost_or_cleared(client, monkeypatch):
    seen = []
    def predict(image):
        seen.append(image.info.get('heavy_jpeg_compression'))
        return {'result_code':'compressed' if seen[-1] else 'normal', 'probability':0, 'result':'test'}
    monkeypatch.setattr(routes, 'predict_cataract', predict)
    # A resized PNG carries the original JPEG's compression warning.
    r = client.post('/api/analyze-eye', data={'source_compressed':'true'},
                    files={'file':('resized.png',make_image_bytes(), 'image/png')})
    assert r.status_code == 200 and r.json()['result_code'] == 'compressed'
    # A false client flag can never override server-detected JPEG compression.
    import io
    from PIL import Image
    buf=io.BytesIO(); Image.new('RGB',(48,48)).save(buf,format='JPEG',quality=35)
    r = client.post('/api/analyze-eye', data={'source_compressed':'false'},
                    files={'file':('original.jpg',buf.getvalue(), 'image/jpeg')})
    assert r.status_code == 200 and r.json()['result_code'] == 'compressed'
    assert seen == [True, True]


def test_removed_save_endpoint_returns_not_found(client):
    response = client.post("/api/save-diagnosis", json={"consent_to_store": True})
    assert response.status_code == 404


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
        return {"question": "눈을 다친 적이 있나요?", "answer_type": "yesno"}
    monkeypatch.setattr(routes, "generate_personalized_question", fake)
    r = client.post("/api/generate-next-question", json={"cataract_res": "정상", "amsler_res": "정상"})
    assert r.json() == {"question": "눈을 다친 적이 있나요?", "answer_type": "yesno"}


@pytest.mark.parametrize("signals", [{"red_flags": ["rf_acute"]}, {"triage_level": "urgent"}])
def test_응급_고정안내는_LLM_대기열을_우회한다(client, monkeypatch, signals):
    def blocked(*args, **kwargs):
        pytest.fail("Emergency advice must not acquire an LLM slot")
    monkeypatch.setattr(routes, "_limited_stream", blocked)
    r = client.post("/api/get-ai-opinion", json={
        "cataract_res": "normal", "amsler_res": "normal", "lang": "ko", **signals,
    })
    assert r.status_code == 200
    assert r.text.startswith("<<<SUMMARY>>>\n지금 바로 안과 진료를 받으세요.")
    assert len(r.text.split("<<<SUMMARY>>>\n")[1].splitlines()) == 3


def test_next_question_ignores_model_prose_and_returns_catalog_copy(client, monkeypatch):
    async def fake(*a, **kw):
        return {"question_id": "eye_injury", "question": "시력 변화를 설명해 주세요."}
    monkeypatch.setattr("app.services.llm.generate_json", fake)
    r = client.post("/api/generate-next-question", json={"cataract_res": "정상", "amsler_res": "정상"})
    assert r.json()["answer_type"] == "yesno"
    assert r.json()["question"] == "눈을 다친 적이 있나요?"
    assert r.json()["question_id"] == "eye_injury"


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

def test_personalized_route_returns_generated_question_after_review(client, monkeypatch):
    responses = iter([{'topic': 'symptom_side', 'question': '흐리게 보이는 느낌이 한쪽 눈에만 있나요?'}, {'verdict': 'ok'}])
    async def fake(*_):
        return next(responses)
    monkeypatch.setattr('app.services.llm.generate_json', fake)
    r = client.post('/api/generate-next-question', json={
        'cataract_res': 'uncertain', 'amsler_res': 'normal', 'cataract_code': 'uncertain',
        'symptom_answers': {'cat_foggy': True}, 'lang': 'ko'})
    assert r.status_code == 200
    assert r.json()['source'] == 'generated'
    assert r.json()['question'] == '흐리게 보이는 느낌이 한쪽 눈에만 있나요?'


def test_question_translation_route_keeps_semantics(client, monkeypatch):
    responses = iter([{'question': 'Is the blurred vision in only one eye?'}, {'equivalent': True}])
    async def fake(*_):
        return next(responses)
    monkeypatch.setattr('app.services.llm.generate_json', fake)
    r = client.post('/api/translate-question', json={
        'question': '흐리게 보이는 느낌이 한쪽 눈에만 있나요?', 'source_lang': 'ko', 'target_lang': 'en'})
    assert r.status_code == 200 and r.json()['translated'] is True
    assert r.json()['question'] == 'Is the blurred vision in only one eye?'

def test_explanation_intent_reaches_chat_service(client, monkeypatch):
    captured = {}
    async def fake(user_msg, context, lang, explain_results=False, facts=None,
                   explain_required=None, explain_fallback=None):
        captured['explain_results'] = explain_results
        captured['explain_required'] = explain_required
        captured['explain_fallback'] = explain_fallback
        yield 'report explanation'
    monkeypatch.setattr(routes, 'chat_with_gemma_stream', fake)
    response = client.post('/api/chat-with-gemma', json={
        'lang':'ko', 'user_msg':'내 검사 결과를 쉽게 설명해 줘', 'context':'확인된 결과', 'explain_results':True,
        'explain_required':['cat_risk', 'tri_weeks'], 'explain_fallback':['사진 결과', '몇 주 안에 검진']})
    assert response.status_code == 200
    assert captured['explain_results'] is True
    assert captured['explain_required'] == ['cat_risk', 'tri_weeks']
    assert captured['explain_fallback'] == ['사진 결과', '몇 주 안에 검진']


def test_챗봇_요청의_사실목록이_안전필터까지_전달된다(client, monkeypatch):
    """고혈압 '아니오'인 사람에게 챗봇이 혈압 관리를 권하던 문제(2026-09-29 실측 2/3) — 사실 필터로 막는다."""
    captured = {}
    async def fake(user_msg, context, lang, explain_results=False, facts=None,
                   explain_required=None, explain_fallback=None):
        captured['facts'] = facts
        yield 'ok'
    monkeypatch.setattr(routes, 'chat_with_gemma_stream', fake)
    r = client.post('/api/chat-with-gemma', json={'lang': 'ko', 'user_msg': '관리 방법', 'context': '',
                                                  'facts': ['Hypertension: no', '2년 내 검진 없음']})
    assert r.status_code == 200 and captured['facts'] == ['Hypertension: no', '2년 내 검진 없음']
    # 예전 프론트(facts 없음)도 그대로 동작한다
    assert client.post('/api/chat-with-gemma', json={'lang': 'ko', 'user_msg': '관리', 'context': ''}).status_code == 200
