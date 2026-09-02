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
    """또렷한 질감이 있는 더미 눈 사진.

    단색으로 만들면 흔들림 게이트(_sharpness == 0)에 걸려 'blurry'로 반려되므로,
    판정 분기를 검사할 수 없다. 실제 사진처럼 고주파 성분을 넣어준다.
    """
    import numpy as np
    rng = np.random.default_rng(7)
    base = np.full((224, 224, 3), (100, 80, 60), dtype=np.uint8)
    noise = rng.integers(-45, 46, (224, 224, 3))
    return Image.fromarray(np.clip(base.astype(int) + noise, 0, 255).astype(np.uint8))


@pytest.fixture
def loaded(monkeypatch):
    """가중치 로드 완료 상태로 만드는 기본 셋업."""
    monkeypatch.setattr(vision, "weights_loaded", True)
    # 얼굴 모드도 크롭마다 눈 게이트를 통과시키므로(2026-09-02) 기본은 '눈 맞음'으로 둔다
    monkeypatch.setattr(eye_validator, "check_eye", lambda i: (True, 0.95))


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
    monkeypatch.setattr(vision, "_predict_single", lambda t: 1.0)
    out = vision.predict_cataract(img)
    assert out["result_code"] == "normal"
    assert out["mode"] == "eye"
    assert out["eyes"] == [{"side": "single", "probability": 1.0, "code": "normal"}]
    assert out["closeup_suggested"] is False
    assert out["asymmetric"] is False


def test_경계구간_판정(monkeypatch, loaded, img):
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [])
    monkeypatch.setattr(eye_validator, "check_eye", lambda i: (True, 0.8))
    mid = (settings.borderline_threshold + settings.risk_threshold) / 2
    monkeypatch.setattr(vision, "_predict_single", lambda t: mid)
    out = vision.predict_cataract(img)
    assert out["result_code"] == "borderline"


def test_얼굴모드도_크롭마다_눈게이트를_거친다(monkeypatch, loaded, img):
    # MTCNN은 얼굴 기하에서 눈 '위치'만 추정한다 — 감은 눈·선글라스·안대도 좌표를 돌려주므로
    # 크롭이 진짜 눈인지 게이트로 확인해야 한다 (2026-09-02 실측: 확인 없이는 '정상 0.0%'가 나갔다)
    calls = []
    monkeypatch.setattr(eye_validator, "check_eye", lambda i: (calls.append(i) or True, 0.95))
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [img, img])
    monkeypatch.setattr(vision, "_predict_single", lambda t: 1.0)
    out = vision.predict_cataract(img)
    assert out["mode"] == "face" and len(calls) == 2


def test_얼굴모드_한쪽눈이라도_가려지면_eyes_hidden(monkeypatch, loaded, img):
    scores = iter([(True, 0.97), (False, 0.01)])
    monkeypatch.setattr(eye_validator, "check_eye", lambda i: next(scores))
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [img, img])
    def boom(t):
        raise AssertionError("가려진 눈은 모델 추론까지 가면 안 됩니다")
    monkeypatch.setattr(vision, "_predict_single", boom)
    out = vision.predict_cataract(img)
    assert out["result_code"] == "eyes_hidden"
    assert out["eyes_detected"] == 2 and out["eye_score"] == 0.01


def test_얼굴모드_검증기_불능이면_503(monkeypatch, loaded, img):
    monkeypatch.setattr(eye_validator, "check_eye", lambda i: (None, None))
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [img, img])
    with pytest.raises(HTTPException) as e:
        vision.predict_cataract(img)
    assert e.value.status_code == 503


def test_반사가_있어도_모델이_정상이면_통과(monkeypatch, loaded, img):
    # 반사는 판정을 '위험' 쪽으로만 밀므로, 반사 속에서도 '정상'이면 믿을 수 있다 (불필요한 재촬영 제거)
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [])
    monkeypatch.setattr(vision, "_glare_fraction", lambda t: 0.05)
    monkeypatch.setattr(vision, "_predict_single", lambda t: 1.0)   # 2.0부터는 uncertain(판단 어려움)
    assert vision.predict_cataract(img)["result_code"] == "normal"


def test_반사가_있고_모델이_위험이면_hold(monkeypatch, loaded, img):
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [])
    monkeypatch.setattr(vision, "_glare_fraction", lambda t: 0.05)
    monkeypatch.setattr(vision, "_predict_single", lambda t: 88.0)
    out = vision.predict_cataract(img)
    assert out["result_code"] == "hold" and out["glare"] == 0.05


def test_TTA는_기본_OFF이고_배치가_1장(monkeypatch, loaded, img):
    import torch
    seen = {}
    def fake_model(batch):
        seen["n"] = batch.shape[0]
        return torch.zeros(batch.shape[0], 2)
    monkeypatch.setattr(vision, "model", fake_model)
    assert settings.use_tta is False
    vision._predict_single(img)
    assert seen["n"] == 1
    monkeypatch.setattr(settings, "use_tta", True)
    vision._predict_single(img)
    assert seen["n"] == 2


def test_얼굴모드_편측위험_asymmetric(monkeypatch, loaded, img):
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [img, img])
    probs = iter([88.0, 1.0])                       # 왼눈 위험, 오른눈 정상 (2점부터는 uncertain)
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
    (1.99, "normal"),
    (2.0, "uncertain"),        # 판단 어려움 하한 — 이상(≥) (2026-09-02 신설)
    (24.99, "uncertain"),
    (25.0, "borderline"),      # 경계 하한 — 이상(≥)
    (49.99, "borderline"),
    (50.0, "risk"),            # 위험 문턱 — 이상(≥)
    (99.9, "risk"),
])
def test_3단계_판정_경계값(monkeypatch, prob, expected):
    # _classify의 '이상(≥)' 경계 계약을 검증. .env로 임계값을 튜닝한 환경에서도
    # skip되지 않도록 임계값을 테스트 안에서 고정한다(스킵하면 정작 임계값을
    # 만지는 환경에서 경계 검증이 사라짐).
    monkeypatch.setattr(settings, "risk_threshold", 50.0)
    monkeypatch.setattr(settings, "borderline_threshold", 25.0)
    code, _ = vision._classify(prob)
    assert code == expected


def test_애매한_신호는_눈클로즈업_재촬영을_권한다(monkeypatch, loaded, img):
    # 외부 테스트(2026-09-02): 옅은 초기 혼탁이 0~4.9점으로 나와 전부 '정상'으로 표시됐다.
    # 2~25점은 '판단 어려움'으로, 얼굴 모드의 경계 판정도 눈 클로즈업 재촬영으로 확인시킨다.
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [])
    monkeypatch.setattr(vision, "_predict_single", lambda t: 4.9)
    out = vision.predict_cataract(img)
    assert out["result_code"] == "uncertain" and out["closeup_suggested"] is True
    assert "판단이 어렵" in out["result"]
    monkeypatch.setattr(eye_detector, "extract_eye_crops", lambda i: [img, img])
    monkeypatch.setattr(vision, "_predict_single", lambda t: 30.0)
    out = vision.predict_cataract(img)
    assert out["result_code"] == "borderline" and out["closeup_suggested"] is True
    monkeypatch.setattr(vision, "_predict_single", lambda t: 90.0)
    assert vision.predict_cataract(img)["closeup_suggested"] is False

