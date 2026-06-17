"""
백내장 분류 모델 학습 스크립트 (전이학습 / Transfer Learning)
================================================================
- 백본: ImageNet 사전학습 ResNet18  (app/models/cataract_model.py)
- 데이터: dataset/0_normal, dataset/1_cataract  (ImageFolder)
- 핵심 개선점:
    1) 전이학습으로 소량 데이터에서도 높은 정확도
    2) train/val/test 층화 분할 (test셋으로 진짜 성능 측정)
    3) 데이터 증강 (회전/반전/밝기 등)
    4) 클래스 불균형 보정 (가중 CrossEntropyLoss)
       ← 정상 14,993 vs 백내장 1,823 (약 8:1 — 정상이 다수 클래스)
       ※ bincount로 자동 계산되므로 데이터가 바뀌어도 코드 수정 불필요
    5) 2단계 학습: 헤드 먼저 → 전체 미세조정
    6) 의료용 지표: 정확도 + 민감도/특이도 + AUC + 혼동행렬
       + 운영 임계값(vision.py의 75%) 기준 지표도 함께 출력
    7) 검증 성능 기준 Early Stopping & best 가중치 저장
    8) num_workers/pin_memory로 대용량(1.6만장) 로딩 가속

실행:  (프로젝트 루트에서)
    python train_ai.py
필요 패키지: torch, torchvision  (sklearn 불필요 - 지표 직접 구현)
"""

import os
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import transforms
from torchvision.datasets import ImageFolder
from PIL import Image, ImageOps

from app.models.cataract_model import build_model

# ----------------------------- 설정 -----------------------------
DATA_DIR      = "dataset"
OUTPUT_PATH   = "cataract_resnet18_v2.pth"   # 새 데이터셋(정상 1.5만장) 학습 가중치
IMG_SIZE      = 224
BATCH_SIZE    = 64    # 데이터가 커져서 배치 키움 (GPU 메모리 부족하면 32로)
NUM_WORKERS   = 4     # 1.6만장 로딩 가속 (Windows에서도 __main__ 가드 있어 안전)
SEED          = 42
PROD_THRESHOLD = 0.75  # vision.py의 운영 임계값(75%) — 같은 기준으로 지표 확인용
VAL_RATIO     = 0.15
TEST_RATIO    = 0.15
HEAD_EPOCHS   = 5     # 1단계: 백본 동결, 분류 헤드만 학습
FINETUNE_EPOCHS = 20  # 2단계: 전체 미세조정
PATIENCE      = 5     # Early Stopping
LR_HEAD       = 1e-3
LR_FINETUNE   = 1e-4

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ImageNet 정규화 (vision.py 추론 전처리와 반드시 동일)
NORM_MEAN = [0.485, 0.456, 0.406]
NORM_STD  = [0.229, 0.224, 0.225]


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def rgb_loader(path: str) -> Image.Image:
    # EXIF 회전 반영 + RGB 변환 (추론과 동일하게 처리)
    with open(path, "rb") as f:
        img = Image.open(f)
        return ImageOps.exif_transpose(img.convert("RGB"))


# 학습용: 증강 / 평가용: 증강 없음
train_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
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


def stratified_split(targets, val_ratio, test_ratio, seed):
    """클래스 비율을 유지하며 train/val/test 인덱스로 분할."""
    rng = random.Random(seed)
    by_class = {}
    for idx, label in enumerate(targets):
        by_class.setdefault(label, []).append(idx)

    train_idx, val_idx, test_idx = [], [], []
    for label, idxs in by_class.items():
        rng.shuffle(idxs)
        n = len(idxs)
        n_test = int(n * test_ratio)
        n_val = int(n * val_ratio)
        test_idx += idxs[:n_test]
        val_idx  += idxs[n_test:n_test + n_val]
        train_idx += idxs[n_test + n_val:]
    rng.shuffle(train_idx)
    return train_idx, val_idx, test_idx


