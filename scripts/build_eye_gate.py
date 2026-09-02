"""눈/비-눈 분류기(eye gate) 학습 — app/models/eye_gate.npz 생성
================================================================
왜 필요한가 (2026-09-02 실측):
    기존 게이트는 ImageNet ResNet18 임베딩과 '눈 분포 중심'의 코사인 유사도 하나로 판정했다.
    그런데 이마 0.67 / 볼 0.67 / 코 0.77 / 안저사진 0.63 / 거리 풍경 0.58이 모두 기준 0.55를
    넘어 '눈'으로 통과했고, 데이터셋 눈의 최솟값이 0.59라 기준을 올릴 여지도 없었다.
    더 심각한 것은 얼굴 사진 경로: 눈을 감았거나 선글라스·안대로 가린 얼굴도 MTCNN이 눈 위치를
    돌려주므로 피부·검정·흰색 조각이 모델에 들어가 '정상 0.0%'가 자신 있게 나갔다.

방식:
    같은 ResNet18 임베딩(512-d, L2 정규화) 위에 로지스틱 회귀 1층을 얹는다. 양성은 데이터셋 눈
    사진(정상·백내장 모두), 음성은 (a) 눈 사진의 중앙(홍채·동공 영역)을 피부색·검정·흰색·회색으로
    덮은 '가려진 눈' — 실제 실패 사례를 그대로 재현 — (b) 눈 사진의 네 모서리(눈꺼풀·속눈썹·피부)
    (c) 단색·노이즈·풍경 임의 크롭. 눈 사진은 이미지 단위로 학습/홀드아웃을 나눈다.

실행:  python scripts/build_eye_gate.py            # 학습 + 홀드아웃 평가 + 저장
       python scripts/build_eye_gate.py --dry-run  # 저장하지 않음
출력:  app/models/eye_gate.npz (w, b, threshold, meta)
"""
import os, sys, json, random, argparse
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

import numpy as np
import torch
from PIL import Image, ImageOps, ImageDraw
from torchvision import models, transforms

SEED = 7
N_POS_PER_CLASS = 1800          # 정상·백내장 각각 (총 3,600 양성)
HOLDOUT_RATIO = 0.2
OUT_PATH = Path("app/models/eye_gate.npz")
EXTRA_NEG_DIRS = ["static/assets"]   # 질환 사진·풍경 등 — 임의 크롭 음성으로 사용
TARGET_POS_RECALL = 0.997       # 홀드아웃 눈 사진의 이 비율 이상이 통과하도록 임계값 선택

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def load_backbone():
    net = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    net.fc = torch.nn.Identity()
    return net.eval().to(device)


@torch.no_grad()
def embed(net, imgs, bs=64):
    out = []
    for i in range(0, len(imgs), bs):
        x = torch.stack([preprocess(im.convert("RGB")) for im in imgs[i:i + bs]]).to(device)
        f = net(x)
        out.append(torch.nn.functional.normalize(f, dim=1).cpu())
    return torch.cat(out)


def open_rgb(p):
    with Image.open(p) as im:
        return ImageOps.exif_transpose(im.convert("RGB"))


def skin_color(im):
    a = np.asarray(im.resize((32, 32)), dtype=np.float32).reshape(-1, 3)
    return tuple(int(v) for v in np.median(a, axis=0))


def covered_variants(im, rng):
    """가려진 눈 — 중앙(홍채·동공)을 덮는다. 덮개 크기·색을 랜덤하게."""
    w, h = im.size
    outs = []
    for fill in (skin_color(im), (18, 16, 20), (238, 238, 235), (128, 128, 128)):
        v = im.copy(); d = ImageDraw.Draw(v)
        fw, fh = rng.uniform(0.45, 0.8), rng.uniform(0.3, 0.6)
        cx, cy = w * rng.uniform(0.42, 0.58), h * rng.uniform(0.42, 0.58)
        if rng.random() < 0.5:
            d.rectangle((cx - w * fw / 2, cy - h * fh / 2, cx + w * fw / 2, cy + h * fh / 2), fill=fill)
        else:
            d.ellipse((cx - w * fw / 2, cy - h * fh / 2, cx + w * fw / 2, cy + h * fh / 2), fill=fill)
        outs.append(v)
    return outs


def corner_crops(im, rng):
    w, h = im.size
    f = rng.uniform(0.28, 0.4)
    cw, ch = int(w * f), int(h * f)
    boxes = [(0, 0, cw, ch), (w - cw, 0, w, ch), (0, h - ch, cw, h), (w - cw, h - ch, w, h)]
    return [im.crop(b) for b in boxes]


