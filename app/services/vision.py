import io
import hashlib
import json
import logging

import numpy as np
import torch
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageOps
from torchvision import transforms

from app.core.config import settings
from app.models.cataract_model import build_model
from app.services import eye_detector, eye_validator

logger = logging.getLogger(__name__)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = build_model(backbone=settings.model_backbone).to(device)

MAX_FILE_SIZE = settings.max_upload_size_bytes
# 디코딩 후 픽셀 수 상한 — 작은 압축파일이 거대한 비트맵으로 풀리는 '압축 폭탄' 방어
MAX_IMAGE_PIXELS = 24_000_000   # 약 24MP (예: 6000x4000). 일반 폰 사진은 충분히 통과
# PIL 자체 안전장치도 보수적으로 설정 (이 값 초과 시 디코딩 단계에서 거부)
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

# 가중치 로드 성공 여부 — False면 학습 안 된 모델이므로 예측을 거부해야 함
weights_loaded = False

# 추론 전처리 (요청마다 재생성하지 않도록 모듈 레벨에 1회 생성)
# train_ai.py의 eval_tf와 반드시 동일해야 함
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def _weights_match_metadata(weights_path, metadata_path) -> bool:
    """기록된 SHA-256과 실제 가중치가 다르면 잘못된 모델 서빙을 막는다."""
    if not metadata_path.exists():
        logger.error("⚠️  모델 메타데이터가 없어 가중치 출처를 검증할 수 없습니다: %s", metadata_path)
        return False
    try:
        with open(metadata_path, encoding="utf-8") as f:
            expected = json.load(f).get("weights_sha256")
        if not expected:
            logger.error("⚠️  모델 메타데이터에 weights_sha256이 없습니다: %s", metadata_path)
            return False
        digest = hashlib.sha256()
        with open(weights_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            logger.error("⚠️  가중치 SHA-256 불일치 — 오래되거나 손상된 모델은 서빙하지 않습니다")
            return False
        return True
    except Exception:
        logger.error("⚠️  모델 메타데이터 검증 실패", exc_info=True)
        return False


def load_trained_weights() -> bool:
    """학습된 가중치를 로드합니다. 파일이 없거나 호환되지 않으면
    경고만 출력하고 서버는 계속 기동합니다 (train_ai.py로 먼저 학습 필요)."""
    global weights_loaded
    model_path = settings.model_file
    if not model_path.exists():
        logger.warning(f"⚠️  가중치 파일이 없습니다: {model_path} — train_ai.py로 먼저 학습하세요.")
        model.eval()
        weights_loaded = False
        return False
    if not _weights_match_metadata(model_path, settings.model_metadata_path):
        model.eval()
        weights_loaded = False
        return False
    try:
        model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
        model.eval()
        weights_loaded = True
        return True
    except Exception:
        logger.error("⚠️  가중치 로드 실패(아키텍처 불일치 가능)", exc_info=True)
        model.eval()
        weights_loaded = False
        return False

async def validate_and_read_image(file: UploadFile) -> Image.Image:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")

    # 파일 크기 제한 — '읽기 전에' 막는다.
    # Starlette가 채워주는 file.size를 먼저 보고, 없으면 상한+1바이트만 읽어서 초과를 판정한다.
    # (무인자 read()로 전부 읽은 뒤 검사하면, 거부할 업로드도 일단 통째로 메모리에 올라와
    #  MAX_FILE_SIZE가 사실상 방어 역할을 못 한다.)
    if file.size is not None and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"파일 크기는 {MAX_FILE_SIZE // (1024 * 1024)}MB 이하여야 합니다.")

    contents = await file.read(MAX_FILE_SIZE + 1)
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"파일 크기는 {MAX_FILE_SIZE // (1024 * 1024)}MB 이하여야 합니다.")

    try:
        # 헤더만 먼저 읽어 크기 확인(이 시점엔 전체 픽셀 디코딩 전)
        img = Image.open(io.BytesIO(contents))
        w, h = img.size
    except Image.DecompressionBombError:
        # Pillow가 open/size 단계에서도 폭탄을 던질 수 있음 → 413으로 정확히 분류
        raise HTTPException(status_code=413, detail="이미지 해상도가 너무 큽니다. 더 작은 사진을 올려주세요.")
    except Exception:
        raise HTTPException(status_code=400, detail="유효한 이미지 파일이 아닙니다.")

    # 픽셀 수 상한 검사 — 디코딩으로 메모리 폭주하기 전에 거부
    if w * h > MAX_IMAGE_PIXELS:
        raise HTTPException(
            status_code=413,
            detail=f"이미지 해상도가 너무 큽니다. ({w}x{h}) 더 작은 사진을 올려주세요."
        )

    try:
        # EXIF 회전 정보 반영 + RGB 변환 (여기서 실제 픽셀 디코딩)
        return ImageOps.exif_transpose(img.convert("RGB"))
    except Image.DecompressionBombError:
        raise HTTPException(status_code=413, detail="이미지 해상도가 너무 큽니다. 더 작은 사진을 올려주세요.")
    except Exception:
        raise HTTPException(status_code=400, detail="유효한 이미지 파일이 아닙니다.")

