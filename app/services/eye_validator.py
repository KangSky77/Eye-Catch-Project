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
import os
import logging
import threading
import numpy as np
import torch
from torchvision import models, transforms
from app.core.config import settings

logger = logging.getLogger(__name__)

_CENTROID_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "eye_centroid.npy")

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
_GATE_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "eye_gate.npz")
_gate_w = None       # (512,) 가중치
_gate_b = 0.0
_gate_thr = None     # 게이트 임계값 (npz에 기록된 값)
_load_lock = threading.Lock()   # 동시 요청이 모델을 중복 로드하지 않도록 보호


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
            _net = net
            _centroid = torch.from_numpy(centroid).to(device)
            if os.path.exists(_GATE_PATH):
                g = np.load(_GATE_PATH)
                _gate_w = torch.from_numpy(g["w"].astype(np.float32)).to(device)
                _gate_b = float(g["b"][0]); _gate_thr = float(g["threshold"])
                logger.info("눈 게이트 로드: 임계값 %.3f", _gate_thr)
            else:
                logger.warning("⚠️  eye_gate.npz 없음 — 중심 벡터 유사도로 폴백(비-눈·가려진 눈 판별력 낮음)")
            _loaded = True
        except Exception:
            # 일시적 실패(네트워크 등)는 영구 캐시하지 않음 → 다음 요청에 재시도
            logger.warning("⚠️  눈 검증기 로드 실패(다음 요청에 재시도)", exc_info=True)
            _loaded = False
    return _loaded


def warmup() -> bool:
    """서버 시작 시 호출 — 가중치를 미리 받아두고 첫 요청 지연을 없앤다."""
    ok = _try_load()
    if ok:
        logger.info("🔥 눈 검증기 준비 완료")
    else:
        logger.warning("⚠️  눈 검증기 미준비(요청 시 재시도)")
    return ok


@torch.no_grad()
def _similarity(img) -> float:
    x = _preprocess(img.convert("RGB")).unsqueeze(0).to(device)
    feat = _net(x)[0]
    feat = feat / (feat.norm() + 1e-8)
    return float(torch.dot(feat, _centroid).item())


@torch.no_grad()
def _gate_prob(img) -> float:
    """눈일 확률(0~1) — L2 정규화 임베딩에 로지스틱 1층."""
    x = _preprocess(img.convert("RGB")).unsqueeze(0).to(device)
    feat = _net(x)[0]
    feat = feat / (feat.norm() + 1e-8)
    return float(torch.sigmoid(torch.dot(feat, _gate_w) + _gate_b).item())


def gate_available() -> bool:
    return _gate_w is not None


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
        if _gate_w is not None:
            p = _gate_prob(img)
            return p >= _gate_thr, p
        score = _similarity(img)
    except Exception:
        logger.warning("⚠️  눈 검증 계산 실패", exc_info=True)
        return None, None
    return score >= settings.eye_sim_threshold, score
