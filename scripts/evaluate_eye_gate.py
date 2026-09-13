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
    """비-눈 표본.

    핵심은 dataset_noneye/split.json의 **홀드아웃 사진** — 게이트 학습에 쓰지 않은 것들이다.
    이것이 있어야 "처음 보는 종류의 사진을 막는가"에 답할 수 있다. 저장소 기본 사진과
    합성 이미지는 학습에도 쓰이므로 참고용으로만 함께 잰다(계열이 이름으로 구분된다).
    """
    negatives: dict[str, Image.Image] = {}

    # (1) 학습에 쓰지 않은 실제 사진 — 진짜 평가 대상
    split_path = ROOT / "dataset_noneye" / "split.json"
    if split_path.exists():
        holdout = json.loads(split_path.read_text(encoding="utf-8"))["holdout"]
        for name in holdout:
            path = ROOT / "dataset_noneye" / name
            if not path.exists():
                continue
            img = _load(path)
            negatives[f"holdout/{name}:full"] = img
            w, h = img.size
            for grid in (2, 3):
                for gy in range(grid):
                    for gx in range(grid):
                        negatives[f"holdout/{name}:g{grid}-{gy}{gx}"] = img.crop(
                            (gx * w // grid, gy * h // grid, (gx + 1) * w // grid, (gy + 1) * h // grid))
    else:
        print("  ⚠️ dataset_noneye/split.json 없음 — 학습에 안 쓴 사진으로 평가할 수 없다.")
        print("     python scripts/fetch_non_eye_photos.py 로 먼저 받으세요.")

    # (2) 저장소 기본 사진 — 학습에도 쓰이므로 참고용(회귀 감시)
    assets = ROOT / "static" / "assets"
    for name in ("vision-scene.jpg", "diseases/amd-fundus.jpg",
                 "diseases/diabetic-retinopathy-fundus.jpg"):
        path = assets / name
        if not path.exists():
            continue
        img = _load(path)
        negatives[f"repo/{name}:full"] = img
        w, h = img.size
        for grid in (2, 3):
            for gy in range(grid):
                for gx in range(grid):
                    negatives[f"repo/{name}:g{grid}-{gy}{gx}"] = img.crop(
                        (gx * w // grid, gy * h // grid, (gx + 1) * w // grid, (gy + 1) * h // grid))

    # (3) 합성 계열 — 참고용
    import importlib.util
    spec = importlib.util.spec_from_file_location("probe", ROOT / "scripts" / "probe_eye_gate.py")
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    for i, (img, kind) in enumerate(probe.synthetic_non_eye(random.Random(20260905))):
        negatives[f"synthetic/{kind}-{i}"] = img
    return negatives


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=300, help="클래스당 표본 수")
    parser.add_argument("--gate", type=Path, default=eye_validator._GATE_PATH,
                        help="비교할 게이트 npz 경로 (배포 파일은 변경하지 않음)")
    args = parser.parse_args()
    if args.sample < 1:
        parser.error("--sample must be positive")
    if not eye_validator.warmup() or not eye_validator.gate_available():
        raise SystemExit("Eye gate unavailable")
    gate_path = args.gate if args.gate.is_absolute() else ROOT / args.gate
    if gate_path.resolve() != eye_validator._GATE_PATH.resolve():
        try:
            gate = __import__("numpy").load(gate_path)
            eye_validator._gate_w = eye_validator.torch.from_numpy(gate["w"].astype("float32")).to(eye_validator.device)
            eye_validator._gate_b = float(gate["b"].item())
            eye_validator._gate_thr = float(gate["threshold"].item())
        except Exception as exc:
            raise SystemExit(f"Cannot load gate {gate_path}: {exc}")

    rng = random.Random(20260905)
    scores: dict[str, list[float]] = {}
    for category in ("0_normal", "1_cataract"):
        paths = sorted(p for p in (ROOT / "dataset" / category).rglob("*")
                       if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"})
        if not paths:
            raise SystemExit(f"Missing dataset: {category}")
        paths = rng.sample(paths, min(args.sample, len(paths)))
        scores[category] = [eye_validator._gate_prob(_load(p)) for p in paths]

    # 익상편 눈 — 정상 폴더 안의 소수 계열이라 정상 눈 거부율에 가려진다. v6가 편입한 질환군이므로
    # 따로 잰다(2026-09-13 실측: 임계 0.60에서 10% 거부가 이 표에 보이지 않았다).
    pter_paths = sorted((ROOT / "dataset" / "0_normal").glob("pterygium_*"))
    pter_paths = rng.sample(pter_paths, min(args.sample, len(pter_paths)))
    scores["pterygium"] = [eye_validator._gate_prob(_load(p)) for p in pter_paths]

    # 실제로 감긴 눈 — 학습에 쓰지 않은 사진(split.json holdout)의 검수 통과 크롭만.
    closed_scores = []
    cdir = ROOT / "dataset_closedeye"
    if (cdir / "review.json").exists() and (cdir / "split.json").exists():
        stems = {Path(n).stem for n in json.loads((cdir / "split.json").read_text(encoding="utf-8"))["holdout"]}
        for name in json.loads((cdir / "review.json").read_text(encoding="utf-8"))["closed"]:
            path = cdir / "crops" / name
            if name.split("__f")[0] in stems and path.exists():
                closed_scores.append(eye_validator._gate_prob(_load(path)))

    negatives = build_negatives()
    neg_scores = {k: eye_validator._gate_prob(v) for k, v in negatives.items()}

    # 얼굴 사진에서 잘라낸 눈 크롭은 반드시 통과해야 한다(얼굴 모드의 정상 경로)
    face_eyes = []
    face_path = ROOT / "static" / "assets" / "examples" / "face-good.jpg"
    if face_path.exists():
        face_crops = eye_detector.extract_eye_crops(_load(face_path)) or []
        face_eyes = [eye_validator._gate_prob(c) for c in face_crops]

    n_neg = len(neg_scores)
    print(f"눈 표본: 정상 {len(scores['0_normal'])}장 / 백내장 {len(scores['1_cataract'])}장 / 익상편 {len(scores['pterygium'])}장")
    print(f"감은 눈 표본(학습 미사용 사진): {len(closed_scores)}개")
    print(f"비-눈 표본: {n_neg}개 (실제 사진 크롭 + 합성)")
    print(f"얼굴 사진의 눈 크롭 점수: {[round(s, 3) for s in face_eyes]}  ← 반드시 통과해야 함")
    print()
    print(f"{'임계값':>10} | {'정상 눈 거부':>12} | {'백내장 눈 거부':>14} | {'익상편 눈 거부':>14} | {'비-눈 통과':>12} | {'감은 눈 통과(holdout)':>16}")
    print("-" * 104)
    for t in THRESHOLDS:
        nrm = sum(s < t for s in scores["0_normal"])
        cat = sum(s < t for s in scores["1_cataract"])
        leak = sum(s >= t for s in neg_scores.values())
        pt = sum(s < t for s in scores["pterygium"]); npt = max(1, len(scores["pterygium"]))
        cl = sum(s >= t for s in closed_scores); ncl = len(closed_scores)
        closed_txt = f"{cl:>3}/{ncl} ({cl/ncl:>5.1%})" if ncl else "   (검수 자료 없음)"
        print(f"{t:>10.3f} | {nrm:>4}/{len(scores['0_normal'])} ({nrm/len(scores['0_normal']):>5.1%})"
              f" | {cat:>4}/{len(scores['1_cataract'])} ({cat/len(scores['1_cataract']):>5.1%})"
              f" | {pt:>4}/{len(scores['pterygium'])} ({pt/npt:>5.1%})"
              f" | {leak:>3}/{n_neg} ({leak/n_neg:>5.1%})"
              f" | {closed_txt}")

    holdout_scores = {k: v for k, v in neg_scores.items() if k.startswith("holdout/")}
    if holdout_scores:
        print()
        print(f"※ 학습에 쓰지 않은 사진만: {len(holdout_scores)}개  최고점 {max(holdout_scores.values()):.4f}")
        print("   (이 숫자가 진짜 지표다. 나머지 계열은 학습에도 쓰여 낙관적으로 나온다)")
        for t in THRESHOLDS:
            leak = sum(s >= t for s in holdout_scores.values())
            print(f"     임계 {t:.3f}: 통과 {leak:>3}/{len(holdout_scores)} ({leak/len(holdout_scores):>5.1%})")

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
