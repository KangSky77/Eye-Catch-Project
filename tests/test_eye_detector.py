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
    # 클로즈업 경로에서 눈 게이트·눈 뜸 판정기를 거친다. 보류로 막으면 실제 백내장 클로즈업이 막힌다.
    _fake(monkeypatch, [[100, 150], [300, 150], [200, 200], [150, 250], [250, 250]],
          probs=[settings.face_prob_threshold - 0.01])
    assert eye_detector.extract_eye_crops(face_img) == []


def test_얼굴_검출_오류는_클로즈업으로_우회하지_않는다(monkeypatch, face_img):
    class BrokenMTCNN:
        def detect(self, img, landmarks=True):
            raise RuntimeError("detector unavailable")
    monkeypatch.setattr(eye_detector, "_get_mtcnn", lambda: BrokenMTCNN())
    with pytest.raises(eye_detector.EyeDetectionError):
        eye_detector.extract_eye_crops(face_img)


def test_여러_얼굴은_임의의_한_사람을_고르지_않는다(monkeypatch, face_img):
    boxes = np.array([[0, 0, 180, 300], [220, 0, 400, 300]], dtype=np.float32)
    probs = np.array([0.99, 0.98])
    landmarks = np.array([
        [[70, 120], [120, 120], [95, 160], [70, 200], [120, 200]],
        [[270, 120], [320, 120], [295, 160], [270, 200], [320, 200]],
    ], dtype=np.float32)
    monkeypatch.setattr(eye_detector, "_get_mtcnn", lambda: _FakeMTCNN(boxes, probs, landmarks))
    assert eye_detector.extract_eye_crops(face_img) is None


def test_배경의_작은_얼굴은_여러_얼굴로_세지_않는다(monkeypatch, face_img):
    # 2026-09-23: 벽의 가족사진·사무실 동료 얼굴 때문에 혼자 찍은 셀카가 '여러 얼굴'로 막혔다.
    boxes = np.array([[20, 0, 380, 300], [385, 5, 395, 15]], dtype=np.float32)   # 두 번째는 면적 0.09%
    probs = np.array([0.99, 0.99])
    landmarks = np.array([
        [[100, 150], [300, 150], [200, 200], [150, 250], [250, 250]],
        [[388, 9], [392, 9], [390, 11], [388, 13], [392, 13]],
    ], dtype=np.float32)
    monkeypatch.setattr(eye_detector, "_get_mtcnn", lambda: _FakeMTCNN(boxes, probs, landmarks))
    crops = eye_detector.extract_eye_crops(face_img)
    assert crops is not None and len(crops) == 2, "배경 얼굴 때문에 본인 셀카를 거부했다"
    assert crops[0].getpixel((5, 5)) == (255, 0, 0)   # 큰 얼굴의 눈을 잘랐다


def test_비슷한_크기의_두번째_얼굴은_여전히_보류(monkeypatch, face_img):
    # 함께 찍은 사람(실측 68% 크기)은 누구의 눈인지 정할 수 없으므로 계속 막는다.
    boxes = np.array([[0, 0, 200, 300], [220, 60, 380, 300]], dtype=np.float32)   # 64%
    probs = np.array([0.99, 0.99])
    landmarks = np.array([
        [[70, 120], [130, 120], [100, 160], [70, 200], [130, 200]],
        [[270, 150], [330, 150], [300, 190], [270, 230], [330, 230]],
    ], dtype=np.float32)
    monkeypatch.setattr(eye_detector, "_get_mtcnn", lambda: _FakeMTCNN(boxes, probs, landmarks))
    assert eye_detector.extract_eye_crops(face_img) is None


def test_얼굴_없으면_빈_리스트(monkeypatch, face_img):
    monkeypatch.setattr(eye_detector, "_get_mtcnn",
                        lambda: _FakeMTCNN(None, None, None))
    assert eye_detector.extract_eye_crops(face_img) == []


def test_MTCNN_미설치는_검출기_장애(monkeypatch, face_img):
    monkeypatch.setattr(eye_detector, "_get_mtcnn", lambda: None)
    with pytest.raises(eye_detector.EyeDetectionError):
        eye_detector.extract_eye_crops(face_img)


def test_초기화_실패도_검출기_장애(monkeypatch, face_img):
    def unavailable():
        raise RuntimeError("initialization failed")
    monkeypatch.setattr(eye_detector, "_get_mtcnn", unavailable)
    with pytest.raises(eye_detector.EyeDetectionError):
        eye_detector.extract_eye_crops(face_img)
    assert eye_detector.is_ready() is False


def test_잘린_얼굴은_재검출하고_원본에서_눈을_자른다(monkeypatch, face_img):
    calls = []
    class EdgeFace:
        def detect(self, img, landmarks=True):
            calls.append(img.size)
            pad = 0 if len(calls) == 1 else 100
            lm = np.array([[[100, 150], [300, 150], [200, 200], [150, 250], [250, 250]]]) + pad
            return np.array([[0, 0, 400, 300]]) + pad, np.array([0.90 if pad == 0 else 0.99]), lm
    monkeypatch.setattr(eye_detector, "_get_mtcnn", lambda: EdgeFace())
    crops = eye_detector.extract_eye_crops(face_img)
    assert calls == [(400, 300), (600, 500)]
    assert [c.size for c in crops] == [(180, 180), (180, 180)]
    assert [c.getpixel((90, 90)) for c in crops] == [(255, 0, 0), (0, 0, 255)]


@pytest.mark.parametrize("eyes", [
    [[172, 250], [178, 250]],  # 주름의 가짜 얼굴: 두 눈 간격이 6px
    [[-20, 150], [200, 150]],  # 여백에 생긴 눈 위치는 사용하지 않는다
])
def test_재검출의_작거나_여백에_있는_얼굴은_클로즈업을_막지_않는다(monkeypatch, face_img, eyes):
    calls = 0
    class SpuriousFace:
        def detect(self, img, landmarks=True):
            nonlocal calls
            calls += 1
            lm = np.array([[*eyes, [200, 200], [150, 250], [250, 250]]], dtype=float)
            if calls > 1:
                lm += 100
            return np.array([[0, 0, 400, 300]]), np.array([0.8 if calls == 1 else 0.99]), lm
    monkeypatch.setattr(eye_detector, "_get_mtcnn", lambda: SpuriousFace())
    assert eye_detector.extract_eye_crops(face_img) == []


def test_재검출에서_여러_얼굴이면_보류(monkeypatch, face_img):
    _fake(monkeypatch, [[100, 150], [300, 150], [200, 200], [150, 250], [250, 250]], probs=[0.9])
    monkeypatch.setattr(eye_detector, "_retry_edge_face", lambda *args: (np.zeros((2, 4)), np.ones(2), np.zeros((2, 5, 2))))
    assert eye_detector.extract_eye_crops(face_img) is None


def test_크롭은_이미지_경계를_넘지_않음(monkeypatch, face_img):
    # 눈이 이미지 가장자리에 붙어 있어도 크롭 박스가 음수/초과 좌표로 나가지 않아야 함
    _fake(monkeypatch, [[5, 5], [395, 5], [200, 200], [150, 250], [250, 250]])
    crops = eye_detector.extract_eye_crops(face_img)
    assert len(crops) == 2
    for c in crops:
        assert c.size[0] >= eye_detector.MIN_CROP_PX and c.size[1] >= eye_detector.MIN_CROP_PX
