"""
데이터셋 중복/근접중복(near-duplicate) 탐지 스크립트
================================================================
목적: train/val/test로 나누기 전에, 같은(또는 거의 같은) 사진이 여러 장
      존재하는지 찾아서 그룹으로 묶는다. 이 그룹 정보가 있어야 재학습
      스크립트가 "같은 사진이 train과 test에 동시에 들어가는" 누수를
      막을 수 있다 (그룹 전체를 한 split에만 배정).

방식: perceptual hash(phash, 64비트)로 시각적으로 거의 동일한 이미지를 찾는다.
      - 정확히 같은 해시 → 같은 그룹 (exact duplicate)
      - 실제 해밍거리 <= DUP_THRESHOLD → 같은 그룹 (near duplicate, 리사이즈/
        재인코딩/약한 크롭 등으로 픽셀이 살짝 달라진 동일 출처 사진)

      과거에는 LSH 밴딩(64비트를 4개 16비트 밴드로 쪼개 같은 밴드값만 후보로
      비교)으로 O(n^2) 비교를 피했는데, 실제로 audit_dedup.py로 전수 검사해보니
      해밍거리 차이가 여러 밴드에 걸쳐 분산된 근접중복 636쌍을 놓쳤다(밴드가
      하나도 일치하지 않아 후보에서 빠짐). 16,816장 기준 numpy 바이트 popcount로
      벡터화하면 정확한 O(n^2) 비교도 1분 내로 끝나길래, 근사(LSH) 대신 정확한
      방식으로 교체했다 — false negative 없음.

실행:  python dedup_dataset.py
출력:  dataset_group_map.json  ({"0_normal/img (1).jpg": group_id, ...})
       콘솔에 중복 그룹 요약 + (있다면) 클래스가 다른데 중복인 경우 경고
"""
import json
import os
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import imagehash
import numpy as np
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True  # 살짝 깨진 파일도 최대한 읽어서 스킵 수를 줄임

DATA_DIR = Path("dataset")
CLASSES = ["0_normal", "1_cataract"]
OUTPUT_PATH = Path("dataset_group_map.json")
HASH_SIZE = 8          # 8x8 DCT → 64비트 해시
DUP_THRESHOLD = 6      # 해밍거리 이 값 이하면 "같은 출처 사진"으로 간주 (보수적 값)
COMPARE_CHUNK = 2000   # O(n^2) 비교를 메모리에 맞게 청크 단위로 처리
POPCOUNT_TABLE = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)


def _hash_one(path: str):
    try:
        with Image.open(path) as img:
            h = imagehash.phash(img.convert("RGB"), hash_size=HASH_SIZE)
        return path, int(str(h), 16)
    except Exception as e:
        return path, None


def compute_hashes(paths: list[str]) -> dict[str, int]:
    results = {}
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        for path, h in ex.map(_hash_one, paths, chunksize=64):
            if h is not None:
                results[path] = h
            else:
                print(f"  ⚠️  읽기 실패(스킵): {path}")
    return results


def hamming_block(chunk: np.ndarray, full: np.ndarray) -> np.ndarray:
    """chunk(C,) vs full(N,) uint64 해시 간 해밍거리 (C,N) 행렬을 바이트 popcount로 벡터화 계산."""
    xor = chunk[:, None] ^ full[None, :]
    total = np.zeros(xor.shape, dtype=np.uint16)
    for shift in range(0, 64, 8):
        byte = ((xor >> np.uint64(shift)) & np.uint64(0xFF)).astype(np.uint8)
        total += POPCOUNT_TABLE[byte]
    return total


