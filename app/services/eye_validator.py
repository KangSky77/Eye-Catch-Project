"""
눈 이미지 검증 (out-of-distribution 게이트)
==============================================
"이 사진이 정말 눈(클로즈업)인가?"를 판별해, 전혀 관계없는 사진(풍경·문서·셀카 등)에
의료 결과가 생성되는 것을 막는다.

방식: ImageNet 사전학습 ResNet18 임베딩(512-dim)과 '눈 이미지 분포의 중심(centroid)'
      코사인 유사도. 정상·백내장 눈은 모두 분포 안(유사도 높음), 비-눈은 분포 밖(낮음).
      → 음성(비-눈) 학습 데이터 없이 동작하고, 백내장 눈도 정상 눈과 함께 통과한다.
      (Haar 눈 검출은 백내장 동공을 자주 놓쳐 부적합 / 백내장 미세조정 백본은 OOD 분리 실패 — 실측 확인)

[운영 안정성]
- 성공만 캐시(_loaded=True). 일시적 로드 실패는 캐시하지 않아 다음 요청에 자동 재시도.
- 검증기를 못 쓰면 호출자가 fail-CLOSED(503으로 차단)하도록 (None, None)을 반환 —
  조용히 fail-open 해서 게이트가 무력화되는 일이 없게 한다.
- 서버 시작 시 warmup()으로 미리 로드(가중치 캐시 + 첫 요청 지연 제거).
- centroid는 dataset으로 사전 계산해 app/models/eye_centroid.npy에 저장(데이터셋 비포함 대비).
- 로드는 Lock으로 보호: warmup()과 동시에 들어온 요청이 모델을 중복 로드하지 않도록 함.
"""
import copy
import logging
import threading
from pathlib import Path

import numpy as np
import torch
from torchvision import models, transforms

from app.core.config import settings

logger = logging.getLogger(__name__)

_MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
_CENTROID_PATH = _MODEL_DIR / "eye_centroid.npy"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

_net = None          # ImageNet ResNet18 백본
_centroid = None     # 정규화된 눈 분포 중심 벡터 (게이트 파일이 없을 때의 폴백)
_loaded = False      # 성공적으로 로드된 경우에만 True (실패는 캐시하지 않음)

# 눈/비-눈 로지스틱 게이트 (scripts/build_eye_gate.py 산출물). 2026-09-02 실측: 중심 벡터 유사도는
# 이마 0.67·볼 0.67·코 0.77·안저사진 0.63·거리 풍경 0.58이 모두 기준 0.55를 넘어 '눈'으로 통과했고,
# 눈을 가린 얼굴 크롭(피부·선글라스·안대)도 0.69~0.83으로 통과했다. 같은 임베딩 위에 음성(가려진 눈·
# 모서리 피부·단색·풍경) 1.2만 장으로 학습한 1층 분류기는 홀드아웃 눈 99.7% 통과 / 음성 91.7% 거부,
# 가려진 눈 크롭 0.003~0.016(거부), 실제 눈 크롭 0.98(통과).
_GATE_PATH = _MODEL_DIR / "eye_gate.npz"
_gate_w = None       # (512,) 가중치
_gate_b = 0.0
_gate_thr = None     # 게이트 임계값 (npz에 기록된 값)
_load_lock = threading.Lock()   # 동시 요청이 모델을 중복 로드하지 않도록 보호

# 얼굴 모드 눈 크롭의 '눈 뜸 여부' 판정기 (scripts/build_eye_open_gate.py 산출물).
# 2026-09-13 실측: 감은 눈 얼굴(AI 생성 3장, Commons 수면 사진)이 위 눈 게이트를 0.9 안팎으로 통과해
# '혼탁 특징 없음'이 나갔다. 눈 게이트에 감은 눈을 음성으로 더하면 뜬 눈 거부가 늘어서, 질문을
# 나눴다 — 눈 게이트는 '눈 영역인가', 이 판정기는 '눈 영역이라면 뜨고 있는가'만 본다.
# features: "A" = L2(최종 512) / "B" = A + L2(layer3 전체평균 256)
#           "D" = B + L2(layer3 중앙평균 256) + L2(layer4 중앙평균 512)   ← 배포본
# 중앙평균은 scripts/build_eye_open_gate.py의 center_mean과 반드시 같아야 한다(학습·추론 특징 일치).
_OPEN_GATE_PATH = _MODEL_DIR / "eye_open_gate.npz"
_open_w = None
_open_b = 0.0
_open_thr = None
_open_kind = None
_layer3_out = None   # layer3 출력 (forward hook이 채운다)
_layer4_out = None   # layer4 출력
_feature_lock = threading.Lock()  # hook 출력은 요청별 계산이 끝날 때까지 보호한다

