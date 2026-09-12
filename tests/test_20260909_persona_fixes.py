"""Exposure checks do not identify closed eyes or cloudy pupils."""
import numpy as np
from PIL import Image
from app.services import vision


def test_underexposure_boundary():
    assert vision._underexposed(Image.new('RGB', (224, 224), (34, 34, 34)))
    assert not vision._underexposed(Image.new('RGB', (224, 224), (35, 35, 35)))
    assert not vision._underexposed(Image.new('RGB', (224, 224), (150, 150, 150)))


def test_off_center_visible_area_is_not_discarded():
    pixels = np.zeros((224, 224, 3), dtype=np.uint8)
    pixels[:70] = 180
    assert not vision._underexposed(Image.fromarray(pixels))


def test_dark_photo_returns_no_medical_score(monkeypatch):
    monkeypatch.setattr(vision, 'weights_loaded', True)
    monkeypatch.setattr(vision.eye_detector, 'extract_eye_crops', lambda img: [])
    monkeypatch.setattr(vision, '_sharpness', lambda img: 100)
    def unexpected(*args):
        raise AssertionError('Dark photos must stop before classification')
    monkeypatch.setattr(vision.eye_validator, 'check_eye', unexpected)
    result = vision.predict_cataract(Image.new('RGB', (224, 224), (20, 20, 20)))
    assert result['result_code'] == 'dark'
    assert not result.get('eyes')
