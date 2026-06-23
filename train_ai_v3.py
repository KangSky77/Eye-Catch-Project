"""
백내장 분류 모델 학습 스크립트 v3 (그룹 분할 + 불균형 보정 강화)
================================================================
v2(train_ai.py) 대비 바뀐 점 — Codex 버전(compare/codex/train_cataract_balanced.py)의
불균형 대응 기법을 이식하고, 데이터 중복 누수를 차단함:

  1) 그룹 단위 분할: dedup_dataset.py가 만든 dataset_group_map.json을 읽어서
     "거의 같은 사진"이 train/val/test에 동시에 들어가지 않도록 그룹 전체를
     하나의 split에만 배정한다. 중복 이미지를 삭제(drop)하는 것은 아니며,
     split 간 누수를 막는 것이 목적이다. (v2는 사진 1장 단위로 무작위 분할 → 누수 가능)
  2) WeightedRandomSampler 추가: 기존 class-weighted loss에 더해, 학습 배치
     자체도 클래스 균형을 맞춰 뽑는다 (Codex 기법 — 이중 보정이라 다소 강하지만
     의도적으로 그대로 이식).
  3) 모델 선택 기준 변경: AUC 단독 → balanced_accuracy + 0.25*cataract_f1
     (Codex 기법 — 클래스 불균형 상황에서 AUC만 보는 것보다 안정적인 선택 기준)
  4) 학습마다 메타데이터(JSON)를 같이 저장해 "이 가중치가 어떤 데이터/설정으로
     나왔는지" 추적 가능하게 함.

ResNet18 전이학습 + 2단계 학습(헤드→전체 미세조정)은 v2 방식을 유지.
실행:  python dedup_dataset.py   (먼저 1회, dataset_group_map.json 생성)
       python train_ai_v3.py
"""

import json
import random
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset, WeightedRandomSampler
from torchvision import transforms
from torchvision.datasets import ImageFolder
from PIL import Image, ImageOps

from app.models.cataract_model import build_model
from app.core.config import settings

# ----------------------------- 설정 -----------------------------
DATA_DIR        = "dataset"
GROUP_MAP_PATH  = "dataset_group_map.json"   # dedup_dataset.py 출력
OUTPUT_PATH     = "cataract_resnet18_v3.pth"
METADATA_PATH   = "cataract_resnet18_v3_metadata.json"
IMG_SIZE        = 224
BATCH_SIZE      = 64
NUM_WORKERS     = 4
SEED            = 42
PROD_THRESHOLD  = settings.risk_threshold / 100.0  # vision.py와 같은 출처(config.py)
TARGET_SENSITIVITY = 0.99       # 스크리닝 목적: validation에서 이 민감도 이상인 threshold 중 선택
VAL_RATIO       = 0.15
TEST_RATIO      = 0.15
HEAD_EPOCHS     = 5
FINETUNE_EPOCHS = 20
PATIENCE        = 5
LR_HEAD         = 1e-3
LR_FINETUNE     = 1e-4
SELECTION_METRIC_DESC = "balanced_accuracy + 0.25*cataract_f1"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

NORM_MEAN = [0.485, 0.456, 0.406]
NORM_STD  = [0.229, 0.224, 0.225]


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def rgb_loader(path: str) -> Image.Image:
    with open(path, "rb") as f:
        img = Image.open(f)
        return ImageOps.exif_transpose(img.convert("RGB"))


# 학습용: v2보다 한 단계 더 (RandomResizedCrop으로 줌/크롭 변화도 학습) — Codex 기법 흡수
train_tf = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomResizedCrop(IMG_SIZE, scale=(0.82, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize(NORM_MEAN, NORM_STD),
])
eval_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(NORM_MEAN, NORM_STD),
])


def load_group_map(data_dir: Path) -> dict:
    p = Path(GROUP_MAP_PATH)
    if not p.exists():
        raise SystemExit(
            f"❌ {GROUP_MAP_PATH}가 없습니다. 먼저 `python dedup_dataset.py`를 실행해 "
            "중복 그룹 매핑을 만드세요 (그룹 단위 분할에 필요)."
        )
    with p.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    # dedup_dataset.py는 "0_normal/img (1).jpg" 같은 상대경로 키를 씀
    return raw