# 미세조정 판정기 (scripts/train_eye_open_cnn.py 산출물). 있으면 위 선형 판정기 대신 쓴다.
# 선형 판정기는 고정 특징 위의 선 하나라, AI로 만든 '웃으며 눈 감은 얼굴'(초승달 모양 눈꺼풀)을
# 0.345/0.357로 통과시켰다. 이 판정기는 layer4를 뜸 여부에 맞춰 다시 학습해 그 경우를 거부했고,
# 실제 인물 크롭의 추가 거부도 7개 → 5개로 줄었다(2026-09-13, docs/eye-gate-closed-eye.md).
# layer1~3은 눈 게이트와 같은 ImageNet 가중치를 공유한다 — 게이트 순전파의 layer3 출력을 받아 쓴다.
# *.pth는 git에 올리지 않는다(백내장 모델과 같은 규칙). 파일이 없으면 커밋된 선형 판정기로 동작한다.
_OPEN_CNN_PATH = _MODEL_DIR / "eye_open_cnn.pth"
_open_cnn = None
_open_cnn_thr = None


class _OpenHead(torch.nn.Module):
    """layer3 출력 → 뜸 여부 로짓. scripts/train_eye_open_cnn.py의 Head와 구조·이름이 같아야 한다."""

    def __init__(self, layer4):
        super().__init__()
        self.layer4 = layer4
        self.fc = torch.nn.Sequential(torch.nn.Dropout(0.3), torch.nn.Linear(512, 1))

    def forward(self, l3):
        return self.fc(self.layer4(l3).mean(dim=(2, 3))).squeeze(1)


def _try_load() -> bool:
    """모델·센트로이드 로드 시도. 성공 시에만 True를 캐시(실패는 다음 호출에 재시도)."""
    global _net, _centroid, _loaded, _gate_w, _gate_b, _gate_thr
    if _loaded:
        return True
    with _load_lock:
        if _loaded:   # 락을 기다리는 동안 다른 스레드가 이미 로드를 끝냈을 수 있음
            return True
        try:
            net = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
            net.fc = torch.nn.Identity()
            net.eval().to(device)
            centroid = np.load(_CENTROID_PATH).astype(np.float32)
            centroid = centroid / (np.linalg.norm(centroid) + 1e-8)
            def _keep_layer3(_module, _inputs, output):
                global _layer3_out
                _layer3_out = output
            def _keep_layer4(_module, _inputs, output):
                global _layer4_out
                _layer4_out = output
            net.layer3.register_forward_hook(_keep_layer3)
            net.layer4.register_forward_hook(_keep_layer4)
            _net = net
            _centroid = torch.from_numpy(centroid).to(device)
            if _GATE_PATH.exists():
                g = np.load(_GATE_PATH)
                _gate_w = torch.from_numpy(g["w"].astype(np.float32)).to(device)
                _gate_b = float(g["b"][0])
                _gate_thr = float(g["threshold"])
                logger.info("눈 게이트 로드: 임계값 %.3f", _gate_thr)
            else:
                logger.error("⚠️  eye_gate.npz 없음 — 검증기를 준비 완료로 취급하지 않습니다")
            _load_open_gate()
            _loaded = True
        except Exception:
            # 일시적 실패(네트워크 등)는 영구 캐시하지 않음 → 다음 요청에 재시도
            logger.warning("⚠️  눈 검증기 로드 실패(다음 요청에 재시도)", exc_info=True)
            _loaded = False
    return _loaded


