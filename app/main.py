import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.concurrency import run_in_threadpool
from app.api.routes import router
from app.services.vision import load_trained_weights
from app.services.llm import warmup_ollama
from app.services import eye_validator, eye_detector
from app.services.database import init_db_pool, close_db_pool
import asyncio
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # AI 모델 로드
    load_trained_weights()
    logger.info("✅ AI 모델 로드 완료!")

    # Gemma(Ollama) 모델 백그라운드 워밍업 — 첫 소견서 콜드스타트 제거
    # (서버 기동을 막지 않도록 백그라운드 태스크로 실행)
    asyncio.create_task(warmup_ollama())
    logger.info("🔥 Gemma 워밍업 시작(백그라운드)")

    # 눈 검증기 백그라운드 워밍업 — ImageNet 가중치 미리 로드(첫 분석 지연·런타임 실패 방지)
    asyncio.create_task(run_in_threadpool(eye_validator.warmup))

    # MTCNN 얼굴 감지기 백그라운드 워밍업 (설치되어 있을 때만)
    if eye_detector.is_available():
        asyncio.create_task(run_in_threadpool(eye_detector.warmup))
        logger.info("🔥 MTCNN 감지기 웜업 시작(백그라운드)")


    # DB 풀 초기화 (실패해도 서버는 정상 기동)
    try:
        await init_db_pool()
        logger.info("✅ DB 풀 초기화 완료!")
    except Exception:
        logger.warning("⚠️  DB 연결 실패 — 진단 저장 기능이 비활성화됩니다", exc_info=True)

    yield

    await close_db_pool()

app = FastAPI(lifespan=lifespan)

# CORS 설정
# 프론트가 같은 서버(/static)에서 서빙되므로 사실상 same-origin.
# 와일드카드 origin + credentials 조합은 스펙 위반이라 credentials는 끔.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(router)

# 정적 파일 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    # index.html은 항상 재검증 → 정적 파일의 ?v= 버전이 바뀌면 즉시 반영됨
    # (모바일은 하드 새로고침이 어려워 캐시 무효화가 중요)
    return FileResponse(
        os.path.join("static", "index.html"),
        headers={"Cache-Control": "no-cache, must-revalidate"},
    )
