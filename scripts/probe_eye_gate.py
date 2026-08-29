"""
눈 검증기(OOD 게이트) 임계값 실측 스크립트
================================================================
왜 필요한가:
    scripts/build_eye_centroid.py도 임계값 근거를 뽑아 주지만, --non-eye로 '비-눈
    사진 폴더'를 따로 준비해야 한다. 그 폴더는 저장소에 없고 사람마다 다르다.
    그래서 "왜 0.62인가"를 남이 재현할 수 없었고, 실제로 기존 0.55는 비-눈 표본에
    특정 계열이 빠져 있어서 뚫렸다.

    2026-08-29 실사용 테스트: 초록 배경에 빨간 사각형만 그린 이미지가 게이트를
    통과해 "경계 단계 (안과 검진 권장)"이라는 의료 결과를 받았다. ImageNet 임베딩에서
    '배경 + 가운데 큰 덩어리'는 눈의 거친 구조와 실제로 닮았기 때문이다.

이 스크립트는:
    비-눈 표본을 **코드로 생성**한다(단색·노이즈·문서·그라디언트·블롭 계열).
    데이터 준비 없이 누구나 같은 숫자를 다시 뽑을 수 있고, 게이트를 뚫었던
    블롭 계열이 회귀 표본으로 항상 포함된다.

사용법:
    python scripts/probe_eye_gate.py --dataset dataset --n 300
    python scripts/probe_eye_gate.py --dataset dataset --n 300 --extra-non-eye my_photos/

주의:
    전처리·백본·정규화는 app/services/eye_validator.py와 반드시 같아야 한다.
    어긋나면 유사도 분포가 통째로 밀려 임계값이 의미를 잃는다.
"""
import argparse
import os
import random
import sys

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFilter
from torchvision import models, transforms

sys.stdout.reconfigure(encoding="utf-8")   # Windows cp949 콘솔에서도 안전하게

# eye_validator.py와 동일해야 하는 값들 ---------------------------------------
PREPROCESS = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])
IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
THRESHOLD_CANDIDATES = [0.50, 0.55, 0.58, 0.60, 0.62, 0.63, 0.65, 0.68, 0.70]


def build_backbone():
    net = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    net.fc = torch.nn.Identity()
    net.eval()
    return net


@torch.no_grad()
def score_images(net, centroid, imgs, batch=32):
    """이미지 리스트 → centroid와의 코사인 유사도 배열."""
    out = []
    for i in range(0, len(imgs), batch):
        chunk = imgs[i:i + batch]
        x = torch.stack([PREPROCESS(im.convert("RGB")) for im in chunk])
        f = net(x).numpy().astype(np.float32)
        f /= (np.linalg.norm(f, axis=1, keepdims=True) + 1e-8)
        out.extend((f @ centroid).tolist())
    return np.array(out, dtype=np.float32)


def score_paths(net, centroid, paths, batch=32):
    out = []
    for i in range(0, len(paths), batch):
        imgs = [Image.open(p) for p in paths[i:i + batch]]
        out.extend(score_images(net, centroid, imgs, batch).tolist())
        for im in imgs:
            im.close()
    return np.array(out, dtype=np.float32)


def sample_dir(d, n, rng):
    if not os.path.isdir(d):
        return []
    files = [os.path.join(d, f) for f in sorted(os.listdir(d))
             if f.lower().endswith(IMG_EXTS)]
    rng.shuffle(files)
    return files[:n]


def synthetic_non_eye(rng):
    """비-눈 표본을 코드로 생성. 반환: [(이미지, 계열이름), ...]

    blob_* 계열이 핵심이다 — 실제로 게이트를 통과했던 모양이므로 회귀 표본으로 남긴다.
    """
    items = []

    for c in [(128,) * 3, (20,) * 3, (240,) * 3, (224, 180, 150), (60, 120, 200), (30, 140, 60)]:
        items.append((Image.new("RGB", (600, 600), c), "solid"))

    for i in range(6):
        arr = np.random.RandomState(i).randint(0, 256, (400, 400, 3), dtype=np.uint8)
        items.append((Image.fromarray(arr), "noise"))

    for _ in range(6):
        im = Image.new("RGB", (800, 600), (250, 250, 248))
        d = ImageDraw.Draw(im)
        for r in range(14):
            d.rectangle([60, 60 + r * 35, 60 + rng.randint(300, 680), 70 + r * 35], fill=(40, 40, 40))
        items.append((im, "document"))

    for bg in [(120, 160, 90), (90, 90, 90), (200, 200, 190), (70, 110, 160)]:
        for fg in [(200, 80, 60), (60, 60, 70), (150, 120, 90), (40, 40, 45)]:
            for shape in ("rectangle", "ellipse"):
                im = Image.new("RGB", (800, 600), bg)
                getattr(ImageDraw.Draw(im), shape)([200, 150, 600, 450], fill=fg)
                items.append((im, f"blob_{shape}"))
                items.append((im.filter(ImageFilter.GaussianBlur(12)), f"blob_{shape}_blur"))

    for i in range(6):
        a = np.linspace(0, 255, 400, dtype=np.uint8)[:, None].repeat(400, 1)
        items.append((Image.fromarray(np.stack([a, np.roll(a, i * 40), 255 - a], -1)), "gradient"))

    return items