def _load_open_gate() -> bool:
    """뜸 여부 판정기를 읽는다 — 미세조정 판정기가 있으면 그것을, 없으면 선형 판정기를.
    둘 다 없으면 False. 호출자가 _load_lock을 잡는다(_net이 이미 로드된 뒤에 부른다)."""
    global _open_w, _open_b, _open_thr, _open_kind, _open_cnn, _open_cnn_thr
    if _OPEN_CNN_PATH.exists():
        ck = torch.load(_OPEN_CNN_PATH, map_location=device, weights_only=True)
        head = _OpenHead(copy.deepcopy(_net.layer4))
        head.load_state_dict({k: v.float() for k, v in ck["state_dict"].items()})
        _open_cnn = head.eval().to(device)
        _open_cnn_thr = float(ck["meta"]["threshold"])
        logger.info("눈 뜸 여부 판정기(미세조정) 로드: 임계값 %.3f", _open_cnn_thr)
        return True
    if not _OPEN_GATE_PATH.exists():
        return False
    og = np.load(_OPEN_GATE_PATH)
    kind = str(og["features"])
    if kind not in ("A", "B", "D"):
        raise ValueError(f"eye_open_gate.npz features={kind!r} 알 수 없음")
    _open_w = torch.from_numpy(og["w"].astype(np.float32)).to(device)
    _open_b = float(og["b"][0])
    _open_thr = float(og["threshold"])
    _open_kind = kind
    logger.info("눈 뜸 여부 판정기 로드: 특징 %s, 임계값 %.3f", kind, _open_thr)
    return True


def warmup() -> bool:
    """서버 시작 시 호출 — 가중치를 미리 받아두고 첫 요청 지연을 없앤다."""
    ok = _try_load()
    if ok:
        logger.info("🔥 눈 검증기 준비 완료")
    else:
        logger.warning("⚠️  눈 검증기 미준비(요청 시 재시도)")
    return ok


@torch.no_grad()
def _embedding(img) -> torch.Tensor:
    # ResNet hook이 모듈 전역 변수에 layer3/layer4를 기록하므로, 다른 요청이
    # 같은 순전파를 끼워 넣지 못하게 한다. 모델 로드 락만으로는 추론 경합을 막지 못한다.
    with _feature_lock:
        x = _preprocess(img.convert("RGB")).unsqueeze(0).to(device)
        feat = _net(x)[0]
        return feat / (feat.norm() + 1e-8)


def _similarity(img) -> float:
    return float(torch.dot(_embedding(img), _centroid).item())


@torch.no_grad()
def _gate_prob(img) -> float:
    """눈일 확률(0~1) — L2 정규화 임베딩에 로지스틱 1층."""
    return float(torch.sigmoid(torch.dot(_embedding(img), _gate_w) + _gate_b).item())


def _center_mean(fmap, frac=0.5):
    """특징 지도 가운데 frac 영역의 평균 (build_eye_open_gate.center_mean과 동일)."""
    h, w = fmap.shape[2:]
    ch, cw = max(1, int(h * frac)), max(1, int(w * frac))
    y, x = (h - ch) // 2, (w - cw) // 2
    return fmap[:, :, y:y + ch, x:x + cw].mean(dim=(2, 3))


@torch.no_grad()
def _open_prob(img) -> float:
    """눈을 뜨고 있을 확률(0~1). 눈 게이트와 같은 백본 한 번의 순전파로 두 층을 함께 쓴다."""
    # layer3/layer4 hook 출력과 그 출력을 읽는 분류기까지 하나의 임계구역으로 묶는다.
    with _feature_lock:
        x = _preprocess(img.convert("RGB")).unsqueeze(0).to(device)
        last = _net(x)[0]
        last = last / (last.norm() + 1e-8)
        unit = lambda v: v / (v.norm() + 1e-8)
        if _open_cnn is not None:
            # 위 _net(x)가 layer3 훅을 채웠다 — 같은 순전파 결과를 이어받는다
            return float(torch.sigmoid(_open_cnn(_layer3_out))[0].item())
        if _open_kind == "A":
            feat = last
        else:
            parts = [last, unit(_layer3_out.mean(dim=(2, 3))[0])]
            if _open_kind == "D":
                parts += [unit(_center_mean(_layer3_out)[0]), unit(_center_mean(_layer4_out)[0])]
            feat = torch.cat(parts)
        return float(torch.sigmoid(torch.dot(feat, _open_w) + _open_b).item())


