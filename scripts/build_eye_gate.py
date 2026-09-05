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

실행:  python scripts/build_eye_gate.py                    # 학습 + 홀드아웃 평가 + 저장
       python scripts/build_eye_gate.py --dry-run          # 저장하지 않음
       python scripts/build_eye_gate.py --out cand.npz     # 배포본과 비교할 후보만 뽑기
출력:  app/models/eye_gate.npz (w, b, threshold, meta)

────────────────────────────────────────────────────────────────────
2026-09-05 재학습 시도 — 스크립트는 고쳤고, 가중치는 채택하지 않았다
────────────────────────────────────────────────────────────────────
고친 것 (이 파일에 반영됨):
  1) 음성 라벨 오류. EXTRA_NEG_DIRS = ["static/assets"]로 폴더를 통째로 넣는 바람에
     diseases/cataract-clinical.jpg(교과서적인 백내장 눈 클로즈업)가 '눈이 아님'으로
     학습됐다. 표본을 늘리자 재학습본의 비-눈 최고점이 0.992까지 튀어 드러났다.
     → NON_EYE_ASSETS 명시 목록으로 교체(파일마다 눈으로 확인).
  2) 음성 구성 불균형. '가려진 눈' 45% + '눈 모서리' 45%인데 '임의의 사진'은 0.6%뿐이라,
     분류기가 건물·풍경 사진을 사실상 배우지 못했다. → 격자 크롭 + 증강으로 4.7%까지.
  3) 계열별 거부율 보고가 인덱스 계산이라 틀렸다(배열이 이미지마다 섞여 있었다).
     → 라벨을 실제로 들고 다닌다.

채택하지 않은 이유:
  같은 감사 표본(비-눈 136개)에서 후보가 배포본보다 나아 보인다.
      지표(정상 눈 거부 5.3%로 고정)    배포본    재학습 후보
      비-눈 최고점                      0.612      0.277
      비-눈 통과                        0.0%       0.0%
      백내장 눈 거부                    1.0%       1.3%
  그런데 그 감사 표본은 후보가 학습에 쓴 것과 **같은 사진 세 장**에서 잘라낸 것이다.
  후보의 우위는 일반화가 아니라 암기일 수 있고, 이 표본으로는 둘을 구분할 수 없다.
  여기서 후보를 채택하고 "최고점이 0.277이니 임계값을 0.40으로 낮춰도 된다"고 하면,
  방금 고친 실수(특정 사진에 맞춰 임계값을 정하는 것)를 그대로 반복하게 된다.
  게다가 운영 임계값 0.65에서 백내장 눈 거부는 후보가 오히려 조금 나쁘다.

다음에 할 일:
  실사용 오입력 사진(인물·음식·문서·손·화면 캡처·풍경 등)을 모아 NON_EYE_ASSETS에 넣고,
  그중 일부를 **학습에 쓰지 않고 따로 빼서** 평가용으로 남긴다. 그때 비로소
  "처음 보는 종류의 사진을 막는가"를 답할 수 있고, 임계값도 근거를 갖고 내릴 수 있다.
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
# 음성으로 쓸 '눈이 아닌 사진' — 파일을 하나씩 눈으로 확인하고 적는다.
#
# ⚠️ 폴더 통째로(예: "static/assets" 전부) 넣으면 안 된다. 실제로 그렇게 했다가
#    diseases/cataract-clinical.jpg(교과서적인 백내장 눈 클로즈업)와
#    glaucoma-clinical.jpg가 음성으로 들어갔다. 앱이 반드시 받아들여야 할 사진을
#    '눈이 아니다'라고 가르친 셈이라, 재학습본의 비-눈 최고점이 0.992까지 올라갔다
#    (2026-09-05 실측). 크롭 12개일 때는 노이즈였지만 표본을 늘리자 드러났다.
#
# 안저(fundus) 사진은 여기 포함한다 — 눈 안쪽 망막 사진이라 이 앱의 사진 분석 대상이
# 아니고, 게이트가 거부하는 것이 맞다(README '모델의 한계' 5번 참고).
NON_EYE_ASSETS = [
    "static/assets/vision-scene.jpg",                          # 도서관 외경(건물·하늘·나무)
    "static/assets/diseases/amd-fundus.jpg",                   # 안저 — 외안부 아님
    "static/assets/diseases/diabetic-retinopathy-fundus.jpg",  # 안저 — 외안부 아님
]

