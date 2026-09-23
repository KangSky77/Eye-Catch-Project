"""
얼굴 사진에서 눈 부위만 잘라내는 서비스 (MTCNN 기반)
========================================================
백내장 모델은 '눈 클로즈업'으로 학습됐기 때문에 얼굴 전체 사진이 들어오면
눈 영역만 크롭해서 모델에 넣어야 합니다.

- MTCNN(facenet-pytorch): 얼굴 박스 + 5개 랜드마크(양쪽 눈 중심 포함) 검출
- 얼굴이 검출되면  → 양쪽 눈 크롭 리스트 반환
- 얼굴이 없으면    → 빈 리스트 반환 (vision.py가 원본 전체를 눈 클로즈업으로 간주)
- 검출기 미설치·실행 실패는 EyeDetectionError (검증 없이 사진 판독하지 않음)

설치:  uv pip install facenet-pytorch --no-deps --python .venv
       uv pip install requests --python .venv
  (--no-deps 이유: facenet-pytorch가 구버전 torch를 고정해서
   이미 설치된 torch 2.12+cu130을 다운그레이드하려는 것을 방지)
"""
import threading
import logging
import numpy as np
import torch
from PIL import Image, ImageOps
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from facenet_pytorch import MTCNN
except ImportError:
    MTCNN = None

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 눈 사이 거리 대비 크롭 반변 비율 (0.45 → 눈+주변 흰자/눈꺼풀까지 포함)
EYE_CROP_RATIO = 0.45
# 크롭이 이보다 작으면 해상도가 부족해 분석 불가로 간주
MIN_CROP_PX = 32
# 가장 큰 얼굴 면적의 이 비율 미만인 얼굴은 배경(벽의 가족사진, 멀리 있는 사람)으로 본다.
# 2026-09-23 실사용 테스트: 혼자 찍은 셀카 8장 중 2장이 '여러 얼굴'로 막혔다 —
# 배경 얼굴은 본인 얼굴의 0.13~0.43%, 함께 찍은 두 번째 사람은 68%였다.
BACKGROUND_FACE_AREA_RATIO = 0.10


def _drop_background_faces(boxes, indices):
    """판독 대상이 될 수 없을 만큼 작은 얼굴을 후보에서 뺀다. 비슷한 크기의 두 번째 얼굴은 남긴다."""
    areas = {i: max(0.0, float(boxes[i][2] - boxes[i][0])) * max(0.0, float(boxes[i][3] - boxes[i][1]))
             for i in indices}
    largest = max(areas.values(), default=0.0)
    if largest <= 0:
        return list(indices)
    return [i for i in indices if areas[i] >= largest * BACKGROUND_FACE_AREA_RATIO]

_mtcnn = None


class EyeDetectionError(RuntimeError):
    """검출 실패를 '얼굴 없음/눈 클로즈업'으로 오해하지 않도록 구분한다."""


def _retry_edge_face(mtcnn, img):
    """잘린 얼굴 후보를 여백에서 재검출한다. 원본 픽셀과 판정 기준은 유지한다.

    저신뢰 후보를 일괄 차단하면 실제 백내장 클로즈업도 막힌다. 반대로 원본을
    그대로 판독하면 가려진 얼굴이 들어간다. 여백으로 경계를 복원한 재검출에서
    기존 얼굴 기준을 통과하고, 원본 안에 분석 가능한 두 눈 위치가 있을 때만
    얼굴 경로를 복구한다. 여백 자체는 눈 크롭/백내장 모델에 절대 넣지 않는다.
    """
    # 극단적으로 긴 24MP 입력도 여백 추가로 메모리를 수백 MP까지 키우지 않는다.
    work = img.copy()
    work.thumbnail((1600, 1600))
    pad = max(1, int(max(work.size) * 0.25))
    padded = ImageOps.expand(work, border=pad, fill=(128, 128, 128))
    boxes, probs, landmarks = mtcnn.detect(padded, landmarks=True)
    if boxes is None or landmarks is None:
        return None, None, None
    scale = np.array([img.width / work.width, img.height / work.height])
    landmarks = (np.asarray(landmarks, dtype=np.float32) - pad) * scale
    boxes = (np.asarray(boxes, dtype=np.float32) - pad) * np.tile(scale, 2)
    usable = []
    for i, prob in enumerate(probs):
        eyes = landmarks[i][:2]
        # 재검출이 작은 주름을 얼굴로 착각할 수 있다. 크롭을 32px로 인위적으로
        # 키우지 않아도 두 눈을 검사할 해상도가 있어야 재검출을 채택한다.
        if (prob >= settings.face_prob_threshold and np.isfinite(eyes).all()
                and all(0 <= x < img.width and 0 <= y < img.height for x, y in eyes)
                and np.linalg.norm(eyes[1] - eyes[0]) * 2 * EYE_CROP_RATIO >= MIN_CROP_PX):
            usable.append(i)
    if not usable:
        return None, None, None
    return boxes[usable], np.asarray(probs)[usable], landmarks[usable]


