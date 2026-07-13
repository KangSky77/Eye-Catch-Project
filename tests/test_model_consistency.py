"""학습↔서빙 일관성 — 전처리·클래스 순서·백본이 어긋나면 조용히 정확도만 망가지므로
메타데이터(학습 시 기록)와 서빙 코드(vision.py)를 교차 검증한다."""
import json
import os

import pytest
from torchvision import transforms

from app.core.config import settings
from app.services import vision


def _metadata():
    path = settings.model_path.replace(".pth", "_metadata.json")
    if not os.path.exists(path):
        pytest.skip(f"메타데이터 없음: {path} (학습 산출물 없는 환경)")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_임계값_구조가_말이_됨():
    assert 0 < settings.borderline_threshold < settings.risk_threshold <= 100


def test_클래스_인덱스_계약():
    # vision.py는 softmax[:, 1]을 '백내장 확률'로 쓴다 — 1번이 백내장이 아니면 판정 전체가 반전됨
    meta = _metadata()
    assert meta["class_to_idx"] == {"0_normal": 0, "1_cataract": 1}


def test_백본_설정과_메타데이터_일치():
    meta = _metadata()
    assert meta["backbone"] == settings.model_backbone


def test_서빙_전처리가_학습과_동일():
    meta = _metadata()
    resize = next(t for t in vision.preprocess.transforms if isinstance(t, transforms.Resize))
    norm = next(t for t in vision.preprocess.transforms if isinstance(t, transforms.Normalize))
    assert list(resize.size) == [meta["image_size"], meta["image_size"]]
    assert [round(float(m), 3) for m in norm.mean] == [round(m, 3) for m in meta["normalization"]["mean"]]
    assert [round(float(s), 3) for s in norm.std] == [round(s, 3) for s in meta["normalization"]["std"]]


def test_배포_가중치가_로드_가능():
    # .pth는 git 미포함(용량) — 파일이 있는 환경(노트북/실습실)에서만 실제 로드 검증
    if not os.path.exists(settings.model_path):
        pytest.skip(f"가중치 없음: {settings.model_path}")
    assert vision.load_trained_weights() is True
    assert vision.weights_loaded is True
