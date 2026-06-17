import json
import httpx
from app.core.config import settings

# 언어 코드 → LLM에게 지시할 언어 이름
LANG_NAMES = {
    "ko": "한국어 (Korean)",
    "en": "English",
    "es": "Español (Spanish)",
    "fr": "Français (French)",
    "ja": "日本語 (Japanese)",
    "zh": "中文 (Chinese)",
}

def _lang_name(lang: str) -> str:
    return LANG_NAMES.get(lang, "English")

def _build_opinion_prompt(cataract: str, amsler: str, symptoms: list[str], lang: str) -> str:
    symptom_text = ", ".join(symptoms) if symptoms else "없음"
    lang_name = _lang_name(lang)
    return f"""당신은 경험 많은 안과 전문의의 조수 AI 'Eye-Catch'입니다.
[가장 중요] 답변 전체를 반드시 {lang_name}로만 작성하세요. (Write your ENTIRE response ONLY in {lang_name}.)
다음 검사 결과를 바탕으로 환자에게 줄 맞춤형 소견서를 작성해주세요.
[검사 결과]
1. 백내장 AI 판독: {cataract}
2. 황반변성 자가진단(암슬러 격자): {amsler}
3. 문진 의심 소견: {symptom_text}
[작성 가이드라인]
- 환자분이라고 부르며 시작하세요.
- 위 검사 결과의 수치와 소견을 소견서 본문에 직접 인용하면서, 항목별로 그것이 '무엇을 의미하는지' 구체적으로 해석해주세요.
  (예: 백내장 확률이 높다면 수정체 혼탁 가능성과 그로 인한 증상, 암슬러 격자 이상이면 황반부 문제 가능성, 시야 좁아짐 응답이면 녹내장과의 연관성 등)
- 소견들의 시급성을 구분해주세요: 빠른 시일 내 진료가 필요한 항목과, 경과 관찰해도 되는 항목.
- 안과에 가면 받게 될 검사를 1~2개 구체적으로 언급해 마음의 준비를 돕세요. (예: 세극등 현미경 검사, 안저 검사, 안압 측정, OCT 등 결과와 관련된 것)
- 마지막에 이 환자의 소견과 직접 관련된 생활 관리 조언을 1~2개만 덧붙이세요.
- "눈은 소중하니 잘 관리하세요" 같은 뻔한 일반론과 인사치레는 금지합니다. 모든 문장이 이 환자의 결과에 근거해야 합니다.
- 6~9문장으로 작성하세요. 의료적 확정 진단처럼 말하지 말고 '~가능성', '~의심' 수준으로 표현하세요.
- 마크다운 문법(**, ##, 목록 기호)을 쓰지 말고 자연스러운 평문 문단으로 작성하세요.""".strip()

def _build_chat_prompt(user_msg: str, context: str, lang: str) -> str:
    lang_name = _lang_name(lang)
    return f"""당신은 안과 전문 상담 AI입니다.
[가장 중요] 답변 전체를 반드시 {lang_name}로만 작성하세요. (Write your ENTIRE response ONLY in {lang_name}.)
[진단결과 요약]
{context}
[응답 지침]
- 환자의 질문에 친절하고 구체적으로 답변하세요. "안내해 드릴 수 없다"는 식의 회피성 답변은 절대 하지 마세요.
- 일반적인 눈 건강 관리 수칙은 적극적으로 알려주세요. (예: 자외선 차단 선글라스, 금연, 혈당·혈압 관리, 눈 휴식, 어두운 곳 독서 피하기, 정기 검진 등 질문과 관련된 것)
- 단, 확정 진단·약 처방은 하지 말고, 정확한 진단을 위해 안과 방문도 함께 권하세요.
- 마크다운 문법(**, ##, 번호 목록 기호)을 쓰지 말고 자연스러운 평문 문장으로 3~6문장 작성하세요.
환자 질문: {user_msg}""".strip()

def _build_next_question_prompt(lang: str, cataract_res: str, amsler_res: str, history_text: str) -> str:
    lang_name = _lang_name(lang)
    return f"""당신은 안과 전문의 조수 AI입니다.
[가장 중요] 응답 언어는 반드시 {lang_name}로만 하세요. (Write your question ONLY in {lang_name}.)
현재 환자 상태:
- 백내장 AI 판독: {cataract_res}
- 황반변성 자가진단: {amsler_res}
[지금까지의 문진 내역]
{history_text}
위 상태와 문진 내역을 바탕으로, 환자의 눈 건강 상태를 더 자세히 파악하기 위한 새로운 맞춤형 질문을 딱 1개만 생성해주세요. 부가 설명 없이 질문 한 문장만 출력하세요.""".strip()

async def stream_ollama(prompt: str):
    timeout = httpx.Timeout(connect=10.0, read=settings.ollama_timeout_seconds, write=30.0, pool=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", settings.ollama_url, json={"model": settings.ollama_model, "prompt": prompt, "stream": True}) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line: continue
                try:
                    data = json.loads(line)
                    if token := data.get("response"): yield token
                except json.JSONDecodeError: continue

async def generate_ollama(prompt: str) -> str:
    timeout = httpx.Timeout(connect=10.0, read=settings.ollama_timeout_seconds, write=30.0, pool=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(settings.ollama_url, json={"model": settings.ollama_model, "prompt": prompt, "stream": False})
        response.raise_for_status()
        return response.json().get("response", "").strip()

async def get_gemma_opinion_stream(cataract: str, amsler: str, symptoms: list[str], lang: str = "ko"):
    try:
        async for chunk in stream_ollama(_build_opinion_prompt(cataract, amsler, symptoms, lang)): yield chunk
    except Exception as e: yield f"AI 서버 통신 오류: {str(e)}"

async def chat_with_gemma_stream(user_msg: str, context: str, lang: str = "ko"):
    try:
        async for chunk in stream_ollama(_build_chat_prompt(user_msg, context, lang)): yield chunk
    except Exception as e: yield f"챗봇 응답 오류: {str(e)}"

async def generate_next_question(lang: str, cataract_res: str, amsler_res: str, chat_history: list) -> str:
    # ChatHistoryItem은 Pydantic 모델이므로 .q / .a 속성으로 접근
    history_text = "\n".join([f"- 의사: {item.q}\n- 환자: {item.a}" for item in chat_history]).strip() or "아직 진행된 문진 대화가 없습니다."
    try:
        return await generate_ollama(_build_next_question_prompt(lang, cataract_res, amsler_res, history_text)) or "추가적으로 눈이 불편하신 곳이 있나요?"
    except Exception:
        return "추가적으로 눈이 불편하신 곳이 있나요?"