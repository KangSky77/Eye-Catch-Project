"""공용 픽스처.

설계 원칙: 테스트는 외부 의존성(학습된 가중치, Ollama, PostgreSQL, 카카오 API, 네트워크)
없이 어느 PC에서든 `pytest` 한 방에 돌아야 한다. 무거운 것들은 전부 monkeypatch로 대체하고,
여기서는 순수 로직(검증/판정/폴백/스키마)만 검사한다.
"""
import os

# 스위트 전체가 추론을 모킹하므로 GPU가 전혀 필요 없다. torch가 CUDA를 잡기 전에
# 숨겨서 (1) 6GB 노트북에서 추론 서버·Ollama와 VRAM 경합으로 pytest가 OOM 나는 것을
# 막고 (2) CUDA 컨텍스트 초기화 비용을 없앤다(실측 6.6s→5.2s).
# 반드시 app.* 모듈 import 전에 실행돼야 함 (vision.py가 import 시점에 .to(device) 함).
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import io

import pytest
from PIL import Image
from starlette.datastructures import Headers
from fastapi import UploadFile


@pytest.fixture
def anyio_backend():
    # anyio의 pytest 플러그인으로 async 테스트 실행 (trio는 미설치라 asyncio만)
    return "asyncio"


def make_image_bytes(w=64, h=64, fmt="JPEG", orientation=None, color=(120, 90, 60)) -> bytes:
    """테스트용 이미지 바이트 생성. orientation을 주면 EXIF 회전 태그(274)를 심는다."""
    img = Image.new("RGB", (w, h), color)
    buf = io.BytesIO()
    kwargs = {}
    if orientation:
        exif = Image.Exif()
        exif[274] = orientation
        kwargs["exif"] = exif
    img.save(buf, format=fmt, **kwargs)
    return buf.getvalue()


def make_upload(data: bytes, content_type="image/jpeg", filename="t.jpg") -> UploadFile:
    """vision.validate_and_read_image에 넣을 UploadFile 생성."""
    return UploadFile(
        file=io.BytesIO(data),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


@pytest.fixture(scope="session")
def client():
    """lifespan 없이 만든 TestClient.

    with 컨텍스트로 열지 않으면 lifespan(모델 가중치 로드, Ollama/MTCNN/검증기 웜업,
    DB 풀 초기화)이 실행되지 않는다 — 라우팅·검증·직렬화 로직만 순수하게 테스트하기 위함.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)
