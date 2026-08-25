"""
얼굴→눈 크롭→백내장 분석 파이프라인 스모크 테스트
사용법:
    .venv\\Scripts\\python.exe smoke_eye_detect.py <사진경로>
얼굴 사진을 주면 mode=face / eyes_detected=2 가 나와야 하고,
눈 클로즈업을 주면 mode=eye 로 기존 경로가 동작해야 합니다.

⚠️ 파일명이 `test_*.py`가 아닌 이유: 이 스크립트는 import 시점에 인자를 읽고
   SystemExit를 던지는 CLI라, pytest가 수집하면 INTERNALERROR로 스위트 전체가
   죽는다(`pytest .` 처럼 경로를 넘겨 실행하는 경우). 자동 테스트는 tests/ 참고.
"""
import os
import sys
from pathlib import Path

# scripts/ 안에서 실행돼도 저장소 루트를 기준으로 동작하게 한다.
# (python scripts/x.py 로 실행하면 sys.path[0]이 scripts/라 app 패키지를 못 찾고,
#  dataset/ 같은 상대경로도 실행 위치에 따라 달라진다)
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

import sys
from PIL import Image, ImageOps

from app.services import eye_detector
from app.services.vision import load_trained_weights, predict_cataract

if len(sys.argv) < 2:
    raise SystemExit("사용법: python smoke_eye_detect.py <사진경로>")

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
