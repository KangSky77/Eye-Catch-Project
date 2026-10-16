import asyncio
import io
import logging
import time
from urllib.parse import urlsplit, urlunsplit
import httpx
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool
from app.core.config import settings
from app.services.vision import predict_cataract, validate_and_read_image
from app.services import vision, eye_validator, eye_detector
from app.services.llm import get_gemma_opinion_stream, chat_with_gemma_stream, generate_personalized_question, translate_personalized_question, KEEPALIVE, KEEPALIVE_INTERVAL
from app.services import questions as followup_questions
from app.services.clinics import search_eye_clinics
from app.services.plain_language import rewrite_findings
from app.services.admission import require_admission
from app.services.service_faq import is_score_question
from app.schemas.ai import GemmaRequest, ChatRequest, QuestionGenRequest, PlainFindingsRequest, QuestionTranslationRequest

logger = logging.getLogger(__name__)
router = APIRouter()
_inference_slots = asyncio.Semaphore(settings.max_inference_concurrency)
_llm_slots = asyncio.Semaphore(settings.max_llm_concurrency)
_DEFAULT_INFERENCE_SLOTS = _inference_slots
_DEFAULT_LLM_SLOTS = _llm_slots
_scaled_inference_slots: dict[int, asyncio.Semaphore] = {}
_scaled_llm_slots: dict[int, asyncio.Semaphore] = {}

_photo_in_flight: dict[str, int] = {}
_photo_cooldown_until: dict[str, float] = {}
_photo_rr_cursor: int = 0


def reset_photo_worker_pool_state() -> None:
    """테스트 격리 및 사진 워커 풀 상태 초기화용."""
    global _photo_rr_cursor
    _photo_in_flight.clear()
    _photo_cooldown_until.clear()
    _photo_rr_cursor = 0


def _get_llm_slots() -> asyncio.Semaphore:
    if _llm_slots is not _DEFAULT_LLM_SLOTS:
        return _llm_slots
    n_workers = max(1, len(settings.ollama_url_list))
    if n_workers == 1:
        return _llm_slots
    cap = settings.max_llm_concurrency * n_workers
    return _scaled_llm_slots.setdefault(cap, asyncio.Semaphore(cap))


def _get_inference_slots() -> asyncio.Semaphore:
    if _inference_slots is not _DEFAULT_INFERENCE_SLOTS:
        return _inference_slots
    n_workers = 1 + len(settings.photo_worker_url_list)
    if n_workers == 1:
        return _inference_slots
    cap = settings.max_inference_concurrency * n_workers
    return _scaled_inference_slots.setdefault(cap, asyncio.Semaphore(cap))


def _ordered_photo_targets() -> list[str]:
    global _photo_rr_cursor
    remotes = settings.photo_worker_url_list
    if not remotes:
        return ["local"]
    targets = ["local", *remotes]
    n = len(targets)
    start = _photo_rr_cursor % n
    _photo_rr_cursor = (_photo_rr_cursor + 1) % n
    rotated = targets[start:] + targets[:start]
    now = time.monotonic()
    return sorted(
        rotated,
        key=lambda t: (
            _photo_cooldown_until.get(t, 0.0) > now,
            _photo_in_flight.get(t, 0),
        ),
    )


