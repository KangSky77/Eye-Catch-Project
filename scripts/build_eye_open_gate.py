"""얼굴 모드 눈 크롭의 '눈 뜸 여부' 판정기 학습 — app/models/eye_open_gate.npz 생성
================================================================================
왜 따로 두는가 (2026-09-13 실측):
    AI로 만든 감은 눈 얼굴 3장이 눈 게이트를 0.897~0.978로 통과해 '혼탁 특징 없음 0/100'이 나갔다.
    실제 사진(Commons 수면·명상 범주)에서도 같았다 — 학습에 쓰지 않은 감은 눈 크롭 56개 중 58.9%가
    임계 0.60을 통과했다.

    처음에는 기존 눈 게이트에 감은 눈을 음성으로 더해 재학습했다(build_eye_gate.py). 감은 눈 통과는
    21.4%로 줄었지만 정상 눈 거부가 4.7% → 6.3%로 늘었고, AI 감은 눈은 여전히 0.77~0.93으로 통과했다.
    '눈이 아닌 사진'과 '감은 눈'을 한 판정기에 같이 가르치면 서로 부딪힌다. 그래서 질문을 나눈다:
        눈 게이트        — 이 크롭이 눈 영역인가 (그대로 둔다)
        뜸 여부 판정기    — 눈 영역이라면, 홍채·동공이 보이게 뜨고 있는가 (이 스크립트)

데이터 (모두 Wikimedia Commons 자유 라이선스, 사진은 git 제외, 크롭은 사람이 검수):
    양성 = dataset_openeye/review.json "open" + dataset_closedeye/review.json "excluded_open_eye"
    음성 = dataset_closedeye/review.json "closed"
    각 폴더의 split.json(근접중복 묶음 단위)을 따라 학습/평가를 나눈다.

입력 특징: ImageNet ResNet18(눈 게이트와 같은 백본)의
    A) 마지막 512  B) A + layer3 전체평균 256
    D) B + layer3 중앙평균 256 + layer4 중앙평균 512   ← 채택
    (각 부분은 따로 L2 정규화 후 이어 붙인다. 중앙평균 = 특징 지도 가운데 50% 영역의 평균)

    왜 D인가 (2026-09-13, 뜬 눈 평가 123 / 감은 눈 평가 73, 뜬 눈 99% 통과 기준):
        감은 눈 거부   A 54.8%  B 57.5%  D 91.8%
        앱 흐름(눈 게이트∧판정기)에서 감은 눈 통과: 게이트만 52.1% → D 6.8%, 뜬 눈 추가 거부 0%p
    전체 평균은 '가운데에 동공과 흰자가 있는가'라는 위치 정보를 지운다. 크롭은 MTCNN이 눈 중심에
    맞춰 자르므로 중앙 영역만 따로 보면 뜸·감음이 훨씬 잘 갈린다.

임계값: 평가 표본의 뜬 눈이 TARGET_OPEN_PASS 이상 통과하는 가장 높은 값.
    이 판정기는 실제 사용자의 뜬 눈을 거부하면 앱 전체가 막히므로 뜬 눈 통과를 먼저 지킨다.

실행:  python scripts/build_eye_open_gate.py --compare            # A/B 비교만
       python scripts/build_eye_open_gate.py --features B --out app/models/eye_open_gate.npz
"""
import argparse, json, random, sys
from pathlib import Path
import numpy as np
import torch
from PIL import Image, ImageOps, ImageEnhance
from torchvision import models, transforms

