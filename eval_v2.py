r"""
v2 모델 평가 전용 스크립트 (재학습 X, 추론만)
================================================
- cataract_resnet18_v2.pth 가중치를 그대로 로드
- train_ai.py와 동일한 시드(42)/분할 비율로 test셋 재현
- argmax(임계값 0.5) 및 운영 임계값(50%/75%) 기준 혼동행렬·지표 출력
- 결과를 train_log_v2.txt로 저장 → 발표 근거 파일

실행:  .venv\Scripts\python.exe eval_v2.py
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

# train_ai.py와 반드시 동일해야 하는 설정
DATA_DIR    = "dataset"
WEIGHTS     = "cataract_resnet18_v2.pth"
IMG_SIZE    = 224
BATCH_SIZE  = 64
NUM_WORKERS = 4
SEED        = 42
VAL_RATIO   = 0.15
TEST_RATIO  = 0.15
NORM_MEAN   = [0.485, 0.456, 0.406]
NORM_STD    = [0.229, 0.224, 0.225]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

eval_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(NORM_MEAN, NORM_STD),
])


def rgb_loader(path: str) -> Image.Image:
    with open(path, "rb") as f:
        img = Image.open(f)
        return ImageOps.exif_transpose(img.convert("RGB"))


def stratified_split(targets, val_ratio, test_ratio, seed):
    """train_ai.py와 동일한 층화 분할 (같은 seed → 같은 test셋 보장)."""
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
def collect_probs(model, loader):
    model.eval()
    all_probs, all_labels = [], []
    for x, y in loader:
        x = x.to(device)
        probs = torch.softmax(model(x), dim=1)[:, 1]
        all_probs += probs.cpu().tolist()
        all_labels += y.tolist()
    return np.array(all_probs), np.array(all_labels)


def metrics_at(probs, labels, thr):
    preds = (probs >= thr).astype(int)
    tp = int(((preds == 1) & (labels == 1)).sum())
    tn = int(((preds == 0) & (labels == 0)).sum())
    fp = int(((preds == 1) & (labels == 0)).sum())
    fn = int(((preds == 0) & (labels == 1)).sum())
    acc = (tp + tn) / max(len(labels), 1)
    sens = tp / max(tp + fn, 1)
    spec = tn / max(tn + fp, 1)
    return tn, fp, fn, tp, acc, sens, spec


def main():
    if not os.path.isdir(DATA_DIR):
        raise SystemExit(f"❌ 데이터 폴더 없음: {DATA_DIR}")
    if not os.path.exists(WEIGHTS):
        raise SystemExit(f"❌ 가중치 없음: {WEIGHTS}")

    base = ImageFolder(DATA_DIR, loader=rgb_loader)
    targets = base.targets
    n0 = sum(1 for t in targets if t == 0)
    n1 = sum(1 for t in targets if t == 1)

    train_idx, val_idx, test_idx = stratified_split(targets, VAL_RATIO, TEST_RATIO, SEED)
    eval_ds_full = ImageFolder(DATA_DIR, transform=eval_tf, loader=rgb_loader)
    test_ds = Subset(eval_ds_full, test_idx)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False,
                             num_workers=NUM_WORKERS, pin_memory=(device.type == "cuda"))

    model = build_model().to(device)
    model.load_state_dict(torch.load(WEIGHTS, map_location=device, weights_only=True))
    model.eval()

    probs, labels = collect_probs(model, test_loader)
    auc = manual_auc(probs, labels)

    lines = []
    def out(s=""):
        print(s)
        lines.append(s)

    out("=== v2 모델 평가 (eval_v2.py / 재학습 없이 추론만) ===")
    out(f"가중치: {WEIGHTS}")
    out(f"클래스 매핑: {base.class_to_idx}")
    out(f"전체 데이터: 정상(0)={n0} / 백내장(1)={n1} / 합계={n0+n1}")
    out(f"분할(seed={SEED}) → train {len(train_idx)} / val {len(val_idx)} / test {len(test_idx)}")
    test_n0 = int((labels == 0).sum()); test_n1 = int((labels == 1).sum())
    out(f"테스트셋 구성: 정상={test_n0} / 백내장={test_n1}")
    out(f"AUC = {auc:.4f}")
    out("")

    for thr, tag in [(0.5, "argmax/50%"), (0.75, "75%")]:
        tn, fp, fn, tp, acc, sens, spec = metrics_at(probs, labels, thr)
        out(f"--- 임계값 {tag} ---")
        out(f"정확도 {acc:.4f} | 민감도 {sens:.4f} | 특이도 {spec:.4f}")
        out(f"혼동행렬  TN={tn} FP={fp} FN={fn} TP={tp}")
        out("")

    with open("train_log_v2.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("💾 저장: train_log_v2.txt")


if __name__ == "__main__":
    main()
