"""
눈 검증기(OOD 게이트)의 기준 벡터 생성 스크립트
================================================================
app/services/eye_validator.py는 app/models/eye_centroid.npy를 **읽기만** 하는데,
그 파일을 만드는 코드가 저장소에 없었다. dataset/은 .gitignore이고 centroid는 .npy
바이너리라, "왜 임계값이 0.55인가"를 재현할 방법이 없는 상태였다.
이 스크립트가 그 공백을 메운다.

무엇을 만드나:
    ImageNet 사전학습 ResNet18(fc=Identity, 512-dim)로 데이터셋의 눈 사진을 전부
    임베딩하고, 각 벡터를 L2 정규화한 뒤 평균 → 다시 정규화한 것이 centroid다.
    (정상·백내장 둘 다 '눈'이므로 두 클래스를 함께 쓴다 — eye_validator.py 주석 참고)

    전처리·백본·정규화는 eye_validator.py와 반드시 동일해야 한다. 어긋나면 유사도
    분포가 통째로 밀려서 임계값이 의미를 잃는다. 아래 상수는 그쪽에서 그대로 가져온다.

임계값 근거도 같이 뽑는다:
    --non-eye 폴더를 주면 '눈 최소 유사도'와 '비-눈 최대 유사도'를 함께 출력해,
    config.py의 eye_sim_threshold(현재 0.55)가 그 사이에 있는지 확인할 수 있다.

기본적으로 덮어쓰지 않는다:
    배포 중인 centroid를 말없이 갈아치우면 의료 게이트의 동작이 조용히 바뀐다.
    기본 출력은 별도 파일이고, 기존 파일이 있으면 코사인 유사도로 비교만 해준다.
    실제로 교체하려면 --overwrite 를 명시할 것.

⚠️ 알려진 사실: 현재 배포본은 이 레시피로 재현되지 않는다 (2026-08-19 측정)
    dataset 17,017장 전체로 계산한 centroid와 배포본의 코사인 유사도는 0.976이다.
    부분집합 가설은 전부 기각됐다:
      전체 0.976 / brightiris 201장 제외(v4 시점) 0.975 / 0_normal만 0.963 / 1_cataract만 0.960
    표본 크기 문제도 아니다 — 무작위 100장만 써도 전체 centroid를 cos 0.998로 재현하므로,
    0.976은 "표본이 작아서"로 설명되지 않는다. 배포본은 다른 전처리(크롭 여부 등)나
    다른 이미지 집합으로 만들어진 것으로 보이며, 그 과정이 기록돼 있지 않다.
    → 이 스크립트는 "앞으로의 재현성"을 위한 것이고, 배포본을 교체하는 용도가 아니다.

    배포본을 그대로 두는 근거(측정치): 배포 centroid + 임계값 0.55 기준으로 데이터셋의
    눈 사진 15/17,017장(0.09%)만 '눈 아님'으로 거부된다. 밝은 홍채 201장은 최소 유사도가
    0.576으로 전부 통과한다. 즉 현재 게이트는 실측상 잘 동작하고 있다.

    교체하려면 반드시 --non-eye 로 임계값을 다시 구하고 config.py의 eye_sim_threshold를
    같이 갱신할 것 — centroid가 바뀌면 0.55는 더 이상 같은 의미가 아니다.

실행:
    python build_eye_centroid.py                          # 계산 + 기존 파일과 비교만
    python build_eye_centroid.py --non-eye real_photos/non_eye
    python build_eye_centroid.py --overwrite              # app/models/eye_centroid.npy 교체
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageFile, ImageOps
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

ImageFile.LOAD_TRUNCATED_IMAGES = True

DATA_DIR = Path("dataset")
EYE_CLASSES = ["0_normal", "1_cataract"]      # 둘 다 '눈 클로즈업'이므로 함께 사용
CANONICAL_OUT = Path("app/models/eye_centroid.npy")
DEFAULT_OUT = Path("eye_centroid.new.npy")
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# ⚠️ eye_validator.py와 동일해야 함 (바뀌면 양쪽을 같이 고칠 것)
NORM_MEAN = [0.485, 0.456, 0.406]
NORM_STD = [0.229, 0.224, 0.225]
IMG_SIZE = 224

_preprocess = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(NORM_MEAN, NORM_STD),
])


class ImageList(Dataset):
    """경로 리스트 → 전처리된 텐서. 읽기 실패한 파일은 0 텐서 + 플래그로 표시해 건너뛴다."""

    def __init__(self, paths: list[Path]):
        self.paths = paths

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, i):
        try:
            with Image.open(self.paths[i]) as im:
                return _preprocess(ImageOps.exif_transpose(im.convert("RGB"))), True
        except Exception:
            return torch.zeros(3, IMG_SIZE, IMG_SIZE), False


def collect(folder: Path) -> list[Path]:
    return sorted(f for f in folder.rglob("*") if f.is_file() and f.suffix.lower() in IMG_EXTS)


def build_net(device):
    """eye_validator._try_load()와 동일한 백본 구성."""
    net = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    net.fc = torch.nn.Identity()
    return net.eval().to(device)


@torch.no_grad()
def embed(net, paths: list[Path], device, batch: int, workers: int, label: str) -> np.ndarray:
    """L2 정규화된 임베딩 (N, 512) 반환."""
    loader = DataLoader(ImageList(paths), batch_size=batch, shuffle=False,
                        num_workers=workers, pin_memory=(device.type == "cuda"))
    out, done, skipped = [], 0, 0
    for x, ok in loader:
        feats = net(x.to(device))
        feats = feats / (feats.norm(dim=1, keepdim=True) + 1e-8)
        out.append(feats[ok.to(device)].cpu().numpy())
        done += len(x)
        skipped += int((~ok).sum())
        print(f"  [{label}] {done}/{len(paths)}", end="\r")
    print(f"  [{label}] {done}/{len(paths)} 완료" + (f" (읽기 실패 {skipped}장 제외)" if skipped else ""))
    return np.concatenate(out) if out else np.zeros((0, 512), dtype=np.float32)


def describe(sims: np.ndarray, label: str):
    q = np.percentile(sims, [0, 1, 5, 50, 95, 99, 100])
    print(f"  {label:8s} n={len(sims):6d}  최소 {q[0]:.3f} | p1 {q[1]:.3f} | p5 {q[2]:.3f} | "
          f"중앙 {q[3]:.3f} | p95 {q[4]:.3f} | p99 {q[5]:.3f} | 최대 {q[6]:.3f}")


def main():
    ap = argparse.ArgumentParser(description="눈 검증기 centroid 생성")
    ap.add_argument("--data", default=str(DATA_DIR), help="데이터셋 폴더 (기본: dataset)")
    ap.add_argument("--non-eye", default=None, help="비-눈 사진 폴더(선택) — 임계값 근거 산출용")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help=f"출력 경로 (기본: {DEFAULT_OUT})")
    ap.add_argument("--overwrite", action="store_true",
                    help=f"배포 파일({CANONICAL_OUT})을 직접 교체 — 의료 게이트 동작이 바뀌므로 명시적으로만")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="클래스당 N장만 사용(빠른 점검용)")
    ap.add_argument("--device", default=None, choices=["cuda", "cpu"])
    args = ap.parse_args()

    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    data_dir = Path(args.data)
    if not data_dir.is_dir():
        raise SystemExit(f"❌ 데이터 폴더가 없습니다: {data_dir}")

    paths: list[Path] = []
    for cls in EYE_CLASSES:
        d = data_dir / cls
        if not d.is_dir():
            raise SystemExit(f"❌ 클래스 폴더가 없습니다: {d}")
        p = collect(d)
        if args.limit:
            p = p[: args.limit]
        print(f"{cls}: {len(p)}장")
        paths += p
    if not paths:
        raise SystemExit("❌ 이미지가 없습니다.")

    print(f"\n임베딩 계산 중 (device={device.type}, batch={args.batch})...")
    net = build_net(device)
    feats = embed(net, paths, device, args.batch, args.workers, "eye")

    centroid = feats.mean(axis=0)
    centroid = centroid / (np.linalg.norm(centroid) + 1e-8)

    print("\n=== 유사도 분포 ===")
    eye_sims = feats @ centroid
    describe(eye_sims, "눈")

    non_eye_sims = None
    if args.non_eye:
        ne_dir = Path(args.non_eye)
        if not ne_dir.is_dir():
            raise SystemExit(f"❌ 비-눈 폴더가 없습니다: {ne_dir}")
        ne_paths = collect(ne_dir)
        print(f"\n비-눈 {len(ne_paths)}장 임베딩 중...")
        ne_feats = embed(net, ne_paths, device, args.batch, args.workers, "non-eye")
        non_eye_sims = ne_feats @ centroid
        describe(non_eye_sims, "비-눈")

        lo, hi = float(eye_sims.min()), float(non_eye_sims.max())
        print(f"\n분리 구간: 비-눈 최대 {hi:.3f}  <  눈 최소 {lo:.3f}" if hi < lo else
              f"\n⚠️  겹침: 비-눈 최대 {hi:.3f} >= 눈 최소 {lo:.3f} — 완전 분리 불가")
        if hi < lo:
            print(f"→ 권장 임계값(중간값): {(lo + hi) / 2:.3f}  "
                  f"(config.py의 eye_sim_threshold와 비교할 것)")
    else:
        print("\n(--non-eye 폴더를 주면 임계값 근거까지 계산합니다)")

    # 기존 배포본과 비교 — 같은 레시피로 재현되는지 확인
    if CANONICAL_OUT.exists():
        old = np.load(CANONICAL_OUT).astype(np.float32)
        old = old / (np.linalg.norm(old) + 1e-8)
        cos = float(np.dot(old, centroid))
        print(f"\n=== 기존 배포본({CANONICAL_OUT}) 대비 ===")
        print(f"  코사인 유사도 {cos:.6f}  →  " +
              ("사실상 동일 (재현 확인)" if cos > 0.999 else
               "미세 차이" if cos > 0.99 else
               "⚠️  다름 — 레시피/데이터가 달라졌을 수 있으니 교체 전 확인 필요"))

    out = CANONICAL_OUT if args.overwrite else Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.save(out, centroid.astype(np.float32))
    print(f"\n💾 저장: {out}  (shape={centroid.shape}, dtype=float32)")
    if not args.overwrite:
        print(f"   배포본은 건드리지 않았습니다. 교체하려면 --overwrite 를 주세요.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # Windows cp949 콘솔 대비
    main()
