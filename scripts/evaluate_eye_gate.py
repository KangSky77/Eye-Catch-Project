"""눈/비-눈 게이트 임계값 감사 — 내부 표본 기준(외부 검증 아님).

실행:  python scripts/evaluate_eye_gate.py --sample 300
모델 파일은 건드리지 않는다. 두 클래스는 시드 20260905로 각각 표본추출한다.

왜 이 스크립트가 있나
---------------------
게이트가 도서관 사진(static/assets/vision-scene.jpg)을 눈으로 받아들여 '정상' 판정을
내보낸 적이 있다. 그때 임계값을 그 사진 점수(0.390) 바로 위인 0.40으로 올렸는데,
**같은 사진을 크롭만 바꾸면 0.61로 여전히 통과했다.** 사진 한 장에 맞춘 값은
'비-눈'이라는 부류를 막지 못한다.

그래서 음성 표본을 한 장이 아니라 무리로 만든다:
  · 실제 사진(도서관·안저)을 여러 배율/위치로 잘라낸 크롭 — 현실적인 오입력에 가장 가깝다
  · 합성 이미지(단색·노이즈·문서·블롭·그라데이션) — scripts/probe_eye_gate.py와 동일
음성 표본을 늘리면 '임계값을 올려도 못 막는 것이 남는지'가 눈에 보인다.

출력은 임계값별 트레이드오프 표다. 눈을 몇 % 잃고 비-눈을 몇 % 막는지 함께 본다 —
한쪽만 보고 정하면 안 된다(백내장 유지율만 보고 0.40을 골랐을 때 정상 눈 거부가
1.3%에서 3.3%로 늘어난 것이 보고되지 않았다).
"""
import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageOps
from app.services import eye_validator, eye_detector

THRESHOLDS = (0.20682776, 0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8)


def _load(path: Path) -> Image.Image:
    with Image.open(path) as src:
        return ImageOps.exif_transpose(src).convert("RGB")


def build_negatives() -> dict[str, Image.Image]:
    """비-눈 표본. 실제 사진 크롭이 핵심이고, 합성은 보조다."""
    negatives: dict[str, Image.Image] = {}
    assets = ROOT / "static" / "assets"

    # 실제 사진을 여러 격자/배율로 잘라 '현실적인 오입력'을 만든다.
    # 사용자가 엉뚱한 사진을 올릴 때 그것이 늘 원본 프레이밍이라는 보장이 없다.
    for name in ("vision-scene.jpg", "diseases/amd-fundus.jpg",
                 "diseases/diabetic-retinopathy-fundus.jpg"):
        path = assets / name
        if not path.exists():
            continue
        img = _load(path)
        negatives[f"{name}:full"] = img
        w, h = img.size
        for grid in (2, 3):
            for gy in range(grid):
                for gx in range(grid):
                    box = (gx * w // grid, gy * h // grid,
                           (gx + 1) * w // grid, (gy + 1) * h // grid)
                    negatives[f"{name}:g{grid}-{gy}{gx}"] = img.crop(box)
        for zoom in (0.5, 0.7):
            cw, ch = int(w * zoom), int(h * zoom)
            negatives[f"{name}:center{zoom}"] = img.crop(
                ((w - cw) // 2, (h - ch) // 2, (w - cw) // 2 + cw, (h - ch) // 2 + ch))

    # 합성 표본 — probe_eye_gate.py와 같은 것을 재사용한다(계열별 회귀 표본)
    import importlib.util
    spec = importlib.util.spec_from_file_location("probe", ROOT / "scripts" / "probe_eye_gate.py")
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    for i, (img, kind) in enumerate(probe.synthetic_non_eye(random.Random(20260905))):
        negatives[f"synthetic:{kind}-{i}"] = img
    return negatives


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=300, help="클래스당 표본 수")
    args = parser.parse_args()
    if args.sample < 1:
        parser.error("--sample must be positive")
    if not eye_validator.warmup() or not eye_validator.gate_available():
        raise SystemExit("Eye gate unavailable")

    rng = random.Random(20260905)
    scores: dict[str, list[float]] = {}
    for category in ("0_normal", "1_cataract"):
        paths = sorted(p for p in (ROOT / "dataset" / category).rglob("*")
                       if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"})
        if not paths:
            raise SystemExit(f"Missing dataset: {category}")
        paths = rng.sample(paths, min(args.sample, len(paths)))
        scores[category] = [eye_validator._gate_prob(_load(p)) for p in paths]

    negatives = build_negatives()
    neg_scores = {k: eye_validator._gate_prob(v) for k, v in negatives.items()}

    # 얼굴 사진에서 잘라낸 눈 크롭은 반드시 통과해야 한다(얼굴 모드의 정상 경로)
    face_eyes = []
    face_path = ROOT / "static" / "assets" / "examples" / "face-good.jpg"
    if face_path.exists():
        face_eyes = [eye_validator._gate_prob(c)
                     for c in eye_detector.extract_eye_crops(_load(face_path))]

    n_neg = len(neg_scores)
    print(f"눈 표본: 정상 {len(scores['0_normal'])}장 / 백내장 {len(scores['1_cataract'])}장")
    print(f"비-눈 표본: {n_neg}개 (실제 사진 크롭 + 합성)")
    print(f"얼굴 사진의 눈 크롭 점수: {[round(s, 3) for s in face_eyes]}  ← 반드시 통과해야 함")
    print()
    print(f"{'임계값':>10} | {'정상 눈 거부':>12} | {'백내장 눈 거부':>14} | {'비-눈 통과':>12}")
    print("-" * 62)
    for t in THRESHOLDS:
        nrm = sum(s < t for s in scores["0_normal"])
        cat = sum(s < t for s in scores["1_cataract"])
        leak = sum(s >= t for s in neg_scores.values())
        print(f"{t:>10.3f} | {nrm:>4}/{len(scores['0_normal'])} ({nrm/len(scores['0_normal']):>5.1%})"
              f" | {cat:>4}/{len(scores['1_cataract'])} ({cat/len(scores['1_cataract']):>5.1%})"
              f" | {leak:>3}/{n_neg} ({leak/n_neg:>5.1%})")

    print()
    print("비-눈인데 점수가 높은 것 상위 10개 (이 값들이 임계값의 하한을 정한다):")
    for k, s in sorted(neg_scores.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {s:.4f}  {k}")

    print()
    print(json.dumps({"seed": 20260905,
                      "note": "Internal sample; may contain gate training images.",
                      "negatives": n_neg,
                      "max_negative": max(neg_scores.values()),
                      "face_eye_scores": face_eyes}, indent=2))


if __name__ == "__main__":
    main()