def group_aware_split(dataset: ImageFolder, group_map: dict, val_ratio: float, test_ratio: float, seed: int):
    """같은 그룹(중복/근접중복)의 사진은 항상 같은 split에만 들어가도록 분할.

    그룹 단위로 먼저 클래스별 분할 비율을 맞추고, 그 다음 그룹에 속한
    이미지 인덱스 전체를 해당 split에 배정한다."""
    rng = random.Random(seed)

    # 이미지 인덱스 → 그룹id, 그룹id → (라벨, 인덱스 리스트)
    idx_to_group = {}
    for idx, (path, _) in enumerate(dataset.samples):
        # ImageFolder(DATA_DIR, ...)는 DATA_DIR이 상대경로("dataset")면 path도 상대경로로 줌 →
        # dedup_dataset.py가 만든 키("dataset/0_normal/img (1).jpg")와 그대로 맞춰야 함
        rel = Path(path).as_posix()
        rel_alt = "/".join(Path(path).parts[-2:])  # "0_normal/xxx.jpg" 형태 폴백
        gid = group_map.get(rel, group_map.get(rel_alt))
        if gid is None:
            raise SystemExit(f"❌ 그룹 매핑에 없는 파일: {path} — dedup_dataset.py를 다시 실행하세요.")
        idx_to_group[idx] = gid

    group_to_indices = {}
    group_to_labels = {}
    for idx, gid in idx_to_group.items():
        group_to_indices.setdefault(gid, []).append(idx)
        group_to_labels.setdefault(gid, []).append(dataset.targets[idx])

    # 클래스가 섞인 그룹(같은/거의 같은 사진이 정상·백내장 양쪽에 존재)은 라벨 충돌이다.
    # 다수 라벨로 억지 처리하면 학습/평가 모두 오염되므로, 별도 기록하고 split에서 제외한다.
    group_label = {}
    mixed_group_ids = []
    for gid, labels in group_to_labels.items():
        c = Counter(labels)
        if len(c) > 1:
            mixed_group_ids.append(gid)
            continue
        group_label[gid] = c.most_common(1)[0][0]

    excluded_idx = []
    if mixed_group_ids:
        for gid in mixed_group_ids:
            excluded_idx.extend(group_to_indices[gid])
        conflict_report = {
            str(gid): {
                "count": len(group_to_indices[gid]),
                "labels": dict(Counter(group_to_labels[gid])),
                "paths": [dataset.samples[i][0] for i in group_to_indices[gid]],
            }
            for gid in sorted(mixed_group_ids)
        }
        with open("label_conflicts.json", "w", encoding="utf-8") as f:
            json.dump(conflict_report, f, ensure_ascii=False, indent=2)
        print(
            f"⚠️  클래스가 엇갈린 그룹 {len(mixed_group_ids)}개/"
            f"이미지 {len(excluded_idx)}장 제외 → label_conflicts.json 확인"
        )

    # 클래스별로 그룹을 모아 셔플 후 비율대로 분할
    groups_by_class = {}
    for gid, label in group_label.items():
        groups_by_class.setdefault(label, []).append(gid)

    train_idx, val_idx, test_idx = [], [], []
    for label, gids in groups_by_class.items():
        gids = gids[:]
        rng.shuffle(gids)
        n = len(gids)
        n_test = max(1, int(n * test_ratio))
        n_val = max(1, int(n * val_ratio))
        test_gids = gids[:n_test]
        val_gids = gids[n_test:n_test + n_val]
        train_gids = gids[n_test + n_val:]
        for gid in test_gids:
            test_idx.extend(group_to_indices[gid])
        for gid in val_gids:
            val_idx.extend(group_to_indices[gid])
        for gid in train_gids:
            train_idx.extend(group_to_indices[gid])

    rng.shuffle(train_idx)
    return train_idx, val_idx, test_idx, excluded_idx


