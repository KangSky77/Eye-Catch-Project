"""얼굴→눈 크롭 — MTCNN은 가짜 객체로 대체하고 좌/우 결정·크롭 경계·폴백만 검사."""
import numpy as np
import pytest
from PIL import Image

from app.core.config import settings
from app.services import eye_detector


class _FakeMTCNN:
    def __init__(self, boxes, probs, landmarks):
        self._out = (boxes, probs, landmarks)

    def detect(self, img, landmarks=True):
        return self._out


@pytest.fixture
def face_img():
    # 왼쪽 절반 빨강 / 오른쪽 절반 파랑 → 크롭이 어느 쪽에서 왔는지 픽셀 색으로 판별
    img = Image.new("RGB", (400, 300), (255, 0, 0))
    img.paste((0, 0, 255), (200, 0, 400, 300))
    return img


def _fake(monkeypatch, landmarks, probs=None):
    lm = np.array([landmarks], dtype=np.float32)
    pr = np.array(probs if probs is not None else [0.99])
    boxes = np.array([[0, 0, 400, 300]], dtype=np.float32)
    monkeypatch.setattr(eye_detector, "_get_mtcnn", lambda: _FakeMTCNN(boxes, pr, lm))


def test_눈_순서는_랜드마크_순서가_아니라_사진_x좌표로(monkeypatch, face_img):
    # MTCNN이 [오른쪽(x=300), 왼쪽(x=100)] 순으로 줘도 결과는 [사진 왼쪽, 사진 오른쪽]이어야
    # vision.py의 ["left", "right"] 라벨이 실제 위치와 맞는다
    _fake(monkeypatch, [[300, 150], [100, 150], [200, 200], [150, 250], [250, 250]])
    crops = eye_detector.extract_eye_crops(face_img)
    assert len(crops) == 2
    assert crops[0].getpixel((5, 5)) == (255, 0, 0)   # 왼쪽 크롭 = 빨강 영역
    assert crops[1].getpixel((5, 5)) == (0, 0, 255)   # 오른쪽 크롭 = 파랑 영역


def test_얼굴_확신도가_낮으면_클로즈업_경로(monkeypatch, face_img):
    _fake(monkeypatch, [[100, 150], [300, 150], [200, 200], [150, 250], [250, 250]],
          probs=[settings.face_prob_threshold - 0.01])
    assert eye_detector.extract_eye_crops(face_img) == []


def test_얼굴_없으면_빈_리스트(monkeypatch, face_img):
    monkeypatch.setattr(eye_detector, "_get_mtcnn",
                        lambda: _FakeMTCNN(None, None, None))
    assert eye_detector.extract_eye_crops(face_img) == []


def test_MTCNN_미설치면_빈_리스트(monkeypatch, face_img):
    monkeypatch.setattr(eye_detector, "_get_mtcnn", lambda: None)
    assert eye_detector.extract_eye_crops(face_img) == []


def test_크롭은_이미지_경계를_넘지_않음(monkeypatch, face_img):
    # 눈이 이미지 가장자리에 붙어 있어도 크롭 박스가 음수/초과 좌표로 나가지 않아야 함
    _fake(monkeypatch, [[5, 5], [395, 5], [200, 200], [150, 250], [250, 250]])
    crops = eye_detector.extract_eye_crops(face_img)
    assert len(crops) == 2
    for c in crops:
        assert c.size[0] >= eye_detector.MIN_CROP_PX and c.size[1] >= eye_detector.MIN_CROP_PX