# Wikimedia Commons에서 모은 비-눈 사진 폴더(git 제외 — dataset/과 같은 취급).
# scripts/fetch_non_eye_photos.py로 받고, split.json이 사진 단위로 학습/평가를 나눈다.
#
# 왜 '사진 단위'인가: 같은 사진의 크롭이 학습과 평가 양쪽에 들어가면, 평가 점수가
# 일반화가 아니라 암기를 재게 된다. 실제로 저장소 사진 세 장만으로 재학습했을 때
# 감사 점수가 크게 좋아 보였지만 그 표본이 학습에 쓰인 사진에서 나온 것이라
# 채택할 수 없었다(위 '2026-09-05 재학습 시도' 참고). 이 폴더는 그 문제를 없앤다.
NON_EYE_DIR = REPO_ROOT / "dataset_noneye"
NON_EYE_SPLIT = NON_EYE_DIR / "split.json"
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


def grid_crops(im):
    """격자 크롭 — 임의 크롭이 놓치는 영역까지 결정적으로 덮는다.

    왜 필요한가: 도서관 사진을 3x3으로 잘랐을 때 상단 중앙 조각(건물 옥상 + 하늘)이
    게이트를 0.61로 통과했다. 그 사진 자체는 이미 음성 폴더에 있었는데, 임의 크롭
    12개가 하필 그 영역을 비껴갔던 것이다. 격자로 훑으면 그런 구멍이 남지 않는다.
    """
    w, h = im.size
    outs = [im]
    for g in (2, 3, 4):
        for gy in range(g):
            for gx in range(g):
                outs.append(im.crop((gx * w // g, gy * h // g,
                                     (gx + 1) * w // g, (gy + 1) * h // g)))
    for z in (0.4, 0.55, 0.7):
        cw, ch = int(w * z), int(h * z)
        outs.append(im.crop(((w - cw) // 2, (h - ch) // 2, (w - cw) // 2 + cw, (h - ch) // 2 + ch)))
    return outs


def non_eye_photo_paths(split: str) -> list[Path]:
    """비-눈 사진 경로. split은 'train' 또는 'holdout'.

    dataset_noneye/split.json이 사진 단위로 갈라 놓은 목록을 그대로 따른다.
    폴더가 없으면(사진을 아직 안 받았으면) 저장소 기본 세 장만 쓴다 —
    scripts/fetch_non_eye_photos.py로 받으면 자동으로 늘어난다.
    """
    paths = [REPO_ROOT / p for p in NON_EYE_ASSETS if (REPO_ROOT / p).exists()]
    if not NON_EYE_SPLIT.exists():
        if split == "train":
            print(f"  ⚠️ {NON_EYE_SPLIT} 없음 — 저장소 기본 {len(paths)}장만 사용")
            print("     python scripts/fetch_non_eye_photos.py 로 실제 사진을 받으세요.")
        return paths if split == "train" else []
    names = json.loads(NON_EYE_SPLIT.read_text(encoding="utf-8"))[split]
    extra = [NON_EYE_DIR / n for n in names if (NON_EYE_DIR / n).exists()]
    # 저장소 기본 세 장은 학습 쪽에만 넣는다(평가는 새로 받은 사진으로만 한다)
    return (paths + extra) if split == "train" else extra


def photo_negatives(rng, split="train"):
    """'눈이 아닌 임의의 사진'을 음성으로 모은다.

    왜 이 함수가 생겼나 (2026-09-05):
        기존 음성 구성은 가려진 눈 45% / 눈 모서리 45%였고, 실제 사진 크롭은 0.6%뿐이었다.
        그래서 분류기는 '가려진 눈'과 '눈꺼풀'을 거부하도록만 배웠고, 건물·풍경 사진은
        배운 적이 거의 없었다 — 도서관 사진이 통과한 진짜 이유다.

    사진마다 격자 크롭(2x2·3x3·4x4·중앙확대)과 임의 크롭을 함께 쓴다. 격자는 임의 크롭이
    비껴갈 수 있는 영역을 결정적으로 덮는다(옥상 조각이 그렇게 빠져 있었다).
    """
    outs = []
    for p in non_eye_photo_paths(split):
        im = open_rgb(p)
        n_random = 60 if len(non_eye_photo_paths(split)) < 10 else 8
        base = grid_crops(im) + random_crops(im, rng, n_random, frac=(0.15, 0.7))
        for c in base:
            outs.append(c)
            if rng.random() < 0.4:
                outs.append(c.transpose(Image.FLIP_LEFT_RIGHT))

    # 합성 계열 — probe_eye_gate.py와 같은 것을 재사용한다(학습 쪽에만).
    # blob 계열은 실제로 게이트를 통과했던 모양이라 학습 음성에 반드시 넣는다.
    if split == "train":
        import importlib.util
        spec = importlib.util.spec_from_file_location("probe", REPO_ROOT / "scripts" / "probe_eye_gate.py")
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        outs += [img for img, _ in probe.synthetic_non_eye(random.Random(SEED))]
    return outs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    # 새 가중치를 배포본과 나란히 비교한 뒤에 채택하려면 임시 경로로 뽑는다
    ap.add_argument("--out", default=None, help="저장 경로(기본: app/models/eye_gate.npz)")
    args = ap.parse_args()
    out_path = Path(args.out) if args.out else OUT_PATH
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
        """(양성, 음성, 음성계열라벨) 반환.

        계열 라벨을 함께 만드는 이유: 예전에는 '가려진 눈이 앞에 n*4개, 모서리가 그다음
        n*2개'라고 가정하고 인덱스로 잘라 계열별 거부율을 냈는데, 실제 배열은 이미지마다
        가려진눈·모서리가 번갈아 들어가서 그 구간이 두 계열의 혼합이었다. 보고 숫자가
        틀리면 어느 계열이 약한지 알 수 없다 — 라벨을 실제로 들고 다닌다.
        """
        pos, neg, fam = [], [], []
        for p in fs:
            im = open_rgb(p)
            pos.append(im)
            covered = covered_variants(im, rng)[:2] if tag == "train" else covered_variants(im, rng)
            neg += covered;                fam += ["가려진 눈"] * len(covered)
            corners = corner_crops(im, rng)[:2]
            neg += corners;                fam += ["모서리 피부"] * len(corners)
        # 단색·노이즈
        for _ in range(max(60, len(fs) // 20)):
            c = tuple(int(v) for v in rng.integers(0, 256, 3))
            neg.append(Image.new("RGB", (224, 224), c));                       fam.append("단색·노이즈")
            neg.append(Image.fromarray(rng.integers(0, 255, (224, 224, 3), dtype=np.uint8))); fam.append("단색·노이즈")
        # '눈이 아닌 임의의 사진' — 예전에는 임의 크롭 12개뿐이라 음성의 0.6%였고,
        # 그래서 분류기가 이 부류를 사실상 배우지 못했다. 격자+증강으로 충분히 넣는다.
        photos = photo_negatives(rng, "train" if tag == "train" else "holdout")
        neg += photos;                     fam += ["비-눈 사진"] * len(photos)
        return pos, neg, fam

    net = load_backbone()
    tr_pos, tr_neg, tr_fam = build(train_files, "train")
    ho_pos, ho_neg, ho_fam = build(hold_files, "hold")
    from collections import Counter
    print(f"학습: 양성 {len(tr_pos)} / 음성 {len(tr_neg)}   홀드아웃: 양성 {len(ho_pos)} / 음성 {len(ho_neg)}")
    print("  학습 음성 구성: " + ", ".join(f"{k} {v}({v/len(tr_neg):.1%})"
                                      for k, v in Counter(tr_fam).most_common()))
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
        neg_p = p_ho[yho == 0]
        by_family = {}
        for family in dict.fromkeys(ho_fam):
            idx = [i for i, f in enumerate(ho_fam) if f == family]
            sel = neg_p[idx]
            by_family[family] = {"n": len(idx),
                                 "reject": float((sel < thr).float().mean()),
                                 "max": float(sel.max())}
    print()
    print(f"홀드아웃 — 임계값 {thr:.3f}: 눈 통과 {pos_pass*100:.2f}% | 음성 거부 {neg_rej*100:.1f}%")
    for family, r in by_family.items():
        print(f"    {family:12s} n={r['n']:5d}  거부 {r['reject']*100:5.1f}%  최고점 {r['max']:.3f}")

    meta = {"trained": "2026-09-05", "seed": SEED, "n_train_pos": len(tr_pos), "n_train_neg": len(tr_neg),
            "holdout_pos_pass": pos_pass, "holdout_neg_reject": neg_rej, "threshold": thr,
            "holdout_by_family": {k: round(v["reject"], 4) for k, v in by_family.items()},
            "backbone": "resnet18 IMAGENET1K_V1, fc=Identity, L2-normalized 512-d"}
    if args.dry_run:
        print("(dry-run: 저장하지 않음)"); return
    np.savez(out_path, w=w.detach().numpy().astype(np.float32), b=b.detach().numpy().astype(np.float32),
             threshold=np.float32(thr), meta=json.dumps(meta, ensure_ascii=False))
    print(f"💾 저장: {out_path}  {json.dumps(meta, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