def is_available() -> bool:
    return MTCNN is not None


_detector_lock = threading.Lock()

def _get_mtcnn():
    global _mtcnn
    if MTCNN is None:
        return None
    if _mtcnn is None:
        with _detector_lock:
            if _mtcnn is None:
                # keep_all=True: 모든 얼굴 검출 후 가장 확실한 얼굴 선택
                _mtcnn = MTCNN(keep_all=True, device=device)
    return _mtcnn


def warmup() -> bool:
    """서버 시작 시 호출하여 MTCNN 가중치 로딩 및 초기 오버헤드 제거"""
    return _get_mtcnn() is not None


def is_ready() -> bool:
    """패키지 설치 여부뿐 아니라 검출기 초기화 성공도 확인한다."""
    try:
        return warmup()
    except Exception:
        logger.warning("얼굴 검출기 초기화 실패", exc_info=True)
        return False



# 회전해서 찾은 얼굴로 인정할 최소 면적(사진 대비). 2026-09-23 실측: 테스트 클로즈업 600장을
# 90°/270° 돌렸을 때 잡힌 가짜 얼굴은 1장·면적 0.2%, 옆으로 누운 실제 셀카의 얼굴은 4.5~16%였다.
ROTATED_FACE_MIN_AREA = 0.01
_ROTATION_PROBE_PX = 800


def _is_upright(lm) -> bool:
    """두 눈이 가로로 놓이고 입이 눈보다 아래에 있는가(머리가 위를 향한 얼굴)."""
    (ex0, ey0), (ex1, ey1) = lm[0], lm[1]
    mouth_y = (float(lm[3][1]) + float(lm[4][1])) / 2
    return abs(float(ex1 - ex0)) > abs(float(ey1 - ey0)) and mouth_y > (float(ey0) + float(ey1)) / 2


def rotation_candidates(img: Image.Image) -> list[int]:
    """이 방향으로는 얼굴을 못 찾았을 때, 얼굴이 나오는 회전 각도(90·270·180) 후보를 확신도 순으로.

    EXIF 방향 정보 없이 옆으로 누운 사진(메신저 전달·스크린샷 등)은 얼굴을 못 찾아 클로즈업 경로로
    가고, 사진 전체의 선명도로 '흔들렸어요'라는 틀린 이유가 나갔다(2026-09-23 실사용 테스트).

    후보가 여럿일 수 있다: MTCNN은 거꾸로 뒤집힌 얼굴도 0.99로 잡고 눈 위치를 똑바른 얼굴처럼
    돌려준다(실제로는 입가를 가리킨다). 어느 쪽이 맞는지는 호출자가 눈 크롭으로 가린다.
    없으면 빈 목록 — 호출자는 원래대로 클로즈업 경로를 쓴다.
    """
    mtcnn = _get_mtcnn()
    if mtcnn is None:
        return []
    small = img.copy()
    small.thumbnail((_ROTATION_PROBE_PX, _ROTATION_PROBE_PX))
    found = []
    for angle in (90, 270, 180):
        probe = small.rotate(angle, expand=True)
        try:
            boxes, probs, landmarks = mtcnn.detect(probe, landmarks=True)
        except Exception:
            logger.warning("회전 얼굴 재검출 실패(%d°)", angle, exc_info=True)
            return []
        if boxes is None or landmarks is None:
            continue
        area = probe.size[0] * probe.size[1]
        best = max((float(p) for b, p, lm in zip(boxes, probs, landmarks)
                    if p >= settings.face_prob_threshold and _is_upright(lm)
                    and max(0.0, float(b[2] - b[0])) * max(0.0, float(b[3] - b[1])) >= area * ROTATED_FACE_MIN_AREA),
                   default=None)
        if best is not None:
            found.append((best, angle))
    return [angle for _, angle in sorted(found, reverse=True)]


