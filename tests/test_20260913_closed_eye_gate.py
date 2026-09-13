"""감은 눈이 게이트를 통과하던 문제(2026-09-13)의 회귀 테스트.

AI로 만든 감은 눈 얼굴 세 장이 게이트를 0.897~0.978로 통과해 '혼탁 특징 없음 0/100'이
나갔다. 게이트 학습 음성에 실제로 감긴 눈꺼풀이 없었기 때문이다. 수정: 눈 게이트는 그대로 두고, 얼굴 모드 눈 크롭에 '뜸 여부' 판정기를 따로 둔다.
  학습 데이터는 Wikimedia Commons 자유 라이선스 사진에서 사람이 검수한 뜬 눈·감은 눈 크롭이다.

사진·크롭은 저장소에 없다(dataset/과 같은 취급). 그래서 데이터 의존 테스트는 자료가 있을
때만 돌고, 구조 테스트는 항상 돈다.
"""
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = (ROOT / "scripts" / "build_eye_gate.py").read_text(encoding="utf-8")
CLOSED = ROOT / "dataset_closedeye"


def test_뜸여부_판정기는_검수·분할_기록만으로_학습한다():
    # 폴더를 통째로 쓰면 '수면' 범주의 뜬 눈이나 인물 사진의 감은 눈이 반대 라벨로 들어간다
    trainer = (ROOT / "scripts" / "build_eye_open_gate.py").read_text(encoding="utf-8")
    body = trainer[trainer.index("def load_split("):trainer.index("def open_rgb(")]
    assert "review.json" in body and "split.json" in body
    assert "os.listdir" not in body and ".iterdir()" not in body and ".glob(" not in body
    assert 'load_split("dataset_openeye", "open", "train")' in trainer
    assert 'load_split("dataset_closedeye", "closed", "holdout")' in trainer
    # 얼굴 감사용 사진은 '학습에 쓰지 말 것'이 명시돼 있다
    assert "face-audit" not in body


def test_뜸여부_판정기_파일이_배포되고_학습_추론_특징이_일치한다():
    import numpy as np
    path = ROOT / "app" / "models" / "eye_open_gate.npz"
    assert path.exists(), "scripts/build_eye_open_gate.py 산출물이 있어야 한다 — 없으면 감은 눈이 다시 통과한다"
    gate = np.load(path)
    assert str(gate["features"]) in ("A", "B", "D")
    meta = json.loads(str(gate["meta"]))
    assert meta["holdout_open_pass"] >= 0.98, "실제 사용자의 뜬 눈을 거부하면 앱 전체가 막힌다"
    validator = (ROOT / "app" / "services" / "eye_validator.py").read_text(encoding="utf-8")
    trainer = (ROOT / "scripts" / "build_eye_open_gate.py").read_text(encoding="utf-8")
    # 중앙평균 계산이 학습과 추론에서 다르면 판정기가 엉뚱한 값을 낸다 — 핵심 문장을 양쪽에서 대조한다
    for line in ("frac=0.5):",
                 "ch, cw = max(1, int(h * frac)), max(1, int(w * frac))",
                 "y, x = (h - ch) // 2, (w - cw) // 2",
                 "return fmap[:, :, y:y + ch, x:x + cw].mean(dim=(2, 3))"):
        assert line in validator and line in trainer, f"학습·추론 특징 불일치: {line}"


def test_감은_눈_수집은_자유_라이선스와_출처_기록을_지킨다():
    fetch = (ROOT / "scripts" / "fetch_closed_eye_photos.py").read_text(encoding="utf-8")
    assert "import fetch_non_eye_photos as base" in fetch, "라이선스 필터를 따로 구현하지 말고 재사용한다"
    assert "ATTRIBUTION" in fetch
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "dataset_closedeye/*" in ignore and "!dataset_closedeye/ATTRIBUTION.csv" in ignore


