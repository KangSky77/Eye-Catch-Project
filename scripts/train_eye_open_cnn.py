"""얼굴 모드 눈 크롭 '뜸 여부' — 합성곱 미세조정 판정기 학습 (선형 판정기와 비교용)
==================================================================================
배경: build_eye_open_gate.py의 선형 판정기(ResNet18 고정 특징 + 로지스틱)는 감은 눈의 91.8%를
막았지만 AI로 만든 '웃으며 눈 감은 얼굴'을 0.345/0.357로 통과시켰다. 고정 특징 위의 선 하나로는
초승달 모양 눈꺼풀과 가늘게 뜬 눈의 경계를 긋기 어렵다. 그래서 특징 자체를 이 과제에 맞춘다.

구조: ImageNet ResNet18의 layer1~3은 눈 게이트와 공유(고정)하고, layer4와 분류 헤드만 새로 학습한다.
  - 추론 때 앞 세 층을 한 번만 계산해 눈 게이트와 판정기가 나눠 쓴다(추가 연산은 layer4 한 번).
  - 저장 파일은 layer4 + 헤드 가중치만(fp16) — 백본 전체보다 작다.

데이터: build_eye_open_gate.py와 같다(검수된 review.json, 묶음 단위 split.json).
  양성 = openeye "open" + closedeye "excluded_open_eye" + smileeye "open"
  음성 = closedeye "closed" + smileeye "closed"

임계값: 학습 분할에서 사진 단위로 15%를 떼어 '검증'으로 쓰고, 검증의 뜬 눈 99%가 통과하는 값을
고른다. 평가(holdout) 분할은 임계값 선택에 쓰지 않는다 — 평가 수치가 낙관적으로 부풀지 않게.

실행:  python scripts/train_eye_open_cnn.py --out <경로>.pt
"""
import argparse
import copy
import random
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import ImageFilter
from torchvision import models, transforms

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_eye_open_gate import load_split, open_rgb   # 같은 검수·분할 규칙을 그대로 쓴다

SEED = 20260913
TARGET_OPEN_PASS = 0.99
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
NORM = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
EVAL_TF = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(), NORM])


class RandomBlur:
    def __call__(self, im):
        if random.random() < 0.3:
            return im.filter(ImageFilter.GaussianBlur(random.uniform(0.3, 1.8)))
        return im