def extract_eye_crops(img: Image.Image) -> list[Image.Image] | None:
    """얼굴 사진이면 [왼눈, 오른눈] 크롭 반환, 얼굴이 없으면 빈 리스트.

    여러 얼굴이 감지되면 ``None``을 반환해 호출자가 판독을 보류한다.

    빈 리스트 = '얼굴 없음' → 호출자는 원본을 눈 클로즈업으로 처리하면 됨.
    """
    try:
        mtcnn = _get_mtcnn()
        if mtcnn is None:
            raise EyeDetectionError("얼굴 검출기를 사용할 수 없습니다")
        boxes, probs, landmarks = mtcnn.detect(img, landmarks=True)
    except Exception as exc:
        logger.warning("MTCNN 얼굴 검출 실패: %s", type(exc).__name__)
        raise EyeDetectionError("얼굴 검출 실패") from exc

    # 여러 얼굴이 보이면 누구의 눈인지 결정할 수 없으므로 의료 결과를 만들지 않는다.
    # 예전에는 가장 확신도 높은 얼굴 하나를 조용히 골라 다른 사람의 결과가 나갈 수 있었다.
    valid = ([] if boxes is None or landmarks is None else
             [i for i, p in enumerate(probs) if p >= settings.face_prob_threshold])
    if not valid:
        # 같은 잘린 얼굴도 좌우 반전만으로 후보가 완전히 사라질 수 있다.
        # 따라서 후보가 없는 경우도 한 번 재검출한 뒤 클로즈업으로 보낸다.
        try:
            boxes, probs, landmarks = _retry_edge_face(mtcnn, img)
        except Exception as exc:
            raise EyeDetectionError("잘린 얼굴 재검출 실패") from exc
        if boxes is None:
            # 얼굴이라는 근거가 없으면 기존 클로즈업 경로를 보존한다.
            # 전체 얼굴·가림 사진을 모두 차단한다는 보장은 아니다.
            return []
        valid = list(range(len(boxes)))
    valid = _drop_background_faces(boxes, valid)
    if len(valid) > 1:
        logger.info("얼굴 사진에 여러 얼굴이 감지되어 판독을 보류합니다")
        return None
    best = valid[0]
    if not _is_upright(landmarks[best]):
        # 옆으로 눕거나 뒤집힌 얼굴의 눈 크롭은 모델이 본 적 없는 방향이다. 호출자가 사진을
        # 돌려 다시 찾도록(upright_rotation) '얼굴 없음'으로 돌려준다.
        logger.info("얼굴이 옆으로 누웠거나 뒤집혀 있어 이 방향으로는 판독하지 않습니다")
        return []

    # 랜드마크 순서: [왼눈, 오른눈, 코, 입왼쪽, 입오른쪽]
    # 단, 순서를 믿지 않고 사진 기준 x좌표로 좌/우를 확정한다 — 얼굴이 기울어진 사진에서
    # 순서가 뒤집히면 vision.py의 ["left","right"] 라벨(=프론트 '왼쪽/오른쪽 눈')이 바뀐다.
    left_eye, right_eye = sorted(
        (landmarks[best][0], landmarks[best][1]), key=lambda p: float(p[0]))
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
