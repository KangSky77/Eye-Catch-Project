import io
import logging
import os
import torch
from PIL import Image, ImageOps
from fastapi import UploadFile, HTTPException
from torchvision import transforms
from app.models.cataract_model import build_model
from app.core.config import settings
from app.services import eye_detector
from app.services import eye_validator

logger = logging.getLogger(__name__)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = build_model().to(device)

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

def load_trained_weights() -> bool:
    """학습된 가중치를 로드합니다. 파일이 없거나 호환되지 않으면
    경고만 출력하고 서버는 계속 기동합니다 (train_ai.py로 먼저 학습 필요)."""
    global weights_loaded
    if not os.path.exists(settings.model_path):
        logger.warning(f"⚠️  가중치 파일이 없습니다: {settings.model_path} — train_ai.py로 먼저 학습하세요.")
        model.eval()
        weights_loaded = False
        return False
    try:
        model.load_state_dict(torch.load(settings.model_path, map_location=device, weights_only=True))
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

    contents = await file.read()

    # 파일 크기 제한 (10MB)
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="파일 크기는 10MB 이하여야 합니다.")

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

def _predict_single(img: Image.Image) -> float:
    """이미지 1장의 백내장 확률(%)을 반환.

    TTA(좌우반전 평균): 원본과 거울상 두 뷰의 예측을 평균한다. 눈은 좌우 대칭이고
    학습 때도 RandomHorizontalFlip을 썼으므로 분포상 안전한 앙상블.
    자체 재평가(그룹 분할 val/test) 기준 val FP 11→9, test FN 7→6으로 손해 없는
    소폭 개선이었고, 비용은 배치 2장 추론이라 무시할 수준."""
    x = preprocess(img)
    batch = torch.stack([x, torch.flip(x, dims=[2])]).to(device)   # dims=[2] = W(좌우)축
    with torch.no_grad():
        probs = torch.nn.functional.softmax(model(batch), dim=1)[:, 1]
    return probs.mean().item() * 100


def _classify(prob: float):
    """확률(%) → (언어중립 코드, 한국어 기본 문구). 임계값 일관 적용."""
    if prob >= settings.risk_threshold:
        return "risk", "백내장 위험 단계 (정밀 검사 권장)"
    return "normal", "특이 소견 없음 (정상)"


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
            return {
                "probability": 0.0,
                "result": "눈 사진이 아닌 것 같습니다",
                "result_code": "invalid",      # 프론트가 '눈 사진을 올려주세요'로 안내
                "mode": mode,
                "eyes_detected": 0,
                "eye_probs": [],
                "eyes": [],
                "asymmetric": False,
                "eye_score": round(score, 3),
            }

    targets = eye_crops if eye_crops else [img]

    eye_probs = [_predict_single(t) for t in targets]
    # 의료 스크리닝: 두 눈 중 위험도가 높은 쪽 기준으로 판정
    cat_p = max(eye_probs)

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
    }