TRAIN_TF = transforms.Compose([
    # 얼굴 크롭은 MTCNN 눈 좌표 오차로 위치·크기가 조금씩 흔들린다 — 그 범위를 흉내 낸다
    transforms.RandomResizedCrop(224, scale=(0.75, 1.0), ratio=(0.9, 1.1)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(12),
    transforms.ColorJitter(0.35, 0.35, 0.25, 0.03),
    RandomBlur(),
    transforms.RandomGrayscale(0.1),
    transforms.ToTensor(),
    NORM,
])


class Head(torch.nn.Module):
    """layer3 출력(256x14x14) → 뜸 여부 로짓. layer4는 ImageNet 가중치에서 시작해 미세조정한다."""

    def __init__(self, layer4):
        super().__init__()
        self.layer4 = layer4
        self.fc = torch.nn.Sequential(torch.nn.Dropout(0.3), torch.nn.Linear(512, 1))

    def forward(self, l3):
        return self.fc(self.layer4(l3).mean(dim=(2, 3))).squeeze(1)


def stem_front(net):
    return torch.nn.Sequential(net.conv1, net.bn1, net.relu, net.maxpool, net.layer1, net.layer2, net.layer3)


def split_validation(paths, frac=0.15):
    """학습 경로를 사진(원본 이름) 단위로 나눠 검증을 떼어낸다."""
    stems = sorted({p.name.split("__f")[0] for p in paths})
    random.Random(SEED).shuffle(stems)
    val = set(stems[:max(1, int(len(stems) * frac))])
    train = [p for p in paths if p.name.split("__f")[0] not in val]
    valid = [p for p in paths if p.name.split("__f")[0] in val]
    return train, valid


@torch.no_grad()
def scores(front, head, paths, bs=64):
    head.eval()
    out = []
    for i in range(0, len(paths), bs):
        x = torch.stack([EVAL_TF(open_rgb(p)) for p in paths[i:i + bs]]).to(device)
        out.append(torch.sigmoid(head(front(x))).cpu())
    return torch.cat(out).numpy() if out else np.array([])


def threshold_for(open_scores):
    return float(np.sort(open_scores)[int((1 - TARGET_OPEN_PASS) * len(open_scores))])


def rate(values, pred):
    return float(np.mean(pred(values))) * 100 if len(values) else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--epochs", type=int, default=25)
    args = ap.parse_args()
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    tr_open = (load_split("dataset_openeye", "open", "train") + load_split("dataset_closedeye", "excluded_open_eye", "train")
               + load_split("dataset_smileeye", "open", "train"))
    tr_closed = load_split("dataset_closedeye", "closed", "train") + load_split("dataset_smileeye", "closed", "train")
    ho_open = (load_split("dataset_openeye", "open", "holdout") + load_split("dataset_closedeye", "excluded_open_eye", "holdout")
               + load_split("dataset_smileeye", "open", "holdout"))
    ho_closed = load_split("dataset_closedeye", "closed", "holdout") + load_split("dataset_smileeye", "closed", "holdout")
    tr_open, va_open = split_validation(tr_open)
    tr_closed, va_closed = split_validation(tr_closed)
    print(f"뜬 눈 학습 {len(tr_open)}/검증 {len(va_open)}/평가 {len(ho_open)}  "
          f"감은 눈 학습 {len(tr_closed)}/검증 {len(va_closed)}/평가 {len(ho_closed)}  ({device})")

    net = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1).eval().to(device)
    front = stem_front(net).eval()
    for prm in front.parameters():
        prm.requires_grad = False
    head = Head(copy.deepcopy(net.layer4)).to(device)

    items = [(p, 1.0) for p in tr_open] + [(p, 0.0) for p in tr_closed]
    imgs = {p: open_rgb(p) for p, _ in items}
    weights = torch.tensor([1.0 / len(tr_open) if y else 1.0 / len(tr_closed) for _, y in items])
    opt = torch.optim.AdamW([{"params": head.layer4.parameters(), "lr": 1e-4},
                             {"params": head.fc.parameters(), "lr": 1e-3}], weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    best, best_state = -1.0, None
    steps = max(1, len(items) // 32)
    for epoch in range(args.epochs):
        head.train()
        idx = torch.multinomial(weights, steps * 32, replacement=True).tolist()   # 클래스 균형 표본추출
        for s in range(steps):
            batch = [items[j] for j in idx[s * 32:(s + 1) * 32]]
            with torch.no_grad():
                x = front(torch.stack([TRAIN_TF(imgs[p]) for p, _ in batch]).to(device))
            y = torch.tensor([label for _, label in batch], device=device)
            loss = torch.nn.functional.binary_cross_entropy_with_logits(head(x), y)
            opt.zero_grad()
            loss.backward()
            opt.step()
        sched.step()
        vo, vc = scores(front, head, va_open), scores(front, head, va_closed)
        thr = threshold_for(vo)
        vrej = float(np.mean(vc < thr))
        if vrej > best:
            best, best_state = vrej, copy.deepcopy(head.state_dict())
        print(f"  epoch {epoch + 1:2d}  loss {loss.item():.3f}  검증 감은 눈 거부 {vrej * 100:5.1f}% "
              f"(뜬 눈 99% 기준 임계 {thr:.3f})", flush=True)

    head.load_state_dict(best_state)
    thr = threshold_for(scores(front, head, va_open))
    ho, hc = scores(front, head, ho_open), scores(front, head, ho_closed)
    print(f"\n[선택] 임계 {thr:.3f} (검증에서 결정)  평가: 뜬 눈 통과 {rate(ho, lambda v: v >= thr):5.1f}%  "
          f"감은 눈 거부 {rate(hc, lambda v: v < thr):5.1f}%")
    so, sc = load_split("dataset_smileeye", "open", "holdout"), load_split("dataset_smileeye", "closed", "holdout")
    if so or sc:
        pso, psc = scores(front, head, so), scores(front, head, sc)
        print(f"  └ 웃는 얼굴(평가): 가늘게 뜬 눈 통과 {rate(pso, lambda v: v >= thr):5.1f}% (n={len(so)})  "
              f"웃으며 감은 눈 거부 {rate(psc, lambda v: v < thr):5.1f}% (n={len(sc)})")
    if args.out:
        state = {k: v.half() for k, v in head.state_dict().items()}
        meta = {"trained": "2026-09-13", "seed": SEED, "threshold": thr, "target_open_pass": TARGET_OPEN_PASS,
                "threshold_chosen_on": "validation carved from train split (photo-level)",
                "holdout_open_pass": rate(ho, lambda v: v >= thr) / 100,
                "holdout_closed_reject": rate(hc, lambda v: v < thr) / 100,
                "n_train_open": len(tr_open), "n_train_closed": len(tr_closed),
                "n_holdout_open": len(ho_open), "n_holdout_closed": len(ho_closed),
                "arch": "resnet18 IMAGENET1K_V1 layer1-3 frozen (shared with eye gate) "
                        "+ fine-tuned layer4 + Dropout+Linear(512,1)"}
        torch.save({"state_dict": state, "meta": meta}, args.out)
        print(f"💾 저장: {args.out}")


if __name__ == "__main__":
    main()