def test_기록된_감은_눈_출처는_모두_자유_라이선스다():
    attribution = CLOSED / "ATTRIBUTION.csv"
    if not attribution.exists():
        pytest.skip("감은 눈 사진을 아직 받지 않음")
    import csv
    with open(attribution, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows
    allowed = ("cc0", "public domain", "cc by", "pd-")
    bad = [r["filename"] for r in rows if not r["license"].strip().lower().startswith(allowed)]
    assert not bad, f"비자유 라이선스가 섞였다: {bad[:5]}"
    review = CLOSED / "review.json"
    if review.exists():
        photos = {r["filename"].rsplit(".", 1)[0] for r in rows}
        orphan = [c for c in json.loads(review.read_text(encoding="utf-8"))["closed"]
                  if c.split("__f")[0] not in photos]
        assert not orphan, f"출처 기록이 없는 크롭이 학습 목록에 있다: {orphan[:5]}"


def test_학습에_쓰지_않은_감은_눈은_앱_흐름에서_거부된다():
    """얼굴 모드의 실제 판정 순서와 같게 본다: 눈 게이트가 거부하거나, 통과했더라도
    뜸 여부 판정기가 '감음'이라고 하면 거부다(app/services/vision.py).

    판정기 파일이 없으면 건너뛰지 않고 실패한다 — 파일 없이 배포되면 이 문제가 그대로 돌아온다.
    """
    review, split = CLOSED / "review.json", CLOSED / "split.json"
    if not (review.exists() and split.exists() and (CLOSED / "crops").exists()):
        pytest.skip("검수된 감은 눈 크롭 없음(사진은 저장소 밖)")
    from PIL import Image
    from app.services import eye_validator
    if not eye_validator.warmup() or not eye_validator.gate_available():
        pytest.skip("눈 게이트 가중치 없음")
    assert eye_validator.open_gate_available(), "app/models/eye_open_gate.npz가 없다 — 감은 눈이 다시 통과한다"
    stems = {Path(n).stem for n in json.loads(split.read_text(encoding="utf-8"))["holdout"]}
    crops = [CLOSED / "crops" / n for n in json.loads(review.read_text(encoding="utf-8"))["closed"]
             if n.split("__f")[0] in stems and (CLOSED / "crops" / n).exists()]
    if len(crops) < 20:
        pytest.skip(f"평가용 감은 눈 크롭이 너무 적다({len(crops)}개)")
    passed = []
    for path in crops:
        img = Image.open(path).convert("RGB")
        if eye_validator.check_eye(img)[0] and eye_validator.check_eye_open(img)[0]:
            passed.append(path.name)
    rate = len(passed) / len(crops)
    # 상한은 학습 결과표(docs/eye-gate-closed-eye.md)에 근거해 정한다 — 표를 바꾸면 여기도 본다
    assert rate <= 0.15, f"학습에 쓰지 않은 감은 눈의 {rate:.0%}가 통과했다: {passed[:5]}"


def test_판정기_파일이_늦게_생겨도_조용히_꺼진_채로_남지_않는다(monkeypatch, tmp_path):
    """서버가 검증기를 먼저 로드한 뒤 판정기 파일이 저장되면, 예전에는 _loaded 캐시 때문에
    판정기가 영영 꺼져 있었다(2026-09-13 실제 발생 — 감은 눈 사진이 API에서 '정상'으로 나갔다)."""
    import shutil
    from app.services import eye_validator as EV
    if not EV.warmup() or not EV.gate_available():
        pytest.skip("눈 게이트 가중치 없음")
    real = ROOT / "app" / "models" / "eye_open_gate.npz"
    if not real.exists():
        pytest.skip("판정기 파일 없음")
    late = tmp_path / "eye_open_gate.npz"
    monkeypatch.setattr(EV, "_OPEN_GATE_PATH", late)
    monkeypatch.setattr(EV, "_OPEN_CNN_PATH", tmp_path / "없음.pth")
    monkeypatch.setattr(EV, "_open_cnn", None)
    monkeypatch.setattr(EV, "_open_w", None)
    # 파일이 아직 없는 동안: 준비 상태는 기존 게이트 기준, 판정기는 없음
    assert EV.open_gate_available() is False
    assert EV.is_ready() is True
    # 파일이 생기면 재시작 없이 바로 켜져야 한다
    shutil.copy(real, late)
    assert EV.open_gate_available() is True
    assert EV.is_ready() is True


def test_판정기_파일이_있는데_로드에_실패하면_준비_완료가_아니다(monkeypatch, tmp_path):
    from app.services import eye_validator as EV
    if not EV.warmup() or not EV.gate_available():
        pytest.skip("눈 게이트 가중치 없음")
    broken = tmp_path / "eye_open_gate.npz"
    broken.write_bytes(b"not a numpy file")
    monkeypatch.setattr(EV, "_OPEN_GATE_PATH", broken)
    monkeypatch.setattr(EV, "_OPEN_CNN_PATH", tmp_path / "없음.pth")
    monkeypatch.setattr(EV, "_open_cnn", None)
    monkeypatch.setattr(EV, "_open_w", None)
    assert EV.open_gate_available() is False
    assert EV.is_ready() is False, "판정기 없이 감은 눈이 통과하는 상태로 트래픽을 받으면 안 된다"


def test_미세조정_판정기는_학습_스크립트와_구조가_같고_없으면_선형으로_동작한다(monkeypatch, tmp_path):
    """*.pth는 git에 없다. 새로 받은 저장소에서도 앱이 막히지 않고 커밋된 선형 판정기로 돌아야 한다."""
    import sys
    import torch
    from app.services import eye_validator as EV
    if not EV.warmup() or not EV.gate_available():
        pytest.skip("눈 게이트 가중치 없음")
    sys.path.insert(0, str(ROOT / "scripts"))
    import copy
    from train_eye_open_cnn import Head
    trained_keys = set(Head(copy.deepcopy(EV._net.layer4)).state_dict())
    served_keys = set(EV._OpenHead(copy.deepcopy(EV._net.layer4)).state_dict())
    assert trained_keys == served_keys, "학습·추론 구조가 다르면 가중치를 읽을 수 없다"

    # 파일이 없으면 선형 판정기
    monkeypatch.setattr(EV, "_OPEN_CNN_PATH", tmp_path / "없음.pth")
    monkeypatch.setattr(EV, "_open_cnn", None)
    monkeypatch.setattr(EV, "_open_w", None)
    assert EV.open_gate_available() is True and EV._open_cnn is None and EV._open_w is not None

    # 파일이 있으면 미세조정 판정기, 임계값은 파일에 기록된 값
    fake = tmp_path / "eye_open_cnn.pth"
    head = Head(copy.deepcopy(EV._net.layer4))
    torch.save({"state_dict": {k: v.half() for k, v in head.state_dict().items()}, "meta": {"threshold": 0.4242}}, fake)
    monkeypatch.setattr(EV, "_OPEN_CNN_PATH", fake)
    monkeypatch.setattr(EV, "_open_cnn", None)
    monkeypatch.setattr(EV, "_open_w", None)
    assert EV.open_gate_available() is True and EV._open_cnn is not None
    assert abs(EV._open_threshold() - 0.4242) < 1e-6
    from PIL import Image
    ok, score = EV.check_eye_open(Image.new("RGB", (120, 120), (150, 110, 90)))
    assert ok in (True, False) and 0.0 <= score <= 1.0


def test_뜸여부_특징은_동시호출에서도_섞이지_않는다(monkeypatch):
    """forward hook이 전역 특징을 기록해도 두 요청이 한 번에 순전파되지 않아야 한다."""
    import torch
    from PIL import Image
    from app.services import eye_validator as EV

    active = 0
    max_active = 0
    guard = threading.Lock()

    class DummyNet(torch.nn.Module):
        def forward(self, x):
            nonlocal active, max_active
            with guard:
                active += 1
                max_active = max(max_active, active)
            try:
                # 겹치면 전역 hook 출력이 서로 덮이는 실제 장애를 재현한다.
                time.sleep(0.02)
                EV._layer3_out = torch.zeros((1, 256, 14, 14), device=x.device)
                EV._layer4_out = torch.zeros((1, 512, 7, 7), device=x.device)
                return torch.ones((1, 512), device=x.device)
            finally:
                with guard:
                    active -= 1

    monkeypatch.setattr(EV, "_net", DummyNet())
    monkeypatch.setattr(EV, "_open_cnn", None)
    monkeypatch.setattr(EV, "_open_kind", "A")
    monkeypatch.setattr(EV, "_open_w", torch.zeros(512, device=EV.device))
    monkeypatch.setattr(EV, "_open_b", 0.0)
    image = Image.new("RGB", (120, 120), (150, 110, 90))
    with ThreadPoolExecutor(max_workers=2) as pool:
        values = list(pool.map(EV._open_prob, [image, image]))
    assert max_active == 1
    assert values == pytest.approx([0.5, 0.5], abs=1e-6)


def test_클로즈업은_얼굴보다_낮은_뜸_기준을_쓴다(monkeypatch):
    """얼굴 크롭 기준(0.66대)을 클로즈업에 그대로 쓰면 흰색으로 진행된 백내장이 '눈 감음'으로 막힌다."""
    from PIL import Image
    from app.services import eye_validator as EV

    assert EV._try_load() and EV.open_gate_available()
    face_thr, close_thr = EV._open_threshold(), EV._closeup_threshold()
    assert close_thr < face_thr
    assert set(EV.CLOSEUP_OPEN_THRESHOLD) == {"cnn", "linear"}
    between = (face_thr + close_thr) / 2
    monkeypatch.setattr(EV, "_open_prob", lambda img: between)
    img = Image.new("RGB", (120, 120), (150, 110, 90))
    assert EV.check_eye_open(img)[0] is False
    assert EV.check_eye_open(img, closeup=True)[0] is True
