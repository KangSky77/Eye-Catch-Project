"""업로드 이미지 검증(validate_and_read_image) — 보안 가드가 실제로 막는지 확인."""
import pytest
from fastapi import HTTPException

from app.services import vision
from tests.conftest import make_image_bytes, make_upload

pytestmark = pytest.mark.anyio


async def test_비이미지_content_type_거부():
    up = make_upload(b"hello", content_type="text/plain", filename="a.txt")
    with pytest.raises(HTTPException) as e:
        await vision.validate_and_read_image(up)
    assert e.value.status_code == 400


async def test_content_type만_이미지인_가짜파일_거부():
    # 확장자/헤더를 image로 속여도 실제 디코딩이 실패하면 400
    up = make_upload(b"this is not an image at all", content_type="image/jpeg")
    with pytest.raises(HTTPException) as e:
        await vision.validate_and_read_image(up)
    assert e.value.status_code == 400


async def test_파일크기_상한_초과시_413(monkeypatch):
    monkeypatch.setattr(vision, "MAX_FILE_SIZE", 10)   # 10바이트로 낮춰 재현
    up = make_upload(make_image_bytes())
    with pytest.raises(HTTPException) as e:
        await vision.validate_and_read_image(up)
    assert e.value.status_code == 413


async def test_픽셀수_상한_초과시_413(monkeypatch):
    # 압축폭탄 방어: 디코딩 전에 (w*h) 검사로 거부되는지
    monkeypatch.setattr(vision, "MAX_IMAGE_PIXELS", 1000)
    up = make_upload(make_image_bytes(w=64, h=64))     # 4096픽셀 > 1000
    with pytest.raises(HTTPException) as e:
        await vision.validate_and_read_image(up)
    assert e.value.status_code == 413


async def test_정상이미지_RGB로_반환():
    up = make_upload(make_image_bytes(w=48, h=32))
    img = await vision.validate_and_read_image(up)
    assert img.mode == "RGB"
    assert img.size == (48, 32)


async def test_EXIF_회전정보_반영():
    # orientation=6(90도 회전) → 가로/세로가 뒤집혀 나와야 함
    # (폰 세로 사진이 눕혀진 채 눈 크롭되는 사고 방지)
    up = make_upload(make_image_bytes(w=48, h=32, orientation=6))
    img = await vision.validate_and_read_image(up)
    assert img.size == (32, 48)


async def test_PNG도_허용():
    up = make_upload(make_image_bytes(fmt="PNG"), content_type="image/png", filename="t.png")
    img = await vision.validate_and_read_image(up)
    assert img.mode == "RGB"