async def _dispatch_photo_analysis(img) -> dict:
    targets = _ordered_photo_targets()
    if targets == ["local"]:
        return await run_in_threadpool(predict_cataract, img)
    buf: bytes | None = None
    compressed_flag = "true" if img.info.get("heavy_jpeg_compression") else "false"
    for target in targets:
        _photo_in_flight[target] = _photo_in_flight.get(target, 0) + 1
        try:
            if target == "local":
                return await run_in_threadpool(predict_cataract, img)
            if buf is None:
                out = io.BytesIO()
                img.save(out, format="PNG")
                buf = out.getvalue()
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    target,
                    data={"source_compressed": compressed_flag},
                    files={"file": ("eye.png", buf, "image/png")},
                )
                res.raise_for_status()
                data = res.json()
                if not isinstance(data, dict) or "result_code" not in data:
                    raise ValueError("Invalid photo worker payload")
                _photo_cooldown_until.pop(target, None)
                return data
        except Exception:
            if target != "local" and settings.worker_cooldown_seconds > 0:
                _photo_cooldown_until[target] = time.monotonic() + settings.worker_cooldown_seconds
            logger.warning("⚠️  사진 분석 워커 실패 — 다음 대상(또는 로컬)으로 자동 전환", exc_info=True)
        finally:
            _photo_in_flight[target] = max(0, _photo_in_flight.get(target, 1) - 1)
    return await run_in_threadpool(predict_cataract, img)


