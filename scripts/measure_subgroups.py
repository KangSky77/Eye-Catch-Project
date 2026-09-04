"""하위그룹별 오분류 측정 — 익상편 · 밝은 홍채 · 백내장을 같은 held-out에서 비교.

왜 필요한가:
    docs/retraining-v6.md의 성공 기준 세 가지(익상편 오분류율 / 백내장 민감도 /
    밝은 홍채 오탐) 중 익상편과 밝은 홍채는 메타데이터에 안 남는다. 그런데 두
    데이터 모두 이제 dataset/0_normal 안에 있어서, 폴더째 채점하면 학습에 쓴
    사진으로 채점하는 누수가 된다.

    그래서 train_ai_v3.group_aware_split(SEED 고정)으로 학습 때와 똑같은 분할을
    재현하고 **test 몫만** 채점한다. 이 이미지들은 v5에게도(학습 전이라) v6에게도
    (test로 뺐으니) held-out이라, 두 모델을 같은 자로 잴 수 있다.

무엇을 세는가:
    '놓쳤다'의 기준은 FN이 아니라 **경계·판단어려움에도 못 걸려 '특징 없음'으로 안내된 백내장**이다
    (4단계 판정 — vision._classify 참고). FN과 나란히 센다. TTA는 배포 설정(settings.use_tta)을 따른다.

주의:
    group_aware_split은 그룹맵이 바뀌면(사진 추가·제거) 분할 전체가 다시 섞인다. 학습 때와 다른
    그룹맵으로 돌리면 test에 학습 사진이 섞여(누수) 수치가 부풀 수 있다 — 2026-09-02 라벨 오류
    10장 제거 후 v6를 돌리면 그런 상태다. 학습 직후의 그룹맵으로만 신뢰할 수 있다.

사용법:
    python scripts/measure_subgroups.py                      # 배포 가중치만
    python scripts/measure_subgroups.py --weights a.pth b.pth # 여러 개 비교
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)
sys.path.insert(0, str(REPO_ROOT / "scripts"))

sys.stdout.reconfigure(encoding="utf-8")

import argparse
from collections import Counter

import torch
from torchvision.datasets import ImageFolder

from train_ai_v3 import (
    DATA_DIR, SEED, VAL_RATIO, TEST_RATIO,
    load_group_map, group_aware_split, rgb_loader,
)
from app.models.cataract_model import build_model
from app.core.config import settings
from app.services.vision import preprocess, _classify

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 파일명 접두사로 하위그룹을 나눈다 (prepare 스크립트들이 붙인 접두사)
SUBGROUPS = {
    "익상편": "pterygium_",
    "밝은홍채": "brightiris_",
}


def classify(prob_pct: float) -> str:
    return _classify(prob_pct)[0]      # 배포와 같은 4단계: risk / borderline / uncertain / normal


@torch.no_grad()
def predict_all(model, paths, batch=64):
    """배포와 동일한 방식(settings.use_tta면 좌우반전 평균)의 확률(%)을 순서대로 반환."""
    out = []
    nview = 2 if settings.use_tta else 1
    for i in range(0, len(paths), batch):
        chunk = paths[i:i + batch]
        views = []
        for p in chunk:
            x = preprocess(rgb_loader(p))
            views.append(x)
            if settings.use_tta:
                views.append(torch.flip(x, dims=[2]))
        probs = torch.softmax(model(torch.stack(views).to(device)), dim=1)[:, 1]
        out.extend((probs.view(-1, nview).mean(dim=1) * 100).tolist())
        print(f"\r  {min(i + batch, len(paths))}/{len(paths)}", end="", flush=True)
    print("\r" + " " * 30 + "\r", end="")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", nargs="+", default=[settings.model_path])
    args = ap.parse_args()

    print("test split 재현 중...")
    base = ImageFolder(str(DATA_DIR), loader=rgb_loader)
    group_map = load_group_map(DATA_DIR)
    _, _, test_idx, _ = group_aware_split(base, group_map, VAL_RATIO, TEST_RATIO, SEED)

    # test 몫을 하위그룹으로 쪼갠다
    buckets = {name: [] for name in SUBGROUPS}
    buckets["정상(기타)"] = []
    buckets["백내장"] = []
    for idx in test_idx:
        path, label = base.samples[idx]
        name = Path(path).name
        if label == 1:
            buckets["백내장"].append(path)
            continue
        for gname, prefix in SUBGROUPS.items():
            if name.startswith(prefix):
                buckets[gname].append(path)
                break
        else:
            buckets["정상(기타)"].append(path)

    print(f"test {len(test_idx)}장 = " +
          " / ".join(f"{k} {len(v)}" for k, v in buckets.items() if v))
    print(f"판정: risk ≥{settings.risk_threshold} > borderline ≥{settings.borderline_threshold} "
          f"> uncertain ≥{settings.uncertain_threshold} > normal | TTA {'ON' if settings.use_tta else 'OFF'}\n")

    results = {}
    for w in args.weights:
        if not Path(w).exists():
            print(f"⚠️  건너뜀 (파일 없음): {w}")
            continue
        model = build_model(backbone=settings.model_backbone).to(device)
        model.load_state_dict(torch.load(w, map_location=device, weights_only=True))
        model.eval()
        print(f"▶ {w}")
        results[w] = {k: Counter(classify(p) for p in predict_all(model, v))
                      for k, v in buckets.items() if v}
        del model
        if device.type == "cuda":
            torch.cuda.empty_cache()

    # ---- 출력 ----
    names = list(results)
    label = lambda w: Path(w).stem.replace("cataract_efficientnet_b0_", "")

    print("\n" + "=" * 68)
    print("하위그룹별 판정 분포 (test 몫, 전부 held-out)")
    print("=" * 68)
    for group in buckets:
        if not buckets[group]:
            continue
        n = len(buckets[group])
        print(f"\n[{group}] {n}장")
        for w in names:
            c = results[w][group]
            if group == "백내장":
                # 백내장은 '못 잡은 것'이 문제
                missed = c["normal"]
                print(f"  {label(w):<22} 위험 {c['risk']:>4}  경계 {c['borderline']:>3}  판단어려움 {c['uncertain']:>3}  "
                      f"특징없음(=놓침) {missed:>3}  → 민감도(50) {(c['risk'] / n * 100):.1f}%")
            else:
                # 정상 계열은 '위험/경계로 잘못 안내한 것'이 문제 (판단어려움은 재촬영 안내라 따로 센다)
                bad = c["risk"] + c["borderline"]
                print(f"  {label(w):<22} 위험 {c['risk']:>4}  경계 {c['borderline']:>3}  판단어려움 {c['uncertain']:>3}  "
                      f"특징없음 {c['normal']:>4}  → 오분류(위험+경계) {bad}/{n} ({bad / n * 100:.1f}%)")


if __name__ == "__main__":
    main()
