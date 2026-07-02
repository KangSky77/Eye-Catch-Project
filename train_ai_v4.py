"""
백내장 분류 모델 학습 스크립트 v4 (백본 비교 실험)
================================================================
v3(train_ai_v3.py)의 레시피 — 그룹 단위 분할, WeightedRandomSampler,
2단계 학습(헤드→전체 미세조정), balanced_accuracy+0.25*F1 선택 기준 —
를 그대로 재사용하고, **백본만 인자로 교체**해 공정하게 비교한다.

v3 대비 추가된 것:
  1) --backbone 인자: resnet18(기존) | efficientnet_b0 (cataract_model.py 참고)
  2) 최종 test 평가에 TTA(좌우반전 평균) 지표 추가 — 운영 추론(vision.py)이
     TTA를 쓰므로, 배포 성능과 같은 방식의 수치를 메타데이터에 남긴다.
  3) 출력 파일명에 백본이 들어가 기존 v3 가중치를 덮어쓰지 않음.

실행:  python dedup_dataset.py                        (dataset 변경 시 1회)
       python train_ai_v4.py --backbone resnet18
       python train_ai_v4.py --backbone efficientnet_b0
비교:  두 메타데이터 JSON의 best_val_metrics(선택은 반드시 val 기준!)를 비교해
       승자를 고르고, test 지표는 마지막 확인용으로만 본다.
"""
import argparse
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Subset
from torchvision.datasets import ImageFolder

# v3의 검증된 구성요소를 그대로 재사용 (동일 시드/분할/증강/선택 기준 보장)
from train_ai_v3 import (
    DATA_DIR, BATCH_SIZE, NUM_WORKERS, SEED, VAL_RATIO, TEST_RATIO,
    HEAD_EPOCHS, FINETUNE_EPOCHS, LR_HEAD, LR_FINETUNE,
    NORM_MEAN, NORM_STD, SELECTION_METRIC_DESC, TARGET_SENSITIVITY, PROD_THRESHOLD,
    set_seed, rgb_loader, train_tf, eval_tf,
    load_group_map, group_aware_split, make_sampler,
    evaluate, manual_auc, choose_threshold_on_val, train_phase, device,
)
from app.models.cataract_model import build_model, head_param_prefix


