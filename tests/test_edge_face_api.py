"""Gemini 합성 사진으로 재현된 잘린 얼굴 우회를 실제 multipart API에서 검사한다.

실제 MTCNN/눈 검증기를 사용한다. 질병 모델의 정확도 테스트가 아니라 부적합한
사진이 그 모델에 도달하지 않아야 한다는 회귀다. 두 뜸 판정기 구성 모두 검사한다.
"""
from pathlib import Path
import io

import pytest
from PIL import Image, ImageOps

from app.services import eye_validator as EV, vision


@pytest.mark.parametrize("kind", ["cnn", "linear"])
@pytest.mark.parametrize("filename", ["gemini-eye-patch.png", "gemini-closed-eyes.png"])
@pytest.mark.parametrize("variant", ["original", "mirror", "half", "double"])
def test_가려진_합성얼굴은_API에서_판독되지_않는다(client, monkeypatch, tmp_path, kind, filename, variant):
    if kind == "cnn" and not EV._OPEN_CNN_PATH.exists():
        pytest.skip("CNN 가중치는 별도 배포; 선형 구성은 항상 검사한다")
    # 로드 함수가 전역 상태를 바꾸므로 파일 경로뿐 아니라 파라미터도 복원한다.
    for attr in ("_open_cnn", "_open_cnn_thr", "_open_w", "_open_b", "_open_thr", "_open_kind"):
        monkeypatch.setattr(EV, attr, getattr(EV, attr))
    if kind == "linear":
        monkeypatch.setattr(EV, "_OPEN_CNN_PATH", tmp_path / "absent.pth")
    monkeypatch.setattr(EV, "_open_cnn", None)
    monkeypatch.setattr(EV, "_open_w", None)
    assert EV.open_gate_available()
    monkeypatch.setattr(vision, "weights_loaded", True)
    def forbidden(_):
        pytest.fail("가려진 눈을 백내장 모델에 전달했습니다")
    monkeypatch.setattr(vision, "_predict_single", forbidden)
    path = Path(__file__).parent / "fixtures" / filename
    with Image.open(path) as source:
        img = source.convert("RGB")
    if variant == "mirror":
        img = ImageOps.mirror(img)
    elif variant in ("half", "double"):
        factor = 0.5 if variant == "half" else 2
        img = img.resize((int(img.width * factor), int(img.height * factor)))
    content = io.BytesIO()
    img.save(content, format="PNG")
    response = client.post("/api/analyze-eye", files={"file": (filename, content.getvalue(), "image/png")})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "face"
    # 축소한 감은 눈 사진은 눈 뜸 검사보다 앞선 선명도 검사에서 거부된다.
    expected = "blurry" if filename == "gemini-closed-eyes.png" and variant == "half" else "eyes_hidden"
    assert data["result_code"] == expected
    assert data["eyes"] == [] and data["eye_probs"] == []


def test_판정기_파일이_빠지면_API_준비상태도_503(client, monkeypatch, tmp_path):
    assert EV.warmup()
    monkeypatch.setattr(EV, "_OPEN_CNN_PATH", tmp_path / "absent.pth")
    monkeypatch.setattr(EV, "_OPEN_GATE_PATH", tmp_path / "absent.npz")
    monkeypatch.setattr(EV, "_open_cnn", None)
    monkeypatch.setattr(EV, "_open_w", None)
    monkeypatch.setattr(vision, "weights_loaded", True)
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 503
