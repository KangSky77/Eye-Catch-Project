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
_centroid = None     # 정규화된 눈 분포 중심 벡터
_loaded = False      # 성공적으로 로드된 경우에만 True (실패는 캐시하지 않음)
_load_lock = threading.Lock()   # 동시 요청이 모델을 중복 로드하지 않도록 보호


def _try_load() -> bool:
    """모델·센트로이드 로드 시도. 성공 시에만 True를 캐시(실패는 다음 호출에 재시도)."""
    global _net, _centroid, _loaded
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


def check_eye(img):
    """(is_eye, score) 반환.
    - (True, score)  : 눈으로 판단
    - (False, score) : 눈 아님
    - (None, None)   : 검증기 사용 불가 → 호출자는 fail-closed(차단)해야 함
    """
    if not _try_load():
        return None, None
    try:
        score = _similarity(img)
    except Exception:
        logger.warning("⚠️  눈 유사도 계산 실패", exc_info=True)
        return None, None
    return score >= settings.eye_sim_threshold, score
