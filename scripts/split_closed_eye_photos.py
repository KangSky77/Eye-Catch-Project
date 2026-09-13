"""감은 눈 사진을 학습/평가로 나눈다 — 거의 같은 사진은 한 묶음으로.

왜 묶는가: Commons는 같은 사진이 여러 범주에 들어 있어, 파일명이 달라도 픽셀이 같은
사진이 흔하다(검수 중 확인: 같은 여성 사진이 크롭 140·142로 두 번 나왔다). 파일 단위로만
나누면 같은 얼굴이 학습과 평가 양쪽에 들어가 평가가 일반화가 아니라 암기를 잰다.

방식: 사진마다 16x16 흑백 차이 해시(dHash, 255비트)를 만들고, 해밍 거리 20 이하를
같은 묶음으로 합친다(union-find). 묶음 단위로 섞어 평가 30%를 떼어낸다.
review.json의 감은 눈 크롭이 있는 사진만 대상으로 한다.

실행:  python scripts/split_closed_eye_photos.py                          # 감은 눈
       python scripts/split_closed_eye_photos.py --dir dataset_openeye --key open   # 뜬 눈
출력:  dataset_closedeye/split.json  {"seed", "train": [사진 파일명], "holdout": [...], "groups": n}
"""
import argparse, json, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "dataset_closedeye"
SEED = 20260913
HOLDOUT = 0.30
MAX_DIST = 20


def dhash(path: Path) -> np.ndarray:
    with Image.open(path) as s:
        g = ImageOps.exif_transpose(s).convert("L").resize((17, 16), Image.LANCZOS)
    a = np.asarray(g, dtype=np.int16)
    return (a[:, 1:] > a[:, :-1]).flatten()


def main():
    global D
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="dataset_closedeye")
    ap.add_argument("--key", default="closed", help="review.json에서 분할 대상 크롭 목록 키")
    args = ap.parse_args()
    D = ROOT / args.dir
    review = json.loads((D / "review.json").read_text(encoding="utf-8"))
    # 대상 크롭이 있는 사진 전부를 나눈다 — 감은 눈 폴더의 excluded_open_eye(뜬 눈 양성)도 같은 분할을 따라야
    # 한 사진의 감은 눈과 뜬 눈이 학습·평가로 갈라지지 않는다.
    # 판정기가 쓰는 크롭 목록 전부를 한 분할로 묶는다(closed·open·excluded_open_eye). 웃는 얼굴 폴더는
    # 한 사진에 감은 눈과 뜬 눈이 함께 있을 수 있어, 키별로 따로 나누면 같은 얼굴이 학습·평가로 갈라진다.
    # 기존 두 폴더는 쓰지 않는 키가 비어 있으므로 분할 결과가 바뀌지 않는다.
    target = (set(review.get(args.key, [])) | set(review.get("closed", [])) | set(review.get("open", []))
              | set(review.get("excluded_open_eye", [])))
    stems = sorted({c.split("__f")[0] for c in target})
    by_stem = {p.stem: p for p in D.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")}
    photos = [by_stem[s] for s in stems if s in by_stem]
    hashes = [dhash(p) for p in photos]
    parent = list(range(len(photos)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    merged = 0
    for i in range(len(photos)):
        for j in range(i + 1, len(photos)):
            if int((hashes[i] != hashes[j]).sum()) <= MAX_DIST and find(i) != find(j):
                parent[find(i)] = find(j); merged += 1
    groups = {}
    for i, p in enumerate(photos):
        groups.setdefault(find(i), []).append(p.name)
    group_list = sorted(groups.values())
    random.Random(SEED).shuffle(group_list)
    n_closed = {p.name: sum(1 for c in target if c.split("__f")[0] == p.stem) for p in photos}
    total = sum(n_closed.values()); target = int(total * HOLDOUT)
    holdout, train, got = [], [], 0
    for g in group_list:
        if got < target:
            holdout += g; got += sum(n_closed[n] for n in g)
        else:
            train += g
    out = {"seed": SEED, "method": f"dHash 16x16, hamming<={MAX_DIST} 묶음 단위 분할",
           "groups": len(group_list), "near_duplicate_merges": merged,
           "train": sorted(train), "holdout": sorted(holdout)}
    (D / "split.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"사진 {len(photos)}장 → 묶음 {len(group_list)}개 (근접중복 병합 {merged}회)")
    print(f"감은 눈 크롭: 학습 {total - got}개 / 평가 {got}개")


if __name__ == "__main__":
    main()