def manual_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """순위 기반(Mann-Whitney U) AUC. sklearn 없이 계산.
    scores: 양성(백내장=1) 확률, labels: 0/1"""
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)
    # 동점 평균 순위 처리
    _, inv, counts = np.unique(scores, return_inverse=True, return_counts=True)
    sum_ranks = np.zeros(len(counts))
    np.add.at(sum_ranks, inv, ranks)
    avg_ranks = sum_ranks / counts
    ranks = avg_ranks[inv]
    sum_pos = ranks[labels == 1].sum()
    n_pos, n_neg = len(pos), len(neg)
    return (sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


@torch.no_grad()
def evaluate(model, loader):
    model.eval()
    all_probs, all_labels, all_preds = [], [], []
    loss_sum, n = 0.0, 0
    criterion = nn.CrossEntropyLoss()
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        out = model(x)
        loss_sum += criterion(out, y).item() * x.size(0)
        n += x.size(0)
        probs = torch.softmax(out, dim=1)[:, 1]  # 백내장 확률
        all_probs += probs.cpu().tolist()
        all_preds += out.argmax(1).cpu().tolist()
        all_labels += y.cpu().tolist()

    labels = np.array(all_labels)
    preds  = np.array(all_preds)
    probs  = np.array(all_probs)

    # 혼동행렬 (양성=백내장=1)
    tp = int(((preds == 1) & (labels == 1)).sum())
    tn = int(((preds == 0) & (labels == 0)).sum())
    fp = int(((preds == 1) & (labels == 0)).sum())
    fn = int(((preds == 0) & (labels == 1)).sum())

    acc = (tp + tn) / max(len(labels), 1)
    sensitivity = tp / max(tp + fn, 1)   # 재현율(민감도) - 백내장을 놓치지 않는 비율
    specificity = tn / max(tn + fp, 1)   # 특이도 - 정상을 정상이라 맞히는 비율
    auc = manual_auc(probs, labels)
    return {
        "loss": loss_sum / max(n, 1), "acc": acc,
        "sensitivity": sensitivity, "specificity": specificity, "auc": auc,
        "cm": (tn, fp, fn, tp),
    }


@torch.no_grad()
def collect_probs(model, loader):
    """테스트셋의 백내장 확률·정답 라벨만 모아서 반환 (임계값 분석용)."""
    model.eval()
    all_probs, all_labels = [], []
    for x, y in loader:
        x = x.to(device)
        probs = torch.softmax(model(x), dim=1)[:, 1]
        all_probs += probs.cpu().tolist()
        all_labels += y.tolist()
    return np.array(all_probs), np.array(all_labels)


def train_phase(model, train_loader, val_loader, criterion, optimizer, epochs, phase_name, best_state):
    best_auc = best_state["auc"]
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
        print(f"[{phase_name}] epoch {epoch:02d}/{epochs} | "
              f"train_loss {train_loss:.4f} | val_loss {val['loss']:.4f} "
              f"| val_acc {val['acc']:.3f} | val_AUC {val['auc']:.3f} "
              f"| sens {val['sensitivity']:.3f} | spec {val['specificity']:.3f}")

        # best 갱신 (AUC 기준)
        if not np.isnan(val["auc"]) and val["auc"] > best_auc:
            best_auc = val["auc"]
            best_state["auc"] = best_auc
            best_state["model"] = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience_left = PATIENCE
            print(f"    ✅ best 갱신 (val_AUC={best_auc:.4f}) → 저장 대기")
        else:
            patience_left -= 1
            if patience_left <= 0:
                print(f"    ⏹️  Early Stopping ({phase_name})")
                break
    return best_state


def main():
    set_seed(SEED)
    if not os.path.isdir(DATA_DIR):
        raise SystemExit(f"❌ 데이터 폴더가 없습니다: {DATA_DIR}")

    # 같은 root에 train/eval 두 변환을 적용하기 위해 두 번 생성
    base = ImageFolder(DATA_DIR, loader=rgb_loader)
    print(f"클래스 매핑: {base.class_to_idx}  (백내장=1 이어야 정상)")
    targets = base.targets

    train_idx, val_idx, test_idx = stratified_split(targets, VAL_RATIO, TEST_RATIO, SEED)
    print(f"분할 → train {len(train_idx)} / val {len(val_idx)} / test {len(test_idx)}")

    train_ds_full = ImageFolder(DATA_DIR, transform=train_tf, loader=rgb_loader)
    eval_ds_full  = ImageFolder(DATA_DIR, transform=eval_tf,  loader=rgb_loader)
    train_ds = Subset(train_ds_full, train_idx)
    val_ds   = Subset(eval_ds_full, val_idx)
    test_ds  = Subset(eval_ds_full, test_idx)

    pin = device.type == "cuda"
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=NUM_WORKERS, pin_memory=pin,
                              persistent_workers=NUM_WORKERS > 0)
    val_loader   = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False,
                              num_workers=NUM_WORKERS, pin_memory=pin,
                              persistent_workers=NUM_WORKERS > 0)
    test_loader  = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False,
                              num_workers=NUM_WORKERS, pin_memory=pin,
                              persistent_workers=NUM_WORKERS > 0)

    # 클래스 불균형 보정: 가중치 = 전체 / (클래스수 * 클래스빈도)
    counts = np.bincount([targets[i] for i in train_idx])
    weights = counts.sum() / (len(counts) * counts)
    class_weights = torch.tensor(weights, dtype=torch.float32).to(device)
    print(f"클래스 가중치(불균형 보정): {weights.round(3)}")
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    model = build_model(pretrained=True).to(device)
    best_state = {"auc": -1.0, "model": None}

    # ---- 1단계: 백본 동결, 헤드만 학습 ----
    for name, p in model.named_parameters():
        p.requires_grad = name.startswith("fc.")
    opt_head = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=LR_HEAD)
    print("\n=== 1단계: 분류 헤드 학습 (백본 동결) ===")
    best_state = train_phase(model, train_loader, val_loader, criterion, opt_head, HEAD_EPOCHS, "head", best_state)

    # ---- 2단계: 전체 미세조정 ----
    for p in model.parameters():
        p.requires_grad = True
    opt_ft = torch.optim.Adam(model.parameters(), lr=LR_FINETUNE)
    print("\n=== 2단계: 전체 미세조정 (fine-tune) ===")
    best_state = train_phase(model, train_loader, val_loader, criterion, opt_ft, FINETUNE_EPOCHS, "finetune", best_state)

    # ---- best 가중치 로드 후 test 평가 & 저장 ----
    if best_state["model"] is not None:
        model.load_state_dict(best_state["model"])
    torch.save(model.state_dict(), OUTPUT_PATH)
    print(f"\n💾 best 가중치 저장: {OUTPUT_PATH}")

    print("\n=== 최종 TEST 평가 (argmax = 임계값 0.5) ===")
    test = evaluate(model, test_loader)
    tn, fp, fn, tp = test["cm"]
    print(f"정확도(Accuracy)      : {test['acc']:.3f}")
    print(f"민감도(Sensitivity)   : {test['sensitivity']:.3f}  (백내장을 놓치지 않는 비율 - 의료에서 가장 중요)")
    print(f"특이도(Specificity)   : {test['specificity']:.3f}")
    print(f"AUC                   : {test['auc']:.3f}")
    print(f"혼동행렬  TN={tn} FP={fp} FN={fn} TP={tp}")
    print("  (FN=백내장인데 정상이라 놓친 수 → 0에 가까울수록 좋음)")

    # 운영 임계값(vision.py cat_p >= 75%) 기준 지표 — 실제 서비스에서 보는 성능
    probs, labels = collect_probs(model, test_loader)
    p_preds = (probs >= PROD_THRESHOLD).astype(int)
    p_tp = int(((p_preds == 1) & (labels == 1)).sum())
    p_tn = int(((p_preds == 0) & (labels == 0)).sum())
    p_fp = int(((p_preds == 1) & (labels == 0)).sum())
    p_fn = int(((p_preds == 0) & (labels == 1)).sum())
    p_sens = p_tp / max(p_tp + p_fn, 1)
    p_spec = p_tn / max(p_tn + p_fp, 1)
    print(f"\n=== 운영 임계값 {PROD_THRESHOLD:.0%} 기준 (vision.py와 동일) ===")
    print(f"민감도 {p_sens:.3f} | 특이도 {p_spec:.3f} | TN={p_tn} FP={p_fp} FN={p_fn} TP={p_tp}")
    if p_sens < test["sensitivity"] - 0.02:
        print("⚠️  75% 임계값에서 민감도가 크게 떨어집니다 → vision.py 임계값 하향 검토 필요")


if __name__ == "__main__":
    main()