def quantiles(a):
    return " ".join(f"p{p}={np.percentile(a, p):.3f}" for p in (0, 1, 5, 50, 100))


def main():
    ap = argparse.ArgumentParser(description="눈 OOD 게이트 임계값 실측")
    ap.add_argument("--dataset", default="dataset", help="0_normal / 1_cataract 를 담은 폴더")
    ap.add_argument("--centroid", default=os.path.join("app", "models", "eye_centroid.npy"))
    ap.add_argument("--n", type=int, default=300, help="클래스별 표본 수")
    ap.add_argument("--extra-non-eye", default=None, help="실제 비-눈 사진 폴더(선택)")
    ap.add_argument("--seed", type=int, default=20260829)
    args = ap.parse_args()

    if not os.path.exists(args.centroid):
        sys.exit(f"centroid가 없습니다: {args.centroid}\n"
                 f"먼저 scripts/build_eye_centroid.py로 생성하세요.")

    rng = random.Random(args.seed)
    net = build_backbone()
    centroid = np.load(args.centroid).astype(np.float32)
    centroid /= (np.linalg.norm(centroid) + 1e-8)

    pos = []
    for sub in ("0_normal", "1_cataract"):
        paths = sample_dir(os.path.join(args.dataset, sub), args.n, rng)
        if not paths:
            print(f"[경고] {sub}: 이미지가 없습니다 — 건너뜁니다.")
            continue
        s = score_paths(net, centroid, paths)
        pos.append(s)
        print(f"[눈/{sub}] n={len(paths)}  {quantiles(s)}")
    if not pos:
        sys.exit("눈 표본이 없어 임계값을 평가할 수 없습니다. --dataset 경로를 확인하세요.")
    pos = np.concatenate(pos)

    items = synthetic_non_eye(rng)
    neg = score_images(net, centroid, [im for im, _ in items])
    labels = [lab for _, lab in items]

    if args.extra_non_eye:
        extra = sample_dir(args.extra_non_eye, 10_000, rng)
        if extra:
            neg = np.concatenate([neg, score_paths(net, centroid, extra)])
            labels += ["real_non_eye"] * len(extra)
            print(f"[비-눈] 실제 사진 {len(extra)}장 추가")

    print(f"[비-눈] n={len(neg)}  {quantiles(neg)}")

    print("\n비-눈 계열별 최고 점수 (높을수록 게이트를 뚫기 쉬움):")
    by = {}
    for lab, sc in zip(labels, neg):
        by.setdefault(lab, []).append(float(sc))
    for lab in sorted(by, key=lambda k: -max(by[k])):
        print(f"  {lab:22s} max={max(by[lab]):.3f}  n={len(by[lab])}")

    print("\n임계값   눈 거부(FN)          비-눈 통과(FP)")
    for th in THRESHOLD_CANDIDATES:
        fn, fp = (pos < th), (neg >= th)
        print(f"  {th:.2f}   {fn.sum():4d}/{len(pos):<4d} ({fn.mean() * 100:5.2f}%)"
              f"   {fp.sum():4d}/{len(neg):<4d} ({fp.mean() * 100:5.2f}%)")

    print("\n해석: 눈 거부는 사용자가 정상 사진을 올렸는데 '눈이 아니다'로 막히는 비율,")
    print("      비-눈 통과는 엉뚱한 사진에 의료 결과가 나가는 비율이다.")
    print("      양성 표본은 centroid를 만든 데이터셋과 같은 분포라 낙관적으로 나온다 —")
    print("      실사용 사진의 오거부가 보고되면 --extra-non-eye와 실제 눈 사진으로 재실측할 것.")


if __name__ == "__main__":
    main()
