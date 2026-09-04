"""학습↔서빙 일관성 — 전처리·클래스 순서·백본이 어긋나면 조용히 정확도만 망가지므로
메타데이터(학습 시 기록)와 서빙 코드(vision.py)를 교차 검증한다."""
import hashlib
import json
from pathlib import Path

import pytest
from torchvision import transforms

from app.core.config import Settings, settings
from app.services import vision


def _metadata():
    path = settings.model_metadata_path
    if not path.exists():
        pytest.skip(f"메타데이터 없음: {path} (학습 산출물 없는 환경)")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_임계값_구조가_말이_됨():
    assert 0 <= settings.uncertain_threshold < settings.borderline_threshold < settings.risk_threshold <= 100


@pytest.mark.parametrize("overrides", [
    {"uncertain_threshold": 25.0, "borderline_threshold": 25.0},
    {"borderline_threshold": 60.0, "risk_threshold": 50.0},
    {"risk_threshold": 101.0},
    {"max_upload_size_bytes": 0},
    {"ollama_timeout_seconds": 0},
    {"max_inference_concurrency": 0},
    {"max_llm_concurrency": 0},
])
def test_위험한_런타임설정은_기동전에_거부(overrides):
    with pytest.raises(ValueError):
        Settings(**overrides)


def test_설정과_모델경로는_실행_cwd가_아니라_저장소_기준():
    """IDE·서비스 관리자에서 다른 cwd로 실행해도 .env와 가중치를 찾아야 한다."""
    root = Path(__file__).resolve().parent.parent
    assert Path(settings.model_config["env_file"]).is_absolute()
    assert Path(settings.model_config["env_file"]).resolve() == root / ".env"
    assert settings.model_file.is_absolute()
    assert settings.model_file == root / settings.model_path


def test_클래스_인덱스_계약():
    # vision.py는 softmax[:, 1]을 '백내장 확률'로 쓴다 — 1번이 백내장이 아니면 판정 전체가 반전됨
    meta = _metadata()
    assert meta["class_to_idx"] == {"0_normal": 0, "1_cataract": 1}


def test_백본_설정과_메타데이터_일치():
    meta = _metadata()
    if "backbone" not in meta:
        # v3 시절 메타데이터는 'architecture' 키만 있음 — .env 없는 새 클론은
        # 기본 설정(v3 모델)을 가리키므로 KeyError로 죽지 않고 건너뛴다
        pytest.skip("구버전(v3) 메타데이터 — backbone 필드 없음")
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
    if not settings.model_file.exists():
        pytest.skip(f"가중치 없음: {settings.model_file}")
    try:
        assert vision.load_trained_weights() is True
        assert vision.weights_loaded is True
    finally:
        # 전역 플래그를 원상복구 — 이후 테스트가 '미로드 기본 상태'를 전제해도
        # 실행 순서/이 파일 유무에 따라 결과가 달라지지 않도록
        vision.weights_loaded = False


def test_가중치_파일이_메타데이터와_같은_학습본():
    # v5가 v4 파일명을 덮어쓰는 운영 방식이라, 로컬 .pth가 메타데이터(git 추적)와
    # 다른 세대일 수 있음 — sha256으로 '지금 서빙될 가중치'가 기록된 그 모델인지 확인
    meta = _metadata()
    expected = meta.get("weights_sha256")
    if not expected:
        pytest.skip("메타데이터에 weights_sha256 미기록(구버전 학습 산출물)")
    if not settings.model_file.exists():
        pytest.skip(f"가중치 없음: {settings.model_file}")
    with open(settings.model_file, "rb") as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    assert actual == expected, (
        "로컬 가중치가 메타데이터에 기록된 학습본과 다릅니다 — "
        "오래된 .pth를 쓰고 있을 가능성 (팀원에게 최신 가중치를 받으세요)"
    )


def test_런타임도_가중치_sha256_불일치를_차단한다(tmp_path):
    weights = tmp_path / "model.pth"
    metadata = tmp_path / "model_metadata.json"
    weights.write_bytes(b"known-good")
    digest = hashlib.sha256(b"known-good").hexdigest()
    metadata.write_text(json.dumps({"weights_sha256": digest}), encoding="utf-8")
    assert vision._weights_match_metadata(weights, metadata) is True
    weights.write_bytes(b"corrupted-or-stale")
    assert vision._weights_match_metadata(weights, metadata) is False


@pytest.mark.parametrize("metadata_payload", [None, {}])
def test_출처를_검증할_수_없는_가중치는_차단한다(tmp_path, metadata_payload):
    weights = tmp_path / "model.pth"
    metadata = tmp_path / "model_metadata.json"
    weights.write_bytes(b"unverifiable")
    if metadata_payload is not None:
        metadata.write_text(json.dumps(metadata_payload), encoding="utf-8")
    assert vision._weights_match_metadata(weights, metadata) is False


def test_눈_OOD_게이트_임계값이_실측_근거와_함께_있다():
    """2026-08-29: 0.55는 '단색 배경 + 가운데 블롭' 계열을 통과시켰다.
    (실사용 테스트에서 초록 배경 + 빨간 사각형이 '경계 단계 - 안과 검진 권장'을 받음)

    재실측 근거는 config.py 주석에, 재현 방법은 scripts/probe_eye_gate.py에 있다.
    임계값을 다시 만질 때는 반드시 그 스크립트로 재측정할 것."""
    from pathlib import Path

    assert settings.eye_sim_threshold == 0.62

    root = Path(__file__).resolve().parent.parent
    probe = root / "scripts" / "probe_eye_gate.py"
    assert probe.exists(), "임계값 재현 스크립트가 있어야 근거를 다시 뽑을 수 있다"

    src = probe.read_text(encoding="utf-8")
    assert "blob_" in src, "게이트를 뚫었던 블롭 계열이 회귀 표본으로 남아 있어야 한다"

    cfg = (root / "app" / "core" / "config.py").read_text(encoding="utf-8")
    assert "probe_eye_gate.py" in cfg, "임계값 옆에 재현 방법이 적혀 있어야 한다"