ROOT = Path(__file__).resolve().parents[1]
SEED = 20260913
TARGET_OPEN_PASS = 0.99
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
preprocess = transforms.Compose([
    transforms.Resize((224, 224)), transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def load_split(folder: str, key: str, split: str) -> list[Path]:
    d = ROOT / folder
    review, sp = d / "review.json", d / "split.json"
    if not (review.exists() and sp.exists()):
        return []
    stems = {Path(n).stem for n in json.loads(sp.read_text(encoding="utf-8"))[split]}
    names = json.loads(review.read_text(encoding="utf-8")).get(key, [])
    return [d / "crops" / n for n in names if n.split("__f")[0] in stems and (d / "crops" / n).exists()]


def open_rgb(p):
    with Image.open(p) as im:
        return ImageOps.exif_transpose(im).convert("RGB")


def center_mean(fmap, frac=0.5):
    """특징 지도 가운데 frac 영역의 평균. app/services/eye_validator.py의 _center_mean과 반드시 같아야 한다."""
    h, w = fmap.shape[2:]
    ch, cw = max(1, int(h * frac)), max(1, int(w * frac))
    y, x = (h - ch) // 2, (w - cw) // 2
    return fmap[:, :, y:y + ch, x:x + cw].mean(dim=(2, 3))


class Backbone(torch.nn.Module):
    def __init__(self):
        super().__init__()
        net = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        net.fc = torch.nn.Identity()
        self.net = net.eval().to(device)
        self._l3 = self._l4 = None
        self.net.layer3.register_forward_hook(lambda m, i, o: setattr(self, "_l3", o))
        self.net.layer4.register_forward_hook(lambda m, i, o: setattr(self, "_l4", o))

    @torch.no_grad()
    def features(self, imgs, kind, bs=64):
        out = []
        for i in range(0, len(imgs), bs):
            x = torch.stack([preprocess(im) for im in imgs[i:i + bs]]).to(device)
            last = torch.nn.functional.normalize(self.net(x), dim=1)
            if kind == "A":
                out.append(last.cpu())
                continue
            l3 = torch.nn.functional.normalize(self._l3.mean(dim=(2, 3)), dim=1)
            if kind == "B":
                out.append(torch.cat([last, l3], dim=1).cpu())
                continue
            l3c = torch.nn.functional.normalize(center_mean(self._l3), dim=1)
            l4c = torch.nn.functional.normalize(center_mean(self._l4), dim=1)
            out.append(torch.cat([last, l3, l3c, l4c], dim=1).cpu())
        return torch.cat(out)


def augment(imgs):
    """학습 쪽만: 좌우반전·밝기 변형. 얼굴 사진 눈 크롭의 좌우·조명 변화를 흉내 낸다."""
    out = []
    for im in imgs:
        out += [im, im.transpose(Image.FLIP_LEFT_RIGHT),
                ImageEnhance.Brightness(im).enhance(0.75), ImageEnhance.Brightness(im).enhance(1.25)]
    return out


def train(Xtr, ytr):
    w = torch.zeros(Xtr.shape[1], requires_grad=True); b = torch.zeros(1, requires_grad=True)
    opt = torch.optim.Adam([w, b], lr=0.05, weight_decay=1e-3)
    pos_w = torch.tensor(float((ytr == 0).sum()) / max(1.0, float((ytr == 1).sum())))
    for _ in range(800):
        opt.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(Xtr @ w + b, ytr, pos_weight=pos_w)
        loss.backward(); opt.step()
    return w.detach(), b.detach()


def run(kind, bb, data):
    tr_open, tr_closed, ho_open, ho_closed = data
    Xtr = torch.cat([bb.features(augment(tr_open), kind), bb.features(augment(tr_closed), kind)])
    ytr = torch.cat([torch.ones(len(tr_open) * 4), torch.zeros(len(tr_closed) * 4)])
    w, b = train(Xtr, ytr)
    po = torch.sigmoid(bb.features(ho_open, kind) @ w + b)
    pc = torch.sigmoid(bb.features(ho_closed, kind) @ w + b)
    srt = torch.sort(po).values
    thr = float(srt[int((1 - TARGET_OPEN_PASS) * len(srt))]) if len(srt) else 0.5
    open_pass = float((po >= thr).float().mean()); closed_rej = float((pc < thr).float().mean())
    return {"w": w, "b": b, "thr": thr, "open_pass": open_pass, "closed_reject": closed_rej,
            "po": po, "pc": pc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--features", choices=["A", "B", "D"], default="D")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    random.seed(SEED); torch.manual_seed(SEED)

    tr_open = load_split("dataset_openeye", "open", "train") + load_split("dataset_closedeye", "excluded_open_eye", "train")
    ho_open = load_split("dataset_openeye", "open", "holdout") + load_split("dataset_closedeye", "excluded_open_eye", "holdout")
    tr_closed = load_split("dataset_closedeye", "closed", "train")
    ho_closed = load_split("dataset_closedeye", "closed", "holdout")
    print(f"뜬 눈: 학습 {len(tr_open)} / 평가 {len(ho_open)}   감은 눈: 학습 {len(tr_closed)} / 평가 {len(ho_closed)}  (device {device})")
    if min(len(tr_open), len(tr_closed), len(ho_open), len(ho_closed)) < 20:
        raise SystemExit("검수된 크롭이 부족하다 — review.json·split.json을 먼저 만들 것")
    data = tuple([open_rgb(p) for p in ps] for ps in (tr_open, tr_closed, ho_open, ho_closed))
    bb = Backbone()
    kinds = ["A", "B", "D"] if args.compare else [args.features]
    results = {}
    for k in kinds:
        r = run(k, bb, data); results[k] = r
        name = {"A": "마지막층 512", "B": "마지막층 + layer3 전체", "D": "B + layer3·layer4 중앙"}[k]
        print(f"  [{k}] {name:24s} 임계 {r['thr']:.3f}  뜬 눈 통과 {r['open_pass']*100:5.1f}%  감은 눈 거부 {r['closed_reject']*100:5.1f}%")
    if args.compare or not args.out:
        return
    r = results[args.features]
    meta = {"trained": "2026-09-13", "seed": SEED, "features": args.features,
            "backbone": "resnet18 IMAGENET1K_V1; A=L2(final512) B=A+L2(GAP layer3) D=B+L2(center50% layer3)+L2(center50% layer4)",
            "n_train_open": len(tr_open), "n_train_closed": len(tr_closed),
            "n_holdout_open": len(ho_open), "n_holdout_closed": len(ho_closed),
            "holdout_open_pass": r["open_pass"], "holdout_closed_reject": r["closed_reject"],
            "threshold": r["thr"], "target_open_pass": TARGET_OPEN_PASS,
            "data": "Wikimedia Commons free-license photos; see dataset_openeye/ and dataset_closedeye/ ATTRIBUTION.csv"}
    np.savez(args.out, w=r["w"].numpy().astype(np.float32), b=r["b"].numpy().astype(np.float32),
             threshold=np.float32(r["thr"]), features=np.array(args.features), meta=json.dumps(meta, ensure_ascii=False))
    print(f"💾 저장: {args.out}")


if __name__ == "__main__":
    main()
