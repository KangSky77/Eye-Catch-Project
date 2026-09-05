import asyncio
import logging
from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool
from app.core.config import settings
from app.services.vision import predict_cataract, validate_and_read_image
from app.services import vision, eye_validator
from app.services.llm import get_gemma_opinion_stream, chat_with_gemma_stream, generate_next_question, KEEPALIVE, KEEPALIVE_INTERVAL
from app.services.clinics import search_eye_clinics
from app.services.database import save_diagnosis
from app.schemas.ai import GemmaRequest, ChatRequest, QuestionGenRequest, SaveDiagnosisRequest

logger = logging.getLogger(__name__)
router = APIRouter()
_inference_slots = asyncio.Semaphore(settings.max_inference_concurrency)
_llm_slots = asyncio.Semaphore(settings.max_llm_concurrency)


@router.get("/healthz")
async def healthz():
    """프로세스가 HTTP 요청을 받을 수 있는지 확인하는 경량 liveness 체크."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz():
    """실제 이미지 분석을 받을 준비가 됐는지 확인하는 readiness 체크."""
    if not vision.weights_loaded or not eye_validator.is_ready():
        return JSONResponse(status_code=503, content={"status": "not_ready", "model": "unavailable"})
    return {"status": "ready", "model": "ready"}


async def _limited_stream(stream):
    """LLM 스트림 수를 제한하고 클라이언트 취소 시 슬롯을 즉시 반납한다."""
    acquire = asyncio.create_task(_llm_slots.acquire())
    try:
        while not acquire.done():
            try:
                await asyncio.wait_for(asyncio.shield(acquire), timeout=KEEPALIVE_INTERVAL)
            except asyncio.TimeoutError:
                yield KEEPALIVE
        await acquire
        async for chunk in stream:
            yield chunk
    finally:
        if not acquire.done():
            acquire.cancel()
            await asyncio.gather(acquire, return_exceptions=True)
        # acquire may finish while this generator is suspended at KEEPALIVE.
        # Inspect the task after cancellation has settled, not a local flag.
        if not acquire.cancelled() and acquire.exception() is None and acquire.result():
            _llm_slots.release()


@router.get("/api/nearby-clinics")
async def nearby_clinics(
    # 좌표 범위를 스키마에서 막는다 — 범위 밖 값을 그대로 넘기면 카카오/Overpass에
    # 무의미한 외부 요청만 나가고, 에러도 서드파티 쪽에서 뒤늦게 돌아온다.
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
):
    """현재 위치 주변 안과 검색 (카카오 로컬 REST API, 키 없으면 빈 목록)."""
    return await search_eye_clinics(lat, lng)

@router.post("/api/analyze-eye")
async def analyze_eye(file: UploadFile = File(...)):
    async with _inference_slots:
        img = await validate_and_read_image(file)
        # 무거운 추론(MTCNN+ResNet)은 스레드풀에서 실행 → 이벤트루프(다른 요청/스트림)를 막지 않음
        result = await run_in_threadpool(predict_cataract, img)
    return {
        "status": "success",
        "closeup_suggested": False,
        "eye_score": None,
        "sharpness": None,
        "glare": None,
        **result,
    }

@router.post("/api/get-ai-opinion")
async def get_ai_opinion(req: GemmaRequest):
    return StreamingResponse(
        _limited_stream(get_gemma_opinion_stream(
            req.cataract_res, req.amsler_res, req.chat_symptoms, req.lang,
            cataract_code=req.cataract_code,
            amsler_abnormal=req.amsler_abnormal,
            symptom_codes=req.symptom_codes,
            eye_asymmetric=req.eye_asymmetric,
        )),
        media_type="text/plain"
    )

@router.post("/api/chat-with-gemma")
async def chat_with_gemma(req: ChatRequest):
    return StreamingResponse(
        _limited_stream(chat_with_gemma_stream(req.user_msg, req.context, req.lang)),
        media_type="text/plain"
    )

@router.post("/api/generate-next-question")
async def generate_next_question_endpoint(req: QuestionGenRequest):
    async with _llm_slots:
        question, answer_type = await generate_next_question(
            req.lang, req.cataract_res, req.amsler_res, req.chat_history
        )
    # answer_type: "yesno"(네/아니오 버튼) | "text"(자유 입력칸)
    return {"question": question, "answer_type": answer_type}

@router.post("/api/save-diagnosis")
async def save_diagnosis_endpoint(req: SaveDiagnosisRequest):
    try:
        record_id = await save_diagnosis(
            req.cataract_result,
            req.amsler_result,
            req.chat_symptoms,
            req.gemma_opinion,
        )
        return {"status": "saved", "id": record_id}
    except Exception:
        # DB 연결 실패 시 앱 전체가 죽지 않도록 소프트 실패
        # 내부 에러 상세(호스트명 등)는 클라이언트에 노출하지 않고 서버 로그에만 남김
        logger.error("⚠️  진단 저장 실패", exc_info=True)
        return {"status": "skipped"}
