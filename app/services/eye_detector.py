"""
얼굴 사진에서 눈 부위만 잘라내는 서비스 (MTCNN 기반)
========================================================
백내장 모델은 '눈 클로즈업'으로 학습됐기 때문에 얼굴 전체 사진이 들어오면
눈 영역만 크롭해서 모델에 넣어야 합니다.

- MTCNN(facenet-pytorch): 얼굴 박스 + 5개 랜드마크(양쪽 눈 중심 포함) 검출
- 얼굴이 검출되면  → 양쪽 눈 크롭 리스트 반환
- 얼굴이 없으면    → 빈 리스트 반환 (vision.py가 원본 전체를 눈 클로즈업으로 간주)
- facenet-pytorch 미설치여도 앱은 정상 동작 (눈 크롭 기능만 비활성화)

설치:  uv pip install facenet-pytorch --no-deps --python .venv
       uv pip install requests --python .venv
  (--no-deps 이유: facenet-pytorch가 구버전 torch를 고정해서
   이미 설치된 torch 2.12+cu130을 다운그레이드하려는 것을 방지)
"""
import numpy as np
import torch
from PIL import Image

try:
    from facenet_pytorch import MTCNN
except ImportError:
    MTCNN = None

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 얼굴 검출 확신도 하한 — 눈 클로즈업 사진을 얼굴로 오인하는 것을 방지
FACE_PROB_THRESHOLD = 0.95
# 눈 사이 거리 대비 크롭 반변 비율 (0.45 → 눈+주변 흰자/눈꺼풀까지 포함)
EYE_CROP_RATIO = 0.45
# 크롭이 이보다 작으면 해상도가 부족해 분석 불가로 간주
MIN_CROP_PX = 32

_mtcnn = None


def is_available() -> bool:
    return MTCNN is not None


def _get_mtcnn():
    global _mtcnn
    if MTCNN is None:
        return None
    if _mtcnn is None:
        # keep_all=True: 모든 얼굴 검출 후 가장 확실한 얼굴 선택
        _mtcnn = MTCNN(keep_all=True, device=device)
    return _mtcnn


def extract_eye_crops(img: Image.Image) -> list[Image.Image]:
    """얼굴 사진이면 [왼눈, 오른눈] 크롭 반환, 아니면 빈 리스트.

    빈 리스트 = '얼굴 없음' → 호출자는 원본을 눈 클로즈업으로 처리하면 됨.
    """
    mtcnn = _get_mtcnn()
    if mtcnn is None:
        return []

    try:
        boxes, probs, landmarks = mtcnn.detect(img, landmarks=True)
    except Exception:
        return []  # 검출 실패는 조용히 클로즈업 경로로

    if boxes is None or landmarks is None:
        return []

    # 가장 확신도 높은 얼굴 1개 선택
    best = int(np.argmax(probs))
    if probs[best] < FACE_PROB_THRESHOLD:
        return []

    # 랜드마크 순서: [왼눈, 오른눈, 코, 입왼쪽, 입오른쪽]
    left_eye, right_eye = landmarks[best][0], landmarks[best][1]
    eye_dist = float(np.linalg.norm(np.array(right_eye) - np.array(left_eye)))
    half = max(eye_dist * EYE_CROP_RATIO, MIN_CROP_PX / 2)

    W, H = img.size
    crops = []
    for cx, cy in (left_eye, right_eye):
        l = int(max(cx - half, 0))
        t = int(max(cy - half, 0))
        r = int(min(cx + half, W))
        b = int(min(cy + half, H))
        if r - l >= MIN_CROP_PX and b - t >= MIN_CROP_PX:
            crops.append(img.crop((l, t, r, b)))
    return crops
