from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes import router
from app.services.vision import load_trained_weights
from app.services.database import init_db_pool, close_db_pool
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # AI 모델 로드
    load_trained_weights()
    print("✅ AI 모델 로드 완료!")

    # DB 풀 초기화 (실패해도 서버는 정상 기동)
    try:
        await init_db_pool()
        print("✅ DB 풀 초기화 완료!")
    except Exception as e:
        print(f"⚠️  DB 연결 실패 — 진단 저장 기능이 비활성화됩니다: {e}")

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
