"""
얼굴→눈 크롭→백내장 분석 파이프라인 스모크 테스트
사용법:
    .venv\\Scripts\\python.exe test_eye_detect.py <사진경로>
얼굴 사진을 주면 mode=face / eyes_detected=2 가 나와야 하고,
눈 클로즈업을 주면 mode=eye 로 기존 경로가 동작해야 합니다.
"""
import sys
from PIL import Image, ImageOps

from app.services import eye_detector
from app.services.vision import load_trained_weights, predict_cataract

if len(sys.argv) < 2:
    raise SystemExit("사용법: python test_eye_detect.py <사진경로>")

print(f"MTCNN 사용 가능: {eye_detector.is_available()}")
loaded = load_trained_weights()
print(f"모델 가중치 로드: {loaded}")
if not loaded:
    raise SystemExit("❌ 가중치 로드 실패 — .env의 MODEL_PATH 확인")

img = ImageOps.exif_transpose(Image.open(sys.argv[1]).convert("RGB"))
print(f"입력 이미지: {sys.argv[1]} ({img.size[0]}x{img.size[1]})")

result = predict_cataract(img)
print("\n=== 분석 결과 ===")
print(f"모드          : {result['mode']}  (face=얼굴에서 눈 크롭 / eye=원본 그대로)")
print(f"검출된 눈     : {result['eyes_detected']}개")
print(f"눈별 확률(%)  : {result['eye_probs']}")
print(f"최종 판정     : {result['result']} ({result['probability']}%)")