# 흔들림(초점 흐림) 판정 기준 — 라플라시안 분산을 대비로 정규화한 값.
# 실측(눈 사진 141장, 사진 크기에 비례한 모션 블러, 2026-08-26):
#     흔들림 없음  선명도 중앙 0.175 | 판정 변화 0/141
#     0.5%        0.112 | 3/141
#     1.0%        0.065 | 3/141
#     2.0%        0.033 | 7/141
#     3.5%        0.019 | 4/141
# 임계 0.030에서 심한 흔들림(3.5%)의 74%를 잡고 멀쩡한 사진 거부는 2.1%.
#
# ※ 솔직한 한계: 모델 자체는 흔들림에 꽤 강해서(3.5%에서도 판정 변화 2.8%),
#   이 게이트는 '정확도를 지키는 장치'라기보다 '판독 불가한 입력을 되돌려보내는
#   입력 위생 장치'다. 가벼운 흔들림은 잡지 못한다.
BLUR_MIN_SHARPNESS = 0.030


def _sharpness(img: Image.Image) -> float:
    """라플라시안 분산을 대비(표준편차)로 나눈 선명도. 클수록 선명하다.

    128x128 그레이스케일로 맞춰 크기 영향을 없애고, 표준편차로 나눠
    '어두운 사진이라 값이 작은 것'과 '흔들려서 작은 것'을 구분한다.
    """
    g = np.asarray(img.convert("L").resize((128, 128)), dtype=np.float32)
    p = np.pad(g, 1, mode="edge")
    k = ((0, 1, 0), (1, -4, 1), (0, 1, 0))
    lap = sum(k[i][j] * p[i:i + 128, j:j + 128] for i in range(3) for j in range(3))
    sd = float(g.std())
    if sd < 1e-3:                      # 완전 단색 — 눈 사진이 아니다
        return 0.0
    return float(lap.var() / (sd * sd))

# 플래시 반사 판정 기준 — 근거는 _glare_fraction() 독스트링과 아래 표.
# 합성 반사점 크기별 실측(정상 눈 60장, 배포 모델 v5, 2026-08-24):
#     반경  4%: 모델 오탐  0.0%  |  순백비율 0.56%
#     반경  6%: 모델 오탐  5.0%  |  순백비율 1.27%
#     반경  8%: 모델 오탐 15.0%  |  순백비율 2.25%   <- 여기부터 문제
#     반경 10%: 모델 오탐 33.3%  |  순백비율 3.54%
#     반경 14%: 모델 오탐 70.0%  |  순백비율 6.85%
# 임계 2.0%는 '오탐 10% 이상을 만드는 크기'를 모두 잡으면서
# 백내장 오거부 1.2% / 정상 오거부 1.7%로 억제되는 지점이다.
# 오거부는 '판정 실패'가 아니라 '다시 찍어달라'는 안내이므로, 오탐보다 비용이 훨씬 낮다.
GLARE_SATURATION_LEVEL = 250   # 세 채널 모두 이 값 이상이면 '순백'
GLARE_MAX_FRACTION = 0.02      # 중앙부의 2%를 넘으면 판독 보류