@router.get("/healthz")
async def healthz():
    """프로세스가 HTTP 요청을 받을 수 있는지 확인하는 경량 liveness 체크."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz():
    """실제 이미지 분석을 받을 준비가 됐는지 확인하는 readiness 체크."""
    if (not vision.weights_loaded
            or not await run_in_threadpool(eye_detector.is_ready)
            or not await run_in_threadpool(eye_validator.is_ready)):
        return JSONResponse(status_code=503, content={"status": "not_ready", "model": "unavailable"})
    return {"status": "ready", "model": "ready"}


async def _check_ollama_worker(url: str) -> bool:
    try:
        parts = urlsplit(url)
        tags_url = urlunsplit((parts.scheme, parts.netloc, "/api/tags", "", ""))
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(tags_url)
            response.raise_for_status()
            models = response.json().get("models", [])
            names = {m.get("name", m.get("model", "")) for m in models}
            model = settings.ollama_model
            return model in names or (":" not in model and model + ":latest" in names)
    except Exception:
        return False


@router.get("/api/service-status")
async def service_status():
    """Presentation checks, separate from photo readiness. No secrets or remote addresses returned."""
    photo = (vision.weights_loaded
             and await run_in_threadpool(eye_detector.is_ready)
             and await run_in_threadpool(eye_validator.is_ready))
    checks = await asyncio.gather(*(_check_ollama_worker(u) for u in settings.ollama_url_list))
    ollama = any(checks)
    ready = bool(photo and ollama)
    return JSONResponse(status_code=200 if ready else 503, content={
        "status": "ready" if ready else "degraded",
        "services": {"photo": "ready" if photo else "unavailable",
                     "ollama": "ready" if ollama else "unavailable"},
        "note": "Ollama model availability checked; run a real generation before presenting.",
    })


async def _limited_stream(stream):
    """LLM 스트림 수를 제한하고 클라이언트 취소 시 슬롯을 즉시 반납한다."""
    slots = _get_llm_slots()
    acquire = asyncio.create_task(slots.acquire())
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
            slots.release()


@router.get("/api/nearby-clinics")
async def nearby_clinics(
    # 좌표 범위를 스키마에서 막는다 — 범위 밖 값을 그대로 넘기면 카카오/Overpass에
    # 무의미한 외부 요청만 나가고, 에러도 서드파티 쪽에서 뒤늦게 돌아온다.
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
):
    """현재 위치 주변 안과 검색 (카카오 로컬 REST API, 키 없으면 빈 목록)."""
    return await search_eye_clinics(lat, lng)

@router.post("/api/analyze-eye", dependencies=[Depends(require_admission)])
async def analyze_eye(file: UploadFile = File(...), source_compressed: bool = Form(False)):
    async with _get_inference_slots():
        img = await validate_and_read_image(file)
        # The browser may have resized/re-encoded a large JPEG. A reported
        # degraded original can only tighten the gate; false never clears the
        # server's independently decoded quantization flag.
        if source_compressed:
            img.info['heavy_jpeg_compression'] = True
        # 무거운 추론(MTCNN+ResNet)은 스레드풀 또는 원격 워커에서 실행 → 이벤트루프(다른 요청/스트림)를 막지 않음
        result = await _dispatch_photo_analysis(img)
    return {
        "status": "success",
        "closeup_suggested": False,
        "eye_score": None,
        "sharpness": None,
        "glare": None,
        # 사진 인식 기준 체크리스트. 화면이 항상 같은 모양을 그릴 수 있게 기본값을 둔다.
        "checks": [],
        **result,
    }

@router.post("/api/get-ai-opinion", dependencies=[Depends(require_admission)])
async def get_ai_opinion(req: GemmaRequest):
    stream = get_gemma_opinion_stream(
        req.cataract_res, req.amsler_res, req.chat_symptoms, req.lang,
        cataract_code=req.cataract_code,
        amsler_abnormal=req.amsler_abnormal,
        symptom_codes=req.symptom_codes,
        eye_asymmetric=req.eye_asymmetric,
        red_flags=req.red_flags,
        triage_level=req.triage_level,
        flag_codes=req.flag_codes,
    )
    # Fixed emergency advice needs no model resources and must not queue
    # behind slow ordinary generations.
    return StreamingResponse(
        stream if req.red_flags or req.triage_level == "urgent" else _limited_stream(stream),
        media_type="text/plain"
    )

@router.post("/api/chat-with-gemma", dependencies=[Depends(require_admission)])
async def chat_with_gemma(req: ChatRequest):
    stream = chat_with_gemma_stream(req.user_msg, req.context, req.lang,
                                   explain_results=req.explain_results, facts=req.facts,
                                   explain_required=req.explain_required, explain_fallback=req.explain_fallback)
    return StreamingResponse(
        # 고정 문장 설명은 모델을 부르지 않으므로 줄을 서지 않는다. 실험 모드(ai_checked)는 모델을 부른다.
        stream if (req.explain_results and settings.explain_mode == "fixed")
        or (not req.explain_results and is_score_question(req.user_msg)) else _limited_stream(stream),
        media_type="text/plain"
    )

async def _question_until_disconnect(req, request):
    """Stop optional generation promptly when the visitor skips or edits it."""
    async def generate():
        async with _get_llm_slots():
            return await generate_personalized_question(req)
    stopping = asyncio.Event()
    async def disconnected():
        while not stopping.is_set():
            if await request.is_disconnected():
                return
            try:
                await asyncio.wait_for(stopping.wait(), timeout=0.1)
            except asyncio.TimeoutError:
                pass
    work = asyncio.create_task(generate())
    gone = asyncio.create_task(disconnected())
    try:
        done, _ = await asyncio.wait({work, gone}, return_when=asyncio.FIRST_COMPLETED)
        if work in done:
            return await work
        raise HTTPException(499, detail="Client disconnected")
    finally:
        # is_disconnected uses an AnyIO cancellation scope. Stop the polling loop
        # cooperatively so an external cancellation cannot be swallowed there.
        stopping.set()
        if not work.done():
            work.cancel()
        await asyncio.gather(work, gone, return_exceptions=True)


@router.post("/api/generate-next-question", dependencies=[Depends(require_admission)])
async def generate_next_question_endpoint(req: QuestionGenRequest, request: Request):
    if not followup_questions.eligible_ids(req):
        return followup_questions.response()
    return await _question_until_disconnect(req, request)

@router.post("/api/translate-question", dependencies=[Depends(require_admission)])
async def translate_question_endpoint(req: QuestionTranslationRequest):
    async with _get_llm_slots():
        return await translate_personalized_question(req)


@router.post("/api/plain-findings")
async def plain_findings(req: PlainFindingsRequest):
    """검사 요약 해석을 쉬운 말로 바꿔 돌려준다.

    같은 언어의 원문과 정확히 일치하는 고정 표현만 사용한다.
    준비된 표현이 없는 줄은 원문을 유지하며 LLM을 호출하지 않는다.
    """
    return {"lines": await rewrite_findings(req.findings, req.lang)}