@torch.no_grad()
def evaluate_tta(model, loader, threshold: float = 0.5) -> dict:
    """운영 추론(vision.py의 _predict_single)과 동일한 좌우반전 TTA로 평가.
    배포 시 실제로 나갈 확률과 같은 방식이므로, 이 지표가 '서비스 성능'에 가장 가깝다."""
    model.eval()
    all_probs, all_labels = [], []
    for x, y in loader:
        x = x.to(device)
        p1 = F.softmax(model(x), dim=1)[:, 1]
        p2 = F.softmax(model(torch.flip(x, dims=[3])), dim=1)[:, 1]   # W축(좌우) 반전
        all_probs += ((p1 + p2) / 2).cpu().tolist()
        all_labels += y.tolist()

    labels = np.array(all_labels)
    probs = np.array(all_probs)
    preds = (probs >= threshold).astype(int)
    tp = int(((preds == 1) & (labels == 1)).sum())
    tn = int(((preds == 0) & (labels == 0)).sum())
    fp = int(((preds == 1) & (labels == 0)).sum())
    fn = int(((preds == 0) & (labels == 1)).sum())
    sensitivity = tp / max(tp + fn, 1)
    specificity = tn / max(tn + fp, 1)
    precision = tp / max(tp + fp, 1)
    return {
        "accuracy": (tp + tn) / max(len(labels), 1),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "cataract_precision": precision,
        "cataract_f1": 2 * precision * sensitivity / max(1e-12, precision + sensitivity),
        "balanced_accuracy": (sensitivity + specificity) / 2,
        "auc": manual_auc(probs, labels),
        "cm": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def main():
    parser = argparse.ArgumentParser(description="백내장 모델 v4 학습 (백본 비교)")
    parser.add_argument("--backbone", default="resnet18",
                        choices=["resnet18", "efficientnet_b0"])
    args = parser.parse_args()
    backbone = args.backbone

    output_path = f"cataract_{backbone}_v4.pth"
    metadata_path = f"cataract_{backbone}_v4_metadata.json"
    t_start = time.time()

    set_seed(SEED)
    data_dir = Path(DATA_DIR)
    if not data_dir.is_dir():
        raise SystemExit(f"❌ 데이터 폴더가 없습니다: {DATA_DIR}")

    group_map = load_group_map(data_dir)
    base = ImageFolder(DATA_DIR, loader=rgb_loader)
    print(f"[v4/{backbone}] 클래스 매핑: {base.class_to_idx} (백내장=1 이어야 정상)")

    train_idx, val_idx, test_idx, excluded_idx = group_aware_split(
        base, group_map, VAL_RATIO, TEST_RATIO, SEED)
    print(f"그룹 단위 분할 → train {len(train_idx)} / val {len(val_idx)} / test {len(test_idx)}"
          + (f" / 라벨충돌 제외 {len(excluded_idx)}" if excluded_idx else ""))

    train_ds = Subset(ImageFolder(DATA_DIR, transform=train_tf, loader=rgb_loader), train_idx)
    eval_full = ImageFolder(DATA_DIR, transform=eval_tf, loader=rgb_loader)
    val_ds, test_ds = Subset(eval_full, val_idx), Subset(eval_full, test_idx)

    train_targets = [base.targets[i] for i in train_idx]
    print(f"클래스 분포 → train {dict(Counter(train_targets))} | "
          f"val {dict(Counter(base.targets[i] for i in val_idx))} | "
          f"test {dict(Counter(base.targets[i] for i in test_idx))}")

    pin = device.type == "cuda"
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE,
                              sampler=make_sampler(train_targets),
                              num_workers=NUM_WORKERS, pin_memory=pin,
                              persistent_workers=NUM_WORKERS > 0)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False,
                            num_workers=NUM_WORKERS, pin_memory=pin,
                            persistent_workers=NUM_WORKERS > 0)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False,
                             num_workers=NUM_WORKERS, pin_memory=pin,
                             persistent_workers=NUM_WORKERS > 0)

    # WeightedRandomSampler가 배치 클래스 비율을 이미 맞추므로 일반 CE (v3와 동일)
    criterion = nn.CrossEntropyLoss()
    model = build_model(pretrained=True, backbone=backbone).to(device)
    n_params = sum(p.numel() for p in model.parameters()) / 1e6
    print(f"백본: {backbone} (파라미터 {n_params:.1f}M)")

    best_state = {"score": -1.0, "metrics": {}, "model": None}

    head_prefix = head_param_prefix(backbone)
    for name, p in model.named_parameters():
        p.requires_grad = name.startswith(head_prefix)
    opt_head = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=LR_HEAD)
    print(f"\n=== 1단계: 분류 헤드 학습 (백본 동결, '{head_prefix}*'만 학습) ===")
    best_state = train_phase(model, train_loader, val_loader, criterion, opt_head,
                             HEAD_EPOCHS, f"{backbone}/head", best_state)

    for p in model.parameters():
        p.requires_grad = True
    opt_ft = torch.optim.Adam(model.parameters(), lr=LR_FINETUNE)
    print("\n=== 2단계: 전체 미세조정 (fine-tune) ===")
    best_state = train_phase(model, train_loader, val_loader, criterion, opt_ft,
                             FINETUNE_EPOCHS, f"{backbone}/finetune", best_state)

    if best_state["model"] is not None:
        model.load_state_dict(best_state["model"])
    torch.save(model.state_dict(), output_path)
    print(f"\n💾 best 가중치 저장: {output_path}")

    print(f"\n=== 최종 TEST 평가 — 운영 임계값 {PROD_THRESHOLD:.0%} 기준 ===")
    test_prod = evaluate(model, test_loader, threshold=PROD_THRESHOLD)
    print(f"[기본]  민감도 {test_prod['sensitivity']:.3f} | 특이도 {test_prod['specificity']:.3f} "
          f"| AUC {test_prod['auc']:.4f} | 혼동행렬 {test_prod['cm']}")
    test_prod_tta = evaluate_tta(model, test_loader, threshold=PROD_THRESHOLD)
    print(f"[TTA ]  민감도 {test_prod_tta['sensitivity']:.3f} | 특이도 {test_prod_tta['specificity']:.3f} "
          f"| AUC {test_prod_tta['auc']:.4f} | 혼동행렬 {test_prod_tta['cm']}  ← 운영(vision.py)과 동일 방식")

    val_threshold, val_threshold_metrics = choose_threshold_on_val(model, val_loader)
    test_val_thr = evaluate(model, test_loader, threshold=val_threshold)
    print(f"\n=== validation에서 선택한 threshold {val_threshold:.0%} 기준 (참고) ===")
    print(f"VAL 근거: {val_threshold_metrics['selection_reason']}")
    print(f"TEST 민감도 {test_val_thr['sensitivity']:.3f} | 특이도 {test_val_thr['specificity']:.3f} "
          f"| 혼동행렬 {test_val_thr['cm']}")

    elapsed_min = (time.time() - t_start) / 60
    metadata = {
        "version": "v4",
        "backbone": backbone,
        "params_millions": round(n_params, 1),
        "class_to_idx": base.class_to_idx,
        "seed": SEED,
        "image_size": 224,
        "normalization": {"mean": NORM_MEAN, "std": NORM_STD},
        "split_unit": "dedup_group (near-duplicate-safe)",
        "excluded_label_conflict_images": len(excluded_idx),
        "counts": {
            "train": dict(Counter(train_targets)),
            "val": dict(Counter(base.targets[i] for i in val_idx)),
            "test": dict(Counter(base.targets[i] for i in test_idx)),
        },
        "selection_metric": SELECTION_METRIC_DESC,
        "best_val_metrics": best_state["metrics"],
        "prod_threshold": PROD_THRESHOLD,
        "test_metrics_at_prod_threshold": test_prod,
        "test_metrics_at_prod_threshold_tta": test_prod_tta,   # 운영 추론과 동일 방식
        "val_selected_threshold": val_threshold,
        "val_selected_threshold_target_sensitivity": TARGET_SENSITIVITY,
        "test_metrics_at_val_selected_threshold": test_val_thr,
        "train_minutes": round(elapsed_min, 1),
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"💾 메타데이터 저장: {metadata_path} (학습 {elapsed_min:.0f}분 소요)")


if __name__ == "__main__":
    main()