def _predict_single(img: Image.Image) -> float:
    """이미지 1장의 백내장 확률(%)을 반환.

    TTA는 settings.use_tta(기본 OFF). v6 가중치 재측정(2026-09-02, test 2,526장, 라벨 정정 전):
        TTA 없음 FN 7 / FP 2  |  TTA 적용 FN 9 / FP 3  → 이득이 없어 끈다. 아래 표는 v5 시절 근거.

    TTA(좌우반전 평균): 원본과 거울상 두 뷰의 예측을 평균한다. 눈은 좌우 대칭이고
    학습 때도 RandomHorizontalFlip을 썼으므로 분포상 안전한 앙상블.
    배포 모델(efficientnet_b0 v5) 실측 — test 2,600장, 2026-08-20:
        지표                      TTA 없음   TTA 적용
        FN(50% 기준)                  1         3
        정상으로 안내된 백내장         0         0    ← 사용자 관점의 실제 놓침
        오탐(FP)                     12        12
        정상인데 경계로 안내           4         2
    FN만 보면 TTA가 2건 손해지만, 이 앱은 3단계 판정을 쓰므로 '놓쳤다'의 기준은
    FN이 아니라 '경계에도 못 걸려 정상으로 안내된 백내장'이다. 그 수치는 양쪽 다 0 —
    늘어난 FN 2건을 경계 구간이 전부 흡수한다. 게다가 정상인을 경계로 보내는 부담은
    TTA 쪽이 4→2로 더 적다. 즉 사용자가 받는 안내 기준으로는 동률이거나 TTA가 미세 우위.

    ※ 과거 주석은 "실사진 변화에 대한 보험"이라 적었으나 측정된 근거가 아니었고,
      '무득실'이라는 수치도 v4 시절 것이라 배포 모델(v5)과 맞지 않았다. 위 표로 교체함.
      백본·데이터를 바꾸면 반드시 재측정할 것(resnet18 v4는 TTA가 FN 7→10으로 해로웠다)."""
    x = preprocess(img)
    views = [x, torch.flip(x, dims=[2])] if settings.use_tta else [x]   # dims=[2] = W(좌우)축
    batch = torch.stack(views).to(device)
    with torch.no_grad():
        probs = torch.nn.functional.softmax(model(batch), dim=1)[:, 1]
    return probs.mean().item() * 100