def make_sampler(targets: list[int]) -> WeightedRandomSampler:
    """클래스별 1/빈도 가중치로 배치를 뽑아 학습 중 클래스 균형을 맞춤 (Codex 기법)."""
    counts = Counter(targets)
    weights = [1.0 / counts[t] for t in targets]
    return WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)


def manual_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)
    _, inv, counts = np.unique(scores, return_inverse=True, return_counts=True)
    sum_ranks = np.zeros(len(counts))
    np.add.at(sum_ranks, inv, ranks)
    avg_ranks = sum_ranks / counts
    ranks = avg_ranks[inv]
    sum_pos = ranks[labels == 1].sum()
    n_pos, n_neg = len(pos), len(neg)
    return (sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


@torch.no_grad()
def evaluate(model, loader, threshold: float = 0.5) -> dict:
    """v2의 정확도/민감도/특이도/AUC + Codex의 balanced_accuracy/F1을 모두 계산."""
    model.eval()
    all_probs, all_labels = [], []
    loss_sum, n = 0.0, 0
    criterion = nn.CrossEntropyLoss()
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        out = model(x)
        loss_sum += criterion(out, y).item() * x.size(0)
        n += x.size(0)
        probs = torch.softmax(out, dim=1)[:, 1]
        all_probs += probs.cpu().tolist()
        all_labels += y.cpu().tolist()

    labels = np.array(all_labels)
    probs = np.array(all_probs)
    preds = (probs >= threshold).astype(int)

    tp = int(((preds == 1) & (labels == 1)).sum())
    tn = int(((preds == 0) & (labels == 0)).sum())
    fp = int(((preds == 1) & (labels == 0)).sum())
    fn = int(((preds == 0) & (labels == 1)).sum())

    accuracy = (tp + tn) / max(len(labels), 1)
    sensitivity = tp / max(tp + fn, 1)       # = cataract_recall
    specificity = tn / max(tn + fp, 1)       # = normal_recall
    precision = tp / max(tp + fp, 1)
    f1 = 2 * precision * sensitivity / max(1e-12, precision + sensitivity)
    balanced_accuracy = (sensitivity + specificity) / 2
    auc = manual_auc(probs, labels)

    return {
        "loss": loss_sum / max(n, 1),
        "accuracy": accuracy,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "cataract_precision": precision,
        "cataract_f1": f1,
        "balanced_accuracy": balanced_accuracy,
        "auc": auc,
        "cm": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def selection_score(metrics: dict) -> float:
    return metrics["balanced_accuracy"] + 0.25 * metrics["cataract_f1"]


def choose_threshold_on_val(model, val_loader, target_sensitivity: float = TARGET_SENSITIVITY) -> tuple[float, dict]:
    """운영 threshold 후보를 test가 아니라 validation에서만 선택한다.

    스크리닝 서비스라 민감도를 우선한다. validation에서 target_sensitivity 이상을 만족하는
    threshold 중 specificity가 가장 높은 값을 고르고, 만족 후보가 없으면 balanced accuracy가
    가장 높은 값을 fallback으로 고른다. 최종 test는 이렇게 고른 threshold로 마지막 1회만 본다.
    """
    candidates = np.round(np.arange(0.05, 0.951, 0.01), 2)
    scored = [(float(t), evaluate(model, val_loader, threshold=float(t))) for t in candidates]
    feasible = [(t, m) for t, m in scored if m["sensitivity"] >= target_sensitivity]
    if feasible:
        best_t, best_m = max(feasible, key=lambda tm: (tm[1]["specificity"], tm[1]["balanced_accuracy"], tm[0]))
        best_m = dict(best_m)
        best_m["selection_reason"] = f"max specificity with sensitivity >= {target_sensitivity:.2f} on validation"
        return best_t, best_m

    best_t, best_m = max(scored, key=lambda tm: (tm[1]["balanced_accuracy"], tm[1]["sensitivity"], tm[0]))
    best_m = dict(best_m)
    best_m["selection_reason"] = "fallback max balanced_accuracy on validation"
    return best_t, best_m


def train_phase(model, train_loader, val_loader, criterion, optimizer, epochs, phase_name, best_state):
    best_score = best_state["score"]
    patience_left = PATIENCE
    for epoch in range(1, epochs + 1):
        model.train()
        running = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
            running += loss.item() * x.size(0)
        train_loss = running / len(train_loader.dataset)

        val = evaluate(model, val_loader)
        score = selection_score(val)
        print(f"[{phase_name}] epoch {epoch:02d}/{epochs} | "
              f"train_loss {train_loss:.4f} | val_loss {val['loss']:.4f} "
              f"| bal_acc {val['balanced_accuracy']:.3f} | cat_f1 {val['cataract_f1']:.3f} "
              f"| AUC {val['auc']:.3f} | score {score:.4f}")

        if score > best_score:
            best_score = score
            best_state["score"] = best_score
            best_state["metrics"] = val
            best_state["model"] = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience_left = PATIENCE
            print(f"    ✅ best 갱신 (score={best_score:.4f}) → 저장 대기")
        else:
            patience_left -= 1
            if patience_left <= 0:
                print(f"    ⏹️  Early Stopping ({phase_name})")
                break
    return best_state


def main():
    set_seed(SEED)
    data_dir = Path(DATA_DIR)
    if not data_dir.is_dir():
        raise SystemExit(f"❌ 데이터 폴더가 없습니다: {DATA_DIR}")

    group_map = load_group_map(data_dir)

    base = ImageFolder(DATA_DIR, loader=rgb_loader)
    print(f"클래스 매핑: {base.class_to_idx} (백내장=1 이어야 정상)")

    train_idx, val_idx, test_idx, excluded_idx = group_aware_split(base, group_map, VAL_RATIO, TEST_RATIO, SEED)
    print(f"그룹 단위 분할 → train {len(train_idx)} / val {len(val_idx)} / test {len(test_idx)}")
    if excluded_idx:
        print(f"라벨 충돌 제외 → {len(excluded_idx)}장")

    train_ds_full = ImageFolder(DATA_DIR, transform=train_tf, loader=rgb_loader)
    eval_ds_full  = ImageFolder(DATA_DIR, transform=eval_tf,  loader=rgb_loader)
    train_ds = Subset(train_ds_full, train_idx)
    val_ds   = Subset(eval_ds_full, val_idx)
    test_ds  = Subset(eval_ds_full, test_idx)

    train_targets = [base.targets[i] for i in train_idx]
    val_targets   = [base.targets[i] for i in val_idx]
    test_targets  = [base.targets[i] for i in test_idx]
    print(f"클래스 분포 → train {dict(Counter(train_targets))} | "
          f"val {dict(Counter(val_targets))} | test {dict(Counter(test_targets))}")

    pin = device.type == "cuda"
    train_loader = DataLoader(
        train_ds, batch_size=BATCH_SIZE,
        sampler=make_sampler(train_targets),     # Codex 기법: 클래스 균형 샘플링
        num_workers=NUM_WORKERS, pin_memory=pin, persistent_workers=NUM_WORKERS > 0,
    )
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False,
                            num_workers=NUM_WORKERS, pin_memory=pin, persistent_workers=NUM_WORKERS > 0)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False,
                             num_workers=NUM_WORKERS, pin_memory=pin, persistent_workers=NUM_WORKERS > 0)

    counts = np.bincount(train_targets)
    class_weights = torch.tensor(counts.sum() / (len(counts) * counts), dtype=torch.float32).to(device)
    print(f"클래스 가중치(참고용): {class_weights.cpu().numpy().round(3)}")
    # WeightedRandomSampler가 이미 배치 내 클래스 비율을 50:50으로 맞춰 공급하므로,
    # 손실 함수 가중치까지 이중 적용(Double weighting)하지 않도록 일반 CrossEntropyLoss를 사용합니다.
    criterion = nn.CrossEntropyLoss()

    model = build_model(pretrained=True).to(device)
    best_state = {"score": -1.0, "metrics": {}, "model": None}

    for name, p in model.named_parameters():
        p.requires_grad = name.startswith("fc.")
    opt_head = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=LR_HEAD)
    print("\n=== 1단계: 분류 헤드 학습 (백본 동결) ===")
    best_state = train_phase(model, train_loader, val_loader, criterion, opt_head, HEAD_EPOCHS, "head", best_state)

    for p in model.parameters():
        p.requires_grad = True
    opt_ft = torch.optim.Adam(model.parameters(), lr=LR_FINETUNE)
    print("\n=== 2단계: 전체 미세조정 (fine-tune) ===")
    best_state = train_phase(model, train_loader, val_loader, criterion, opt_ft, FINETUNE_EPOCHS, "finetune", best_state)

    if best_state["model"] is not None:
        model.load_state_dict(best_state["model"])
    torch.save(model.state_dict(), OUTPUT_PATH)
    print(f"\n💾 best 가중치 저장: {OUTPUT_PATH}")

    print(f"\n=== 최종 TEST 평가 (argmax = 임계값 0.5, 그룹 단위로 분할된 진짜 held-out) ===")
    test_05 = evaluate(model, test_loader, threshold=0.5)
    print(f"정확도 {test_05['accuracy']:.3f} | 민감도 {test_05['sensitivity']:.3f} | "
          f"특이도 {test_05['specificity']:.3f} | AUC {test_05['auc']:.3f} | "
          f"balanced_acc {test_05['balanced_accuracy']:.3f} | cataract_F1 {test_05['cataract_f1']:.3f}")
    print(f"혼동행렬 {test_05['cm']}")

    test_prod = evaluate(model, test_loader, threshold=PROD_THRESHOLD)
    print(f"\n=== 운영 임계값 {PROD_THRESHOLD:.0%} 기준 (vision.py와 동일, config.py가 출처) ===")
    print(f"민감도 {test_prod['sensitivity']:.3f} | 특이도 {test_prod['specificity']:.3f} | "
          f"혼동행렬 {test_prod['cm']}")

    val_threshold, val_threshold_metrics = choose_threshold_on_val(model, val_loader)
    test_val_threshold = evaluate(model, test_loader, threshold=val_threshold)
    print(f"\n=== validation에서 선택한 threshold {val_threshold:.0%} 기준 ===")
    print(f"VAL 선택 근거: {val_threshold_metrics['selection_reason']} | "
          f"민감도 {val_threshold_metrics['sensitivity']:.3f} | 특이도 {val_threshold_metrics['specificity']:.3f}")
    print(f"TEST 민감도 {test_val_threshold['sensitivity']:.3f} | "
          f"특이도 {test_val_threshold['specificity']:.3f} | 혼동행렬 {test_val_threshold['cm']}")

    metadata = {
        "architecture": "resnet18_transfer",
        "class_to_idx": base.class_to_idx,
        "seed": SEED,
        "image_size": IMG_SIZE,
        "normalization": {"mean": NORM_MEAN, "std": NORM_STD},
        "dedup_source": GROUP_MAP_PATH,
        "split_unit": "dedup_group (near-duplicate-safe)",
        "duplicates_are_grouped_not_dropped": True,
        "excluded_label_conflict_images": len(excluded_idx),
        "label_conflict_report": "label_conflicts.json" if excluded_idx else None,
        "counts": {
            "train": dict(Counter(train_targets)),
            "val": dict(Counter(val_targets)),
            "test": dict(Counter(test_targets)),
            "excluded_label_conflicts": dict(Counter(base.targets[i] for i in excluded_idx)),
        },
        "selection_metric": SELECTION_METRIC_DESC,
        "best_val_metrics": best_state["metrics"],
        "test_metrics_at_0.5": test_05,
        "test_metrics_at_prod_threshold": test_prod,
        "prod_threshold": PROD_THRESHOLD,
        "val_selected_threshold": val_threshold,
        "val_selected_threshold_target_sensitivity": TARGET_SENSITIVITY,
        "val_selected_threshold_metrics": val_threshold_metrics,
        "test_metrics_at_val_selected_threshold": test_val_threshold,
    }
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"💾 메타데이터 저장: {METADATA_PATH}")


if __name__ == "__main__":
    main()
