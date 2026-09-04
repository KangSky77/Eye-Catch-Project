"""촬영 구도·조명 변화에 대한 배포 파이프라인 스트레스 테스트.

동일한 눈 사진을 위/아래로 이동하거나 밝기를 바꿔, 원본 대비 눈 게이트와
백내장 혼탁 특징 판정이 얼마나 바뀌는지 측정한다. 실제 시선 변화 임상시험을
대체하지 않으며, 카메라 가이드 필요성을 판단하기 위한 재현 가능한 1차 검사다.

사용법:
    python scripts/eval_capture_robustness.py --sample 40
"""
import argparse
import random
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps, ImageStat

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services import eye_validator, vision


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
RETAKE_CODES = {"blurry", "invalid", "hold", "error"}


def load_rgb(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image.convert("RGB"))


def translate(image: Image.Image, dx_ratio: float = 0, dy_ratio: float = 0) -> Image.Image:
    """사진 구도가 프레임 안에서 이동한 상황. 빈 가장자리는 평균색으로 채운다."""
    dx, dy = round(image.width * dx_ratio), round(image.height * dy_ratio)
    fill = tuple(round(v) for v in ImageStat.Stat(image.resize((1, 1))).mean[:3])
    return image.transform(
        image.size,
        Image.Transform.AFFINE,
        (1, 0, -dx, 0, 1, -dy),
        resample=Image.Resampling.BILINEAR,
        fillcolor=fill,
    )


TRANSFORMS = {
    "original": lambda image: image,
    "up_10pct": lambda image: translate(image, dy_ratio=-0.10),
    "down_10pct": lambda image: translate(image, dy_ratio=0.10),
    "up_20pct": lambda image: translate(image, dy_ratio=-0.20),
    "down_20pct": lambda image: translate(image, dy_ratio=0.20),
    "brightness_055": lambda image: ImageEnhance.Brightness(image).enhance(0.55),
    "brightness_075": lambda image: ImageEnhance.Brightness(image).enhance(0.75),
    "brightness_135": lambda image: ImageEnhance.Brightness(image).enhance(1.35),
    "brightness_170": lambda image: ImageEnhance.Brightness(image).enhance(1.70),
}


def run_eye_pipeline(image: Image.Image) -> tuple[str, float]:
    """얼굴 검출 뒤의 한쪽 눈 클로즈업 배포 경로와 같은 순서로 판정한다."""
    if vision._sharpness(image) < vision.BLUR_MIN_SHARPNESS:
        return "blurry", 0.0
    is_eye, _ = eye_validator.check_eye(image)
    if is_eye is None:
        return "error", 0.0
    if not is_eye:
        return "invalid", 0.0
    probability = vision._predict_single(image)
    code, _ = vision._classify(probability)
    if vision._glare_fraction(image) >= vision.GLARE_MAX_FRACTION and code != "normal":
        return "hold", probability
    return code, probability


def summarize(rows: list[dict], label: str, variant: str) -> dict:
    selected = [row for row in rows if row["label"] == label and row["variant"] == variant]
    counts = Counter(row["code"] for row in selected)
    changed = sum(row["code"] != row["base_code"] for row in selected)
    retake = sum(row["code"] in RETAKE_CODES for row in selected)
    mean_delta = sum(abs(row["prob"] - row["base_prob"]) for row in selected) / max(len(selected), 1)
    if label == "normal":
        harmful = sum(row["base_code"] not in {"risk", "borderline"}
                      and row["code"] in {"risk", "borderline"} for row in selected)
    else:
        harmful = sum(row["base_code"] in {"risk", "borderline"}
                      and row["code"] == "normal" for row in selected)
    return {
        "n": len(selected), "changed": changed, "retake": retake,
        "harmful": harmful, "mean_delta": mean_delta, "counts": counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=40, help="클래스별 사진 수")
    parser.add_argument("--seed", type=int, default=20260904)
    args = parser.parse_args()
    if args.sample <= 0:
        raise SystemExit("--sample은 1 이상이어야 합니다.")

    if not vision.load_trained_weights():
        raise SystemExit("배포 가중치 로드 실패")
    if not eye_validator.warmup():
        raise SystemExit("눈 검증기 로드 실패")

    rng = random.Random(args.seed)
    classes = {"normal": REPO_ROOT / "dataset" / "0_normal",
               "cataract": REPO_ROOT / "dataset" / "1_cataract"}
    chosen = {}
    for label, folder in classes.items():
        paths = [path for path in folder.rglob("*")
                 if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES]
        rng.shuffle(paths)
        chosen[label] = paths[:args.sample]

    rows = []
    for label, paths in chosen.items():
        for index, path in enumerate(paths, 1):
            try:
                original = load_rgb(path)
                base_code, base_prob = run_eye_pipeline(original)
                for variant, transform in TRANSFORMS.items():
                    code, probability = ((base_code, base_prob) if variant == "original"
                                         else run_eye_pipeline(transform(original)))
                    rows.append({"label": label, "variant": variant, "code": code,
                                 "prob": probability, "base_code": base_code,
                                 "base_prob": base_prob})
            except Exception as exc:
                print(f"WARN {label} {path.name}: {type(exc).__name__}")
            print(f"\r{label}: {index}/{len(paths)}", end="", flush=True)
        print()

    print("\nvariant,label,n,code_changed,retake_or_reject,harmful_flip,mean_abs_score_delta,codes")
    for variant in TRANSFORMS:
        for label in classes:
            result = summarize(rows, label, variant)
            codes = ";".join(f"{key}:{value}" for key, value in sorted(result["counts"].items()))
            print(f"{variant},{label},{result['n']},{result['changed']},{result['retake']},"
                  f"{result['harmful']},{result['mean_delta']:.2f},{codes}")

    print("\n주의: 데이터셋 내부 사진의 동일-image 변형 실험이므로 임상 정확도나 실제 시선 변화 성능이 아닙니다.")
    print("harmful_flip: 정상은 risk/borderline으로 상승, 백내장은 원래 검진 안내였으나 normal로 하락한 수입니다.")


if __name__ == "__main__":
    main()