def random_crops(im, rng, n, frac=(0.2, 0.6)):
    w, h = im.size; outs = []
    for _ in range(n):
        f = rng.uniform(*frac); cw, ch = max(32, int(w * f)), max(32, int(h * f))
        x, y = rng.integers(0, max(1, w - cw)), rng.integers(0, max(1, h - ch))
        outs.append(im.crop((x, y, x + cw, y + ch)))
    return outs


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); args = ap.parse_args()
    random.seed(SEED); rng = np.random.default_rng(SEED); torch.manual_seed(SEED)

    files = []
    for cls in ("0_normal", "1_cataract"):
        fs = sorted(os.listdir(f"dataset/{cls}")); random.shuffle(fs)
        files += [f"dataset/{cls}/{f}" for f in fs[:N_POS_PER_CLASS]]
    random.shuffle(files)
    n_hold = int(len(files) * HOLDOUT_RATIO)
    hold_files, train_files = files[:n_hold], files[n_hold:]
    print(f"눈 사진: 학습 {len(train_files)} / 홀드아웃 {len(hold_files)}  (device {device})")

    def build(fs, tag):
        pos, neg = [], []
        for p in fs:
            im = open_rgb(p)
            pos.append(im)
            neg += covered_variants(im, rng)[:2] if tag == "train" else covered_variants(im, rng)
            neg += corner_crops(im, rng)[:2]
        # 단색·노이즈·풍경/질환사진 임의 크롭
        for _ in range(max(60, len(fs) // 20)):
            c = tuple(int(v) for v in rng.integers(0, 256, 3)); neg.append(Image.new("RGB", (224, 224), c))
            neg.append(Image.fromarray(rng.integers(0, 255, (224, 224, 3), dtype=np.uint8)))
        for d in EXTRA_NEG_DIRS:
            for p in Path(d).rglob("*.jpg"):
                if "examples" in str(p):
                    continue          # 얼굴 예시 사진은 눈이 들어 있을 수 있어 제외
                neg += random_crops(open_rgb(p), rng, 12)
        return pos, neg

    net = load_backbone()
    tr_pos, tr_neg = build(train_files, "train")
    ho_pos, ho_neg = build(hold_files, "hold")
    print(f"학습: 양성 {len(tr_pos)} / 음성 {len(tr_neg)}   홀드아웃: 양성 {len(ho_pos)} / 음성 {len(ho_neg)}")
    Xtr = torch.cat([embed(net, tr_pos), embed(net, tr_neg)]); ytr = torch.cat([torch.ones(len(tr_pos)), torch.zeros(len(tr_neg))])
    Xho = torch.cat([embed(net, ho_pos), embed(net, ho_neg)]); yho = torch.cat([torch.ones(len(ho_pos)), torch.zeros(len(ho_neg))])

    # 로지스틱 회귀 (풀배치, 클래스 가중 균형)
    w = torch.zeros(Xtr.shape[1], requires_grad=True); b = torch.zeros(1, requires_grad=True)
    opt = torch.optim.Adam([w, b], lr=0.05, weight_decay=1e-4)
    pos_w = torch.tensor(len(tr_neg) / max(1, len(tr_pos)))
    for step in range(600):
        opt.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(Xtr @ w + b, ytr, pos_weight=pos_w)
        loss.backward(); opt.step()
    with torch.no_grad():
        p_ho = torch.sigmoid(Xho @ w + b)
        # 임계값: 홀드아웃 눈 사진의 TARGET_POS_RECALL 이상이 통과하는 가장 높은 값
        pos_scores = torch.sort(p_ho[yho == 1]).values
        thr = float(pos_scores[int((1 - TARGET_POS_RECALL) * len(pos_scores))])
        thr = min(max(thr, 0.05), 0.9)
        pos_pass = float((p_ho[yho == 1] >= thr).float().mean())
        neg_rej = float((p_ho[yho == 0] < thr).float().mean())
        # 음성 종류별 거부율 (가려진 눈 / 모서리 / 기타)
        n_cov = len(ho_pos) * 4; n_cor = len(ho_pos) * 2
        neg_p = p_ho[yho == 0]
        cov_rej = float((neg_p[:n_cov] < thr).float().mean()); cor_rej = float((neg_p[n_cov:n_cov + n_cor] < thr).float().mean())
        oth_rej = float((neg_p[n_cov + n_cor:] < thr).float().mean())
    print(f"\n홀드아웃 — 임계값 {thr:.3f}: 눈 통과 {pos_pass*100:.2f}% | 음성 거부 {neg_rej*100:.1f}% "
          f"(가려진 눈 {cov_rej*100:.1f}% / 모서리 피부 {cor_rej*100:.1f}% / 단색·노이즈·풍경 {oth_rej*100:.1f}%)")

    meta = {"trained": "2026-09-02", "seed": SEED, "n_train_pos": len(tr_pos), "n_train_neg": len(tr_neg),
            "holdout_pos_pass": pos_pass, "holdout_neg_reject": neg_rej, "threshold": thr,
            "backbone": "resnet18 IMAGENET1K_V1, fc=Identity, L2-normalized 512-d"}
    if args.dry_run:
        print("(dry-run: 저장하지 않음)"); return
    np.savez(OUT_PATH, w=w.detach().numpy().astype(np.float32), b=b.detach().numpy().astype(np.float32),
             threshold=np.float32(thr), meta=json.dumps(meta, ensure_ascii=False))
    print(f"💾 저장: {OUT_PATH}  {json.dumps(meta, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
