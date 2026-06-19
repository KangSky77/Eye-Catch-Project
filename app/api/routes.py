from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse
from app.services.vision import predict_cataract, validate_and_read_image
from app.services.llm import get_gemma_opinion_stream, chat_with_gemma_stream, generate_next_question
from app.services.clinics import search_eye_clinics
from app.services.database import save_diagnosis
from app.schemas.ai import GemmaRequest, ChatRequest, QuestionGenRequest, SaveDiagnosisRequest

router = APIRouter()


@router.get("/api/nearby-clinics")
async def nearby_clinics(lat: float, lng: float):
    """현재 위치 주변 안과 검색 (카카오 로컬 REST API, 키 없으면 빈 목록)."""
    return await search_eye_clinics(lat, lng)

@router.post("/api/analyze-eye")
async def analyze_eye(file: UploadFile = File(...)):
    img = await validate_and_read_image(file)
    result = predict_cataract(img)
    return {
        "status": "success",
        "probability": result["probability"],
        "result": result["result"],
        "result_code": result["result_code"],
        "mode": result["mode"],                    # "face"면 얼굴에서 눈을 찾아 분석한 것
        "eyes_detected": result["eyes_detected"],
        "eye_probs": result["eye_probs"],
        "eyes": result["eyes"],                    # 눈별 [{side, probability, code}]
        "asymmetric": result["asymmetric"],        # 편측만 위험이면 True
    }

@router.post("/api/get-ai-opinion")
async def get_ai_opinion(req: GemmaRequest):
    return StreamingResponse(
        get_gemma_opinion_stream(
            req.cataract_res, req.amsler_res, req.chat_symptoms, req.lang,
            cataract_code=req.cataract_code,
            amsler_abnormal=req.amsler_abnormal,
            symptom_codes=req.symptom_codes,
            eye_asymmetric=req.eye_asymmetric,
        ),
        media_type="text/plain"
    )

@router.post("/api/chat-with-gemma")
async def chat_with_gemma(req: ChatRequest):
    return StreamingResponse(
        chat_with_gemma_stream(req.user_msg, req.context, req.lang),
        media_type="text/plain"
    )

@router.post("/api/generate-next-question")
async def generate_next_question_endpoint(req: QuestionGenRequest):
    question = await generate_next_question(req.lang, req.cataract_res, req.amsler_res, req.chat_history)
    return {"question": question}

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
    except Exception as e:
        # DB 연결 실패 시 앱 전체가 죽지 않도록 소프트 실패
        # 내부 에러 상세(호스트명 등)는 클라이언트에 노출하지 않고 서버 로그에만 남김
        print(f"⚠️  진단 저장 실패: {e}")
        return {"status": "skipped"}
