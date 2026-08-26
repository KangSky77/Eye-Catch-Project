"""익상편 캐글 데이터셋 정리 — 학습에 넣기 전 1회 실행.

캐글에서 받은 익상편 데이터는 Roboflow 증강본이 섞여 있어 그대로 쓰면 두 가지가 깨진다.

원본은 dataset_raw/ 에 둔다 — dataset/ 안에 두면 ImageFolder가 하위 폴더를 전부
클래스로 읽어서 2클래스 모델(cataract_model.py)과 어긋난다(실제로 학습이 즉시 멈췄다).

  1) 누수 — 같은 원본의 변형본이 최대 16장. train/val/test로 흩어지면
     v2에서 겪은 근접중복 누수가 재현된다(그때 정확도 99.9%가 부풀려진 원인).
  2) 지름길 학습 — 회전 증강으로 생긴 검은 모서리가 익상편 54.8% / 정상 4.8%로
     클래스마다 크게 다르다. 모델이 '익상편'이 아니라 '검은 모서리'를 배우고,
     test에도 같은 여백이 있어 지표로는 드러나지 않는다.
     (지금 모델이 '수정체 혼탁' 대신 '하얀 정도'를 배운 것과 같은 실패다)

그래서 원본 식별자별로 '가장 깨끗한 1장'만 남기고, 그마저 지저분한 것은 버린다.
증강은 train_ai_v3.py가 학습 중에 수행하므로 미리 구운 증강본은 필요 없다.

출력: dataset/0_normal/ 로 복사 (pterygium_ 접두사)
      -> 3클래스가 아니라 '백내장이 아닌 것'으로 가르치기 위함.
         검열반·각막혼탁은 공개 데이터가 10장 안팎이라 클래스로 만들 수 없고,
         같은 시각적 계열이라 이 경계 학습의 전이를 기대한다.
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
import collections
import shutil

import numpy as np
from PIL import Image

SRC = Path("dataset_raw/2_pterygium_kaggle_raw")
DST = Path("dataset/0_normal")
PREFIX = "pterygium_"
BLACK_LEVEL = 18        # 이 값 미만이면 '검정'으로 본다
CORNER_MAX = 0.02       # 모서리 검정 비율 상한 (정상 클래스 평균 1.4% 수준에 맞춤)


def corner_black_ratio(path: Path) -> float:
    """네 모서리(각 16x16)에서 거의 검은 픽셀이 차지하는 비율."""
    a = np.asarray(Image.open(path).convert("RGB").resize((128, 128)), dtype=np.uint8)
    corners = [a[:16, :16], a[:16, -16:], a[-16:, :16], a[-16:, -16:]]
    return float(np.mean([(c.max(axis=2) < BLACK_LEVEL).mean() for c in corners]))


def main() -> None:
    ap = argparse.ArgumentParser(description="익상편 데이터 정리 후 정상 클래스로 편입")
    ap.add_argument("--apply", action="store_true", help="실제로 복사한다(기본은 미리보기)")
    ap.add_argument("--corner-max", type=float, default=CORNER_MAX)
    args = ap.parse_args()

    if not SRC.is_dir():
        raise SystemExit(f"❌ 폴더가 없습니다: {SRC}")

    # Roboflow 파일명: <원본식별자>.rf.<해시>.jpg — 앞부분이 같으면 같은 원본이다
    groups = collections.defaultdict(list)
    for f in SRC.iterdir():
        if f.is_file():
            groups[f.name.split(".rf.")[0]].append(f)

    kept, dropped = [], []
    for gid, files in sorted(groups.items()):
        best = min(files, key=corner_black_ratio)
        ratio = corner_black_ratio(best)
        (kept if ratio <= args.corner_max else dropped).append((gid, best, ratio))

    print(f"원본 식별자 {len(groups)}개 / 전체 파일 {sum(len(v) for v in groups.values())}장")
    print(f"  ✅ 채택 {len(kept)}개 (모서리 검정 {args.corner_max*100:.0f}% 이하)")
    print(f"  ❌ 제외 {len(dropped)}개 (모든 변형본에 검은 여백 — 중앙 크롭으로도 못 살림)")

    if not args.apply:
        print("\n미리보기입니다. 실제로 복사하려면 --apply 를 붙이세요.")
        return

    DST.mkdir(parents=True, exist_ok=True)
    n = 0
    for gid, path, _ in kept:
        out = DST / f"{PREFIX}{gid}.jpg"
        if out.exists():
            continue
        shutil.copy2(path, out)
        n += 1
    print(f"\n📦 {DST} 로 {n}장 복사 완료 (접두사 {PREFIX!r})")
    print("다음: python scripts/dedup_dataset.py  →  python scripts/train_ai_v4.py --backbone efficientnet_b0 --batch 40")


if __name__ == "__main__":
    main()
