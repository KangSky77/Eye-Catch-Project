"""predict_cataract의 분기 로직 — 모델/검출기/검증기는 전부 모킹.

실제 추론 정확도는 validate_real_photos.py / train 로그가 담당하고,
여기서는 '어떤 상황에서 어떤 판정 경로를 타는가'를 고정한다.
"""
import pytest
from PIL import Image
from fastapi import HTTPException

from app.core.config import settings
from app.services import vision, eye_detector, eye_validator


@pytest.fixture
def img():
    return Image.new("RGB", (224, 224), (100, 80, 60))


@pytest.fixture
def loaded(monkeypatch):
    """가중치 로드 완료 상태로 만드는 기본 셋업."""
    monkeypatch.setattr(vision, "weights_loaded", True)


def test_가중치_미로드시_503(monkeypatch, img):
    # 학습 안 된 모델의 무작위 예측이 의료 결과로 나가면 안 됨
    monkeypatch.setattr(vision, "weights_loaded", False)
    with pytest.raises(HTTPException) as e:
        vision.predict_cataract(img)
    assert e.value.status_code == 503


def test_눈검증기_불능이면_fail_closed_503(monkeypatch, loaded, img):
    # 검증기 장애 시 검증 없이 결과를 내보내지 않고 차단해야 함(fail-closed)
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [])
    monkeypatch.setattr(eye_validator, "check_eye", lambda i: (None, None))
    with pytest.raises(HTTPException) as e:
        vision.predict_cataract(img)
    assert e.value.status_code == 503


def test_비눈사진은_invalid_판정(monkeypatch, loaded, img):
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [])
    monkeypatch.setattr(eye_validator, "check_eye", lambda i: (False, 0.41))
    out = vision.predict_cataract(img)
    assert out["result_code"] == "invalid"
    assert out["eyes_detected"] == 0
    assert out["eye_score"] == 0.41


def test_눈클로즈업_정상판정(monkeypatch, loaded, img):
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [])
    monkeypatch.setattr(eye_validator, "check_eye", lambda i: (True, 0.8))
    monkeypatch.setattr(vision, "_predict_single", lambda t: 3.0)
    out = vision.predict_cataract(img)
    assert out["result_code"] == "normal"
    assert out["mode"] == "eye"
    assert out["eyes"] == [{"side": "single", "probability": 3.0, "code": "normal"}]
    assert out["asymmetric"] is False


def test_경계구간_판정(monkeypatch, loaded, img):
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [])
    monkeypatch.setattr(eye_validator, "check_eye", lambda i: (True, 0.8))
    mid = (settings.borderline_threshold + settings.risk_threshold) / 2
    monkeypatch.setattr(vision, "_predict_single", lambda t: mid)
    out = vision.predict_cataract(img)
    assert out["result_code"] == "borderline"


def test_얼굴모드는_눈검증기를_거치지_않음(monkeypatch, loaded, img):
    # MTCNN이 눈 위치를 이미 확인했으므로 OOD 게이트 생략 — 실수로 다시 타면 여기서 잡힘
    def boom(i):
        raise AssertionError("얼굴 모드에서는 check_eye를 호출하면 안 됩니다")
    monkeypatch.setattr(eye_validator, "check_eye", boom)
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [img, img])
    monkeypatch.setattr(vision, "_predict_single", lambda t: 1.0)
    out = vision.predict_cataract(img)
    assert out["mode"] == "face"


def test_얼굴모드_편측위험_asymmetric(monkeypatch, loaded, img):
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [img, img])
    probs = iter([88.0, 5.0])                       # 왼눈 위험, 오른눈 정상
    monkeypatch.setattr(vision, "_predict_single", lambda t: next(probs))
    out = vision.predict_cataract(img)
    assert out["probability"] == 88.0               # 두 눈 중 최댓값 기준(스크리닝)
    assert out["result_code"] == "risk"
    assert [e["side"] for e in out["eyes"]] == ["left", "right"]
    assert [e["code"] for e in out["eyes"]] == ["risk", "normal"]
    assert out["asymmetric"] is True


def test_얼굴모드_양눈위험은_asymmetric_아님(monkeypatch, loaded, img):
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [img, img])
    probs = iter([90.0, 85.0])
    monkeypatch.setattr(vision, "_predict_single", lambda t: next(probs))
    out = vision.predict_cataract(img)
    assert out["asymmetric"] is False


@pytest.mark.parametrize("prob,expected", [
    (0.0, "normal"),
    (24.99, "normal"),
    (25.0, "borderline"),      # 경계 하한 — 이상(≥)
    (49.99, "borderline"),
    (50.0, "risk"),            # 위험 문턱 — 이상(≥)
    (99.9, "risk"),
])
def test_3단계_판정_경계값(prob, expected):
    # 기본 임계값(50/25) 기준의 경계값 계약. .env로 임계값을 바꾼 환경이면 스킵.
    if settings.risk_threshold != 50.0 or settings.borderline_threshold != 25.0:
        pytest.skip("임계값이 기본값이 아닌 환경")
    code, _ = vision._classify(prob)
    assert code == expected