def open_gate_available() -> bool:
    """뜸 여부 판정기가 로드됐는가. 파일은 저장소에 포함되며 테스트가 존재를 강제한다.

    파일이 있는데 아직 로드되지 않았으면 여기서 다시 읽는다. 2026-09-13 실제로 겪었다: 서버가
    코드 변경으로 재시작하며 검증기를 먼저 로드한 뒤에 판정기 파일이 저장돼, _loaded=True가 캐시된
    채 판정기만 꺼져 있었다 — 감은 눈 사진이 API에서 그대로 '정상'으로 나갔다. 조용히 꺼진 상태로
    남지 않게 한다. 파일이 있는데 읽기에 실패하면 예외 대신 False를 돌려주고, is_ready()가 막는다.
    """
    if not _try_load():
        return False
    if _open_w is None and _open_cnn is None and (_OPEN_GATE_PATH.exists() or _OPEN_CNN_PATH.exists()):
        with _load_lock:
            if _open_w is None and _open_cnn is None:
                try:
                    _load_open_gate()
                except Exception:
                    logger.warning("⚠️  눈 뜸 여부 판정기 로드 실패", exc_info=True)
    return _open_w is not None or _open_cnn is not None


def _open_threshold() -> float:
    return _open_cnn_thr if _open_cnn is not None else _open_thr


# 눈 클로즈업(eye 모드)용 뜸 기준. 판정기는 얼굴 사진의 눈 크롭으로 학습했고, 기준값도 그 분포에서
# '뜬 눈 99% 통과'로 골랐다. 클로즈업에 같은 기준을 쓰면 흰색으로 진행된 뚜렷한 백내장이 0.62~0.66에
# 몰려 '눈이 감겨 있어요'로 막혔다(2026-09-13, 데이터셋 표본 두 묶음에서 백내장 3.0%·1.4%).
# 클로즈업에서 실제로 감긴 눈은 훨씬 낮게 나와 기준을 낮춰도 거의 다 걸린다 — 근거 표는
# docs/eye-gate-closed-eye.md '클로즈업 기준값'. 판정기 종류마다 점수 척도가 달라 따로 둔다.
CLOSEUP_OPEN_THRESHOLD = {"cnn": 0.35, "linear": 0.13}


def _closeup_threshold() -> float:
    kind = "cnn" if _open_cnn is not None else "linear"
    return min(_open_threshold(), CLOSEUP_OPEN_THRESHOLD[kind])


def check_eye_open(img, closeup: bool = False):
    """(is_open, score). 계산 실패는 (None, None) — 호출자는 fail-closed(차단)해야 한다.
    closeup=True면 눈 클로즈업용 기준(_closeup_threshold)을 쓴다."""
    if not _try_load() or (_open_w is None and _open_cnn is None):
        return None, None
    try:
        p = _open_prob(img)
        return p >= (_closeup_threshold() if closeup else _open_threshold()), p
    except Exception:
        logger.warning("⚠️  눈 뜸 여부 계산 실패", exc_info=True)
        return None, None


def gate_available() -> bool:
    return _gate_w is not None


def is_ready() -> bool:
    """사진 분석에 필수인 눈 게이트와 눈 뜸 판정기가 모두 준비됐는가."""
    base = bool(_loaded and _net is not None and _centroid is not None and _gate_w is not None)
    # vision.py는 파일 유무와 무관하게 뜸 판정기를 요구한다. 파일이 모두 빠졌을 때도
    # readyz가 200을 반환하면 분석은 503인 서버로 트래픽을 보내게 된다.
    return base and open_gate_available()


def check_eye(img):
    """(is_eye, score) 반환. 눈 클로즈업뿐 아니라 얼굴 사진의 눈 크롭에도 쓴다.
    - (True, score)  : 눈으로 판단
    - (False, score) : 눈 아님 (풍경·피부·감은 눈·선글라스 등)
    - (None, None)   : 검증기 사용 불가 → 호출자는 fail-closed(차단)해야 함
    score는 게이트가 있으면 눈일 확률(0~1), 없으면 중심 벡터 코사인 유사도.
    """
    if not _try_load():
        return None, None
    try:
        if _gate_w is None:
            return None, None
        p = _gate_prob(img)
        threshold = max(float(_gate_thr), settings.eye_gate_threshold)
        return p >= threshold, p
    except Exception:
        logger.warning("⚠️  눈 검증 계산 실패", exc_info=True)
        return None, None
    return None, None
