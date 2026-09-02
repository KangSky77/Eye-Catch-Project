"""재학습(v6) 전후 비교 — 익상편 오분류율과 부작용을 함께 잰다.

익상편만 좋아지고 백내장을 놓치면 실패다. 그래서 세 가지를 한 번에 잰다.
  1) 익상편 오분류율   — 정상으로 편입한 익상편 사진을 백내장이라 하는 비율
  2) 백내장 민감도     — v5 기준 98.9%. 여기가 떨어지면 재학습은 실패다
  3) 밝은 홍채 오탐    — v5 기준 18.2%. 같은 계열 약점이 되살아났는지 확인

사용:
    python scripts/eval_pterygium.py                     # 현재 배포 가중치로 측정
    python scripts/eval_pterygium.py --weights other.pth # 특정 가중치로 측정
"""
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")   # Windows cp949 콘솔에서도 안전하게

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

import argparse
import random
from collections import Counter

from PIL import Image

from app.core.config import settings
from app.services import vision, eye_validator

NORMAL = Path("dataset/0_normal")
CATARACT = Path("dataset/1_cataract")


def run(paths, label):
    """판정 코드 분포를 센다."""
    c = Counter()
    for p in paths:
        try:
            c[vision.predict_cataract(Image.open(p).convert("RGB"))["result_code"]] += 1
        except Exception:
            c["error"] += 1
    n = max(1, sum(c.values()))
    print(f"\n[{label}] n={sum(c.values())}")
    for k, v in c.most_common():
        print(f"    {k:<12} {v:5d}장 ({v / n * 100:5.1f}%)")
    return c, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", help="측정할 .pth (기본: .env의 MODEL_PATH)")
    ap.add_argument("--sample", type=int, default=250, help="클래스별 표본 수")
    args = ap.parse_args()

    if args.weights:
        settings.model_path = args.weights
    if not vision.load_trained_weights():
        raise SystemExit(f"❌ 가중치 로드 실패: {settings.model_path}")
    if not eye_validator.warmup():
        raise SystemExit("❌ 눈 검증기 로드 실패 (최초 1회 인터넷 필요)")
    print(f"측정 대상 가중치: {settings.model_path}")

    random.seed(11)

    def pick(folder, pattern, n):
        fs = [folder / f for f in os.listdir(folder) if pattern(f)]
        random.shuffle(fs)
        return fs[:n]

    # 1) 익상편 — 백내장이라 하면 오분류
    pt = pick(NORMAL, lambda f: f.startswith("pterygium_"), args.sample)
    c, n = run(pt, "익상편 (정상으로 편입된 사진)")
    bad = c["risk"] + c["borderline"]
    print(f"    >>> 백내장 오분류: {bad}/{n} = {bad / n * 100:.1f}%   (재학습 전 88.0%)")

    # 2) 백내장 민감도 — 여기가 떨어지면 실패
    cat = pick(CATARACT, lambda f: True, args.sample)
    c, n = run(cat, "백내장")
    hit = c["risk"] + c["borderline"]
    print(f"    >>> 검진 안내율(민감도 근사): {hit}/{n} = {hit / n * 100:.1f}%   (v5 test 98.9%)")

    # 3) 밝은 홍채 — 같은 계열 약점이 되살아났는지
    bi = pick(NORMAL, lambda f: f.startswith("brightiris"), args.sample)
    if bi:
        c, n = run(bi, "밝은 홍채 정상 눈")
        fp = c["risk"] + c["borderline"]
        print(f"    >>> 오탐: {fp}/{n} = {fp / n * 100:.1f}%   (v5 held-out 18.2%)")

    print("\n※ dataset 안에서의 수치다. 실제 폰 사진은 scripts/validate_real_photos.py 로 따로 확인할 것.")


if __name__ == "__main__":
    main()