class UnionFind:
    def __init__(self, items):
        self.parent = {x: x for x in items}

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        # 경로 압축 (Path Compression)
        curr = x
        while curr != root:
            nxt = self.parent[curr]
            self.parent[curr] = root
            curr = nxt
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def group_duplicates(hashes: dict[str, int]) -> dict[str, int]:
    """모든 쌍을 정확히(O(n^2), 근사 없이) 비교해 해밍거리 <= DUP_THRESHOLD인
    이미지를 같은 그룹으로 묶는다. numpy 바이트 popcount로 벡터화해 16,816장
    기준으로도 1분 내에 끝난다."""
    paths = list(hashes.keys())
    hash_arr = np.array([hashes[p] for p in paths], dtype=np.uint64)
    n = len(paths)
    uf = UnionFind(paths)

    merged = 0
    for start in range(0, n, COMPARE_CHUNK):
        end = min(start + COMPARE_CHUNK, n)
        dist = hamming_block(hash_arr[start:end], hash_arr)
        for local_i, global_i in enumerate(range(start, end)):
            row = dist[local_i]
            close = np.where(row[global_i + 1:] <= DUP_THRESHOLD)[0] + global_i + 1
            for j in close:
                a, b = paths[global_i], paths[j]
                if uf.find(a) != uf.find(b):
                    uf.union(a, b)
                    merged += 1
        print(f"  진행: {end}/{n}", end="\r")
    print(f"\n  (정확 비교로 {merged}건 병합)")

    # 그룹 id 부여 (정렬해서 재현 가능하게)
    roots = sorted({uf.find(p) for p in paths})
    root_to_gid = {r: i for i, r in enumerate(roots)}
    return {p: root_to_gid[uf.find(p)] for p in paths}


def main():
    if not DATA_DIR.is_dir():
        raise SystemExit(f"❌ 데이터 폴더가 없습니다: {DATA_DIR}")

    IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    all_paths = []
    label_of = {}
    for cls in CLASSES:
        cls_dir = DATA_DIR / cls
        for f in sorted(cls_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in IMG_EXTENSIONS:
                rel = str(f.as_posix())
                all_paths.append(rel)
                label_of[rel] = cls

    print(f"📂 전체 이미지 {len(all_paths)}장 — phash 계산 중 (CPU {os.cpu_count()}코어)...")
    hashes = compute_hashes(all_paths)
    print(f"✅ 해시 계산 완료: {len(hashes)}/{len(all_paths)}장 성공")

    print(f"🔍 중복 그룹 탐색 중 (임계값 해밍거리 ≤ {DUP_THRESHOLD})...")
    group_map = group_duplicates(hashes)

    groups = defaultdict(list)
    for p, gid in group_map.items():
        groups[gid].append(p)

    dup_groups = {gid: members for gid, members in groups.items() if len(members) > 1}
    dup_images = sum(len(m) for m in dup_groups.values())
    cross_class = []
    for gid, members in dup_groups.items():
        labels = {label_of[m] for m in members}
        if len(labels) > 1:
            cross_class.append((gid, members, labels))

    print()
    print("=" * 60)
    print(f"전체 이미지        : {len(group_map)}")
    print(f"고유 그룹(=실질 사진 수): {len(groups)}")
    print(f"중복 그룹 수        : {len(dup_groups)}  (그 안에 사진 {dup_images}장)")
    print(f"중복으로 줄어드는 수  : {len(group_map) - len(groups)}장 (이만큼이 '가짜 추가 샘플')")
    print(f"⚠️  클래스가 엇갈린 중복 그룹: {len(cross_class)}건")
    if cross_class:
        print("    (같은 사진이 0_normal과 1_cataract 둘 다에 라벨링됨 — 데이터 품질 버그 가능성)")
        for gid, members, labels in cross_class[:10]:
            print(f"    - group {gid} {labels}: {members}")

    largest = sorted(dup_groups.items(), key=lambda kv: -len(kv[1]))[:10]
    if largest:
        print("\n가장 큰 중복 그룹 Top 10:")
        for gid, members in largest:
            print(f"    group {gid} ({len(members)}장): {members[:4]}{' ...' if len(members) > 4 else ''}")
    print("=" * 60)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(group_map, f, ensure_ascii=False)
    print(f"\n💾 그룹 매핑 저장: {OUTPUT_PATH} (재학습 스크립트가 이걸 읽어 그룹 단위로 split)")


if __name__ == "__main__":
    main()