def _glare_fraction(img: Image.Image) -> float:
    """눈 크롭 중앙부에서 '완전포화된 흰 픽셀'이 차지하는 비율.

    플래시가 각막에 맺히는 반사점(캐치라이트)은 세 채널이 모두 255에 붙는
    작고 단단한 순백 영역이다. 반면 백내장의 수정체 혼탁은 회백색이라
    포화까지 가지 않는다 — 이 차이로 둘을 가른다.

    실측(2026-08-24, 배포 모델 v5):
        순백비율 중앙값 — 정상 0.00% / 백내장 0.01% / 플래시 반사 3.54%
    """
    w, h = img.size
    if w < 8 or h < 8:
        return 0.0
    # 동공·홍채가 있는 중앙부만 본다(눈꺼풀·속눈썹·피부 하이라이트 제외)
    cw, ch = int(w * 0.6), int(h * 0.6)
    crop = img.convert("RGB").crop(((w - cw) // 2, (h - ch) // 2,
                                    (w - cw) // 2 + cw, (h - ch) // 2 + ch))
    a = np.asarray(crop.resize((96, 96)), dtype=np.uint8)
    return float((a.min(axis=2) >= GLARE_SATURATION_LEVEL).mean())

def _classify(prob: float):
    """확률(%) → (언어중립 코드, 한국어 기본 문구). 임계값 일관 적용.

    3단계 판정: risk(≥risk_threshold) / borderline(경계 구간) / normal.
    경계 구간은 '정상'으로 안심시키기엔 애매한 확률대(임계값 근거는 config.py 주석)를
    재촬영·검진 권장으로 안내해, 문턱 바로 아래에서 놓치는 백내장(FN)을 줄인다."""
    # 4단계: 강한 특징 / 특징 감지 / 판단 어려움 / 뚜렷한 특징 없음.
    # 문구는 '백내장 판별'이 아니라 '사진에서 보이는 진행성 혼탁 특징'으로 범위를 좁힌다 — 외부 테스트에서
    # 옅은 초기 혼탁(AI 생성 얼굴)은 0~4.9점으로 반응하지 않았고, 초기 백내장은 겉사진에 나타나지 않을 수
    # 있다(NEI). '정상'이라 쓰면 눈 전체가 정상이라는 뜻으로 읽히므로 쓰지 않는다 (2026-09-02).
    if prob >= settings.risk_threshold:
        return "risk", "강한 혼탁 특징 감지 (안과 정밀 검사 권장)"
    if prob >= settings.borderline_threshold:
        return "borderline", "혼탁 특징 감지 (재촬영 후 재검사 또는 안과 검진 권장)"
    if prob >= settings.uncertain_threshold:
        return "uncertain", "사진만으로 판단이 어렵습니다 (약한 혼탁 특징 신호)"
    return "normal", "뚜렷한 진행성 혼탁 특징이 감지되지 않았습니다 (초기 백내장은 사진으로 확인이 어렵습니다)"


def _empty_result(code: str, message: str, mode: str, eyes_detected: int, **details) -> dict:
    """판정을 내리지 않는 품질 실패 응답의 공통 필드를 만든다."""
    return {
        "probability": 0.0,
        "result": message,
        "result_code": code,
        "mode": mode,
        "eyes_detected": eyes_detected,
        "eye_probs": [],
        "eyes": [],
        "asymmetric": False,
        **details,
    }


def predict_cataract(img: Image.Image):
    # 학습된 가중치 없이 예측하면 무작위 결과가 나가므로 명시적으로 거부
    if not weights_loaded:
        raise HTTPException(
            status_code=503,
            detail="AI 모델이 준비되지 않았습니다. 관리자에게 문의하세요. (가중치 미로드)"
        )

    # 얼굴 사진이면 눈 부위만 크롭해서 분석 (모델이 눈 클로즈업으로 학습됐기 때문)
    # 얼굴이 안 잡히면 원본을 눈 클로즈업으로 간주
    eye_crops = eye_detector.extract_eye_crops(img)
    mode = "face" if eye_crops else "eye"

    targets = eye_crops if eye_crops else [img]

    # [흔들림 게이트] 초점이 나간 사진은 사람도 판독할 수 없다.
    # 반사 게이트보다 먼저 본다 — 흔들려서 뿌연 것을 '반사'라고 안내하면 엉뚱한 재촬영을 시킨다.
    sharp = max((_sharpness(t) for t in targets), default=0.0)
    if sharp < BLUR_MIN_SHARPNESS:
        logger.info("판독 보류 — 흔들림/초점 흐림 (선명도 %.4f)", sharp)
        return _empty_result(
            "blurry", "판독 보류 (사진이 흔들렸습니다)", mode, len(eye_crops),
            sharpness=round(sharp, 4),
        )

    # 흔들림 게이트가 먼저다: 흐린 눈 사진을 눈 게이트에 먼저 넣으면 '눈이 아님/가려짐'으로 잘못 안내된다
    # (실측 2026-09-02: 흔들린 얼굴 사진의 눈 크롭 게이트 점수 0.106 → eyes_hidden). 흐림은 흐림이라고 말한다.

    # [검증] 얼굴(MTCNN)이 안 잡힌 'eye 모드'는 눈 클로즈업인지 확신할 수 없으므로,
    # 임베딩 OOD 게이트로 '진짜 눈 사진인가'를 확인. 비-눈이면 의료 결과 대신 거부.
    # (얼굴 모드는 MTCNN가 눈 위치를 이미 확인했으므로 생략)
    if mode == "eye":
        is_eye, score = eye_validator.check_eye(img)
        if is_eye is None:
            # 검증기 사용 불가 → fail-CLOSED: 검증 없이 의료 결과를 내지 않고 명시적으로 차단
            raise HTTPException(
                status_code=503,
                detail="눈 이미지 검증기를 사용할 수 없습니다. 잠시 후 다시 시도해주세요."
            )
        if not is_eye:
            return _empty_result(
                "invalid", "눈 사진이 아닌 것 같습니다", mode, 0,
                eye_score=round(score, 3),
            )

    # [검증·얼굴 모드] MTCNN은 얼굴 '기하'에서 눈 위치를 추정할 뿐, 그 자리에 눈이 보이는지는 모른다.
    # 눈을 감았거나 선글라스·안대로 가린 얼굴도 눈 좌표를 돌려주므로, 피부·검정·흰색 조각이 모델에
    # 들어가 '정상 0.0%'가 자신 있게 나갔다(2026-09-02 실측). 크롭마다 눈/비-눈 게이트를 통과시킨다.
    if mode == "face":
        checks = [eye_validator.check_eye(c) for c in eye_crops]
        if any(ok is None for ok, _ in checks):
            raise HTTPException(
                status_code=503,
                detail="눈 이미지 검증기를 사용할 수 없습니다. 잠시 후 다시 시도해주세요."
            )
        if not all(ok for ok, _ in checks):
            return _empty_result(
                "eyes_hidden", "눈이 감겨 있거나 가려진 것 같습니다 (재촬영 필요)",
                mode, len(eye_crops), eye_score=round(min(s for _, s in checks), 3),
            )

    # [반사 게이트] 플래시 반사가 눈동자를 덮으면 모델이 그것을 수정체 혼탁으로 읽는다.
    # 실측: 정상 눈에 반사점을 합성하니 최대 70%가 '위험'으로 뒤집혔다(위 상수 주석 표).
    # 반사는 판정을 '위험' 쪽으로만 밀므로, 반사가 있어도 모델이 '정상'이라 하면 그 결과는 믿을 수 있다.
    # 반면 '위험/경계'는 반사 때문일 수 있어 판정을 내리지 않고 재촬영을 요청한다.
    # (예전엔 반사가 있으면 무조건 보류했는데, 데이터셋 백내장 사진의 3.0%(54/1,823)·정상 0.1%가 걸렸다.
    #  이 규칙으로 정상 눈의 불필요한 재촬영은 사라지고, 반사 낀 진짜 백내장은 여전히 재촬영을 요청한다 —
    #  놓치는 것이 아니라 플래시를 끄고 다시 찍으면 판정된다. 2026-09-02)
    glare = max((_glare_fraction(t) for t in targets), default=0.0)

    eye_probs = [_predict_single(t) for t in targets]
    # 의료 스크리닝: 두 눈 중 위험도가 높은 쪽 기준으로 판정
    cat_p = max(eye_probs)

    if glare >= GLARE_MAX_FRACTION and _classify(cat_p)[0] != "normal":
        logger.info("판독 보류 — 조명 반사 감지 (순백비율 %.3f, 모델 %.1f%%)", glare, cat_p)
        return _empty_result(
            "hold", "판독 보류 (강한 조명 반사 감지됨)", mode, len(eye_crops),
            glare=round(glare, 4),
        )

    # result_code: 프론트엔드에서 언어별로 번역할 수 있도록 언어 중립적 코드 제공
    # 참고: 과거 'cat_p>=99 → 조명 반사 보류' 규칙은 약한 모델의 오탐을 막으려던
    #       임시방편이었음. 현재는 높은 확률을 별도 보류로 뒤집지 않고, 동일 임계값으로
    #       일관되게 판정한다. 단, 공개 성능 수치는 중복 제거/그룹 분할 재평가 후 갱신해야 한다.
    # 임계값 50%: v2 모델 테스트셋 기준 75%에서는 FN=2(백내장 놓침),
    #             50%에서는 FN=0 / FP 2→3. 스크리닝은 FN 최소화가 우선이라 50% 채택.
    code, res = _classify(cat_p)

    # 눈별 결과: 얼굴 모드(눈 2개)면 [왼쪽, 오른쪽](사진 기준) 라벨, 아니면 단일 눈.
    # 크롭 순서는 eye_detector가 [왼눈, 오른눈]으로 보장.
    if mode == "face" and len(eye_probs) == 2:
        sides = ["left", "right"]
    else:
        sides = ["single"] * len(eye_probs)
    eyes = []
    for side, p in zip(sides, eye_probs):
        eye_code, _ = _classify(p)
        eyes.append({"side": side, "probability": round(p, 1), "code": eye_code})

    # 편측(비대칭) 의심: 얼굴 모드에서 한 눈만 위험 단계인 경우
    risk_count = sum(1 for e in eyes if e["code"] == "risk")
    asymmetric = mode == "face" and len(eyes) == 2 and risk_count == 1

    # 애매한 신호는 눈 클로즈업으로 확인시킨다 — 얼굴 사진의 눈 크롭은 해상도가 낮고, 외부 테스트에서
    # 옅은 혼탁은 얼굴 사진으로 거의 잡히지 않았다. uncertain은 어느 모드든, borderline은 얼굴 모드일 때.
    closeup_suggested = code == "uncertain" or (mode == "face" and code == "borderline")

    # 백내장 확률만 표시 (max 사용 시 정상이어도 높은 숫자 표시되는 혼란 방지)
    return {
        "probability": round(cat_p, 1),
        "result": res,
        "result_code": code,
        "mode": mode,                              # "face"=눈 크롭 분석 / "eye"=원본 그대로
        "eyes_detected": len(eye_crops),           # 얼굴에서 찾은 눈 개수 (0이면 클로즈업 경로)
        "eye_probs": [round(p, 1) for p in eye_probs],
        "eyes": eyes,                              # 눈별 [{side, probability, code}]
        "asymmetric": asymmetric,                  # 편측만 위험이면 True
        "closeup_suggested": closeup_suggested,    # 프론트가 '눈을 한쪽씩 가까이 다시 찍기'를 권함
    }
