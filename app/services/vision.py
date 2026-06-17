import io
import torch
from PIL import Image, ImageOps
from fastapi import UploadFile, HTTPException
from torchvision import transforms
from app.models.cataract_model import build_model
from app.core.config import settings
from app.services import eye_detector

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = build_model().to(device)

MAX_FILE_SIZE = settings.max_upload_size_bytes

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
    import os
    if not os.path.exists(settings.model_path):
        print(f"⚠️  가중치 파일이 없습니다: {settings.model_path} — train_ai.py로 먼저 학습하세요.")
        model.eval()
        weights_loaded = False
        return False
    try:
        model.load_state_dict(torch.load(settings.model_path, map_location=device, weights_only=True))
        model.eval()
        weights_loaded = True
        return True
    except Exception as e:
        print(f"⚠️  가중치 로드 실패(아키텍처 불일치 가능): {e}")
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
        # EXIF 회전 정보 반영해서 이미지 오픈
        return ImageOps.exif_transpose(Image.open(io.BytesIO(contents)).convert("RGB"))
    except Exception:
        raise HTTPException(status_code=400, detail="유효한 이미지 파일이 아닙니다.")

def _predict_single(img: Image.Image) -> float:
    """이미지 1장의 백내장 확률(%)을 반환."""
    input_tensor = preprocess(img).unsqueeze(0).to(device)
    with torch.no_grad():
        output = model(input_tensor)
        probs = torch.nn.functional.softmax(output, dim=1)[0]
    return probs[1].item() * 100


def predict_cataract(img: Image.Image):
    # 학습된 가중치 없이 예측하면 무작위 결과가 나가므로 명시적으로 거부
    if not weights_loaded:
        raise HTTPException(
            status_code=503,
            detail="AI 모델이 준비되지 않았습니다. 관리자에게 문의하세요. (가중치 미로드)"
        )

    # 얼굴 사진이면 눈 부위만 크롭해서 분석 (모델이 눈 클로즈업으로 학습됐기 때문)
    # 얼굴이 안 잡히면 기존처럼 원본을 눈 클로즈업으로 간주
    eye_crops = eye_detector.extract_eye_crops(img)
    mode = "face" if eye_crops else "eye"
    targets = eye_crops if eye_crops else [img]

    eye_probs = [_predict_single(t) for t in targets]
    # 의료 스크리닝: 두 눈 중 위험도가 높은 쪽 기준으로 판정
    cat_p = max(eye_probs)

    # result_code: 프론트엔드에서 언어별로 번역할 수 있도록 언어 중립적 코드 제공
    # 참고: 과거 'cat_p>=99 → 조명 반사 보류' 규칙은 약한 모델의 오탐을 막으려던
    #       임시방편이었음. 전이학습 모델(AUC~0.999)은 잘 보정돼 있어, 높은 확신도는
    #       오히려 정확한 백내장 검출이므로 해당 규칙을 제거함.
    # 임계값 50%: v2 모델 테스트셋 기준 75%에서는 FN=2(백내장 놓침),
    #             50%에서는 FN=0 / FP 2→3. 스크리닝은 FN 최소화가 우선이라 50% 채택.
    if cat_p >= 50.0:
        code = "risk"
        res = "백내장 위험 단계 (정밀 검사 권장)"
    else:
        code = "normal"
        res = "특이 소견 없음 (정상)"

    # 백내장 확률만 표시 (max 사용 시 정상이어도 높은 숫자 표시되는 혼란 방지)
    return {
        "probability": round(cat_p, 1),
        "result": res,
        "result_code": code,
        "mode": mode,                              # "face"=눈 크롭 분석 / "eye"=원본 그대로
        "eyes_detected": len(eye_crops),           # 얼굴에서 찾은 눈 개수 (0이면 클로즈업 경로)
        "eye_probs": [round(p, 1) for p in eye_probs],
    }