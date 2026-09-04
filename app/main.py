import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from app.api.routes import router
from app.core.config import PROJECT_ROOT, settings
from app.services import eye_validator, eye_detector
from app.services.database import init_db_pool, close_db_pool
from app.services.llm import warmup_ollama
from app.services.vision import load_trained_weights

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # AI 모델 로드
    weights_ready = load_trained_weights()
    if weights_ready:
        logger.info("✅ AI 모델 가중치 로드 완료!")
    else:
        logger.warning("⚠️  AI 모델 가중치 미로드 — 사진 분석 API는 503으로 차단됩니다")

    warmup_tasks: set[asyncio.Task] = set()

    def spawn(coro) -> None:
        """워밍업 태스크를 종료할 때까지 추적한다."""
        task = asyncio.create_task(coro)
        warmup_tasks.add(task)
        task.add_done_callback(warmup_tasks.discard)

    # Gemma(Ollama) 모델 백그라운드 워밍업 — 첫 소견서 콜드스타트 제거
    # (서버 기동을 막지 않도록 백그라운드 태스크로 실행)
    spawn(warmup_ollama())
    logger.info("🔥 Gemma 워밍업 시작(백그라운드)")

    # 눈 검증기 백그라운드 워밍업 — ImageNet 가중치 미리 로드(첫 분석 지연·런타임 실패 방지)
    spawn(run_in_threadpool(eye_validator.warmup))

    # MTCNN 얼굴 감지기 백그라운드 워밍업 (설치되어 있을 때만)
    if eye_detector.is_available():
        spawn(run_in_threadpool(eye_detector.warmup))
        logger.info("🔥 MTCNN 감지기 웜업 시작(백그라운드)")
    else:
        # 조용히 넘어가면 안 된다 — MTCNN이 없으면 얼굴 사진에서 눈을 잘라내지 못해
        # 얼굴 전체가 눈 게이트에서 거부될 수 있고 눈별(좌/우) 판정도 사라진다.
        # 눈 클로즈업은 계속 쓸 수 있지만 얼굴 사진 편의 기능이 빠지므로 로그에 남긴다.
        logger.warning(
            "⚠️  MTCNN(facenet-pytorch) 미설치 — 얼굴→눈 크롭이 비활성화됩니다. "
            "얼굴 사진은 거부될 수 있으며 눈별(좌/우) 판정이 표시되지 않습니다. "
            "그동안은 눈을 한쪽씩 가까이 찍어주세요. "
            "복구: pip install --no-deps facenet-pytorch"
        )
    # DB 풀 초기화 (실패해도 서버는 정상 기동)
    try:
        await init_db_pool()
        logger.info("✅ DB 풀 초기화 완료!")
    except Exception:
        logger.warning("⚠️  DB 연결 실패 — 진단 저장 기능이 비활성화됩니다", exc_info=True)

    try:
        yield
    finally:
        # 워밍업 도중 서버가 종료돼도 미완료 태스크와 네트워크 연결을 남기지 않는다.
        for task in warmup_tasks:
            task.cancel()
        if warmup_tasks:
            await asyncio.gather(*warmup_tasks, return_exceptions=True)
        await close_db_pool()

app = FastAPI(lifespan=lifespan)

# CORS 설정 — 화이트리스트 방식(기본은 아예 미적용)
# 프론트가 같은 서버(/static)에서 서빙되므로 평소에는 same-origin이고, ngrok으로
# 공유해도 페이지와 API가 같은 도메인이라 CORS 헤더가 필요 없다. 예전에는
# allow_origins=["*"]로 전부 열어뒀는데 쓰지도 않는 개방이라, 필요한 origin만
# .env의 ALLOWED_ORIGINS에 나열하는 방식으로 좁혔다.
# 와일드카드가 아니어도 이 API는 쿠키 인증을 쓰지 않으므로 credentials는 계속 끈다.
_allowed_origins = settings.allowed_origins_list
if _allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"🔒 CORS 허용 origin: {_allowed_origins}")
else:
    logger.info("🔒 CORS 미들웨어 미적용 — same-origin 요청만 받습니다")

# 라우터 등록
app.include_router(router)

STATIC_DIR = PROJECT_ROOT / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def read_index():
    # index.html은 항상 재검증 → 정적 파일의 ?v= 버전이 바뀌면 즉시 반영됨
    # (모바일은 하드 새로고침이 어려워 캐시 무효화가 중요)
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-cache, must-revalidate"},
    )
