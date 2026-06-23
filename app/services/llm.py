import json
import logging
import asyncio
import httpx
from app.core.config import settings
from app.services import knowledge

logger = logging.getLogger(__name__)

# 하트비트 문자: 생성이 느려도(Ollama 콜드스타트/CPU) 스트림 연결이 끊기지 않도록
# 첫 토큰 전까지 주기적으로 보낸다. 폭이 0인 제로폭 공백이라 프론트가 무시/제거.
KEEPALIVE = chr(0x200B)     # zero-width space (U+200B)
KEEPALIVE_INTERVAL = 5.0    # 초
# 오류 마커: 스트림 중 발생한 오류를 '정상 소견'과 구분하기 위한 접두사.
# 프론트가 이 마커를 감지하면 에러로 처리(알림·DB저장 건너뜀). 일반 텍스트엔 안 나오는 시퀀스.
ERROR_MARKER = "⛔__ECERR__"   # ⛔__ECERR__

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

def _build_opinion_prompt(cataract: str, amsler: str, symptoms: list[str], lang: str,
                          reference: str = "", eye_asymmetric: bool = False) -> str:
    symptom_text = ", ".join(symptoms) if symptoms else "없음" if lang == "ko" else "None"
    lang_name = _lang_name(lang)
    reference_block = f"\n{reference}\n" if reference else ""
    if lang == "ko":
        asym_line = ("\n- 양쪽 눈의 백내장 위험도가 다릅니다(편측). 어느 쪽 눈이 더 위험한지 짚고, "
                     "한쪽 눈에만 진행된 백내장일 가능성과 양안 비교 검진의 필요성을 언급하세요."
                     if eye_asymmetric else "")
        return f"""당신은 경험 많은 안과 전문의의 조수 AI 'Eye-Catch'입니다.
[가장 중요] 답변 전체를 반드시 {lang_name}로만 작성하세요. (Write your ENTIRE response ONLY in {lang_name}.)
다음 검사 결과를 바탕으로 환자에게 줄 맞춤형 소견서를 작성해주세요.
[검사 결과]
1. 백내장 AI 판독: {cataract}
2. 황반변성 자가진단(암슬러 격자): {amsler}
3. 문진 의심 소견: {symptom_text}
{reference_block}[작성 가이드라인]
- 환자분이라고 부르며 시작하세요.
- 위 [참고 의학 정보]에 담긴 검사명·위험요인·관리법에 근거해 전문적으로 설명하되, 참고 정보에 없는 내용은 지어내지 마세요.
- 위 검사 결과의 수치와 소견을 소견서 본문에 직접 인용하면서, 항목별로 그것이 '무엇을 의미하는지' 구체적으로 해석해주세요.
  (예: 백내장 확률이 높다면 수정체 혼탁 가능성과 그로 인한 증상, 암슬러 격자 이상이면 황반부 문제 가능성, 시야 좁아짐 응답이면 녹내장과의 연관성 등){asym_line}
- 소견들의 시급성을 구분해주세요: 빠른 시일 내 진료가 필요한 항목과, 경과 관찰해도 되는 항목.
- 안과에 가면 받게 될 검사를 1~2개 구체적으로 언급해 마음의 준비를 돕세요. (예: 세극등 현미경 검사, 안저 검사, 안압 측정, OCT 등 결과와 관련된 것)
- 마지막에 이 환자의 소견과 직접 관련된 생활 관리 조언을 1~2개만 덧붙이세요.
- "눈은 소중하니 잘 관리하세요" 같은 뻔한 일반론과 인사치레는 금지합니다. 모든 문장이 이 환자의 결과에 근거해야 합니다.
- 6~9문장으로 작성하세요. 의료적 확정 진단처럼 말하지 말고 '~가능성', '~의심' 수준으로 표현하세요.
- 마크다운 문법(**, ##, 목록 기호)을 쓰지 말고 자연스러운 평문 문단으로 작성하세요.""".strip()
    else:
        asym_line = ("\n- Left and right eye cataract risk levels differ (asymmetric). Mention which eye is at higher risk, "
                     "explain the possibility of unilateral cataract, and suggest a bilateral comparative examination."
                     if eye_asymmetric else "")
        return f"""You are 'Eye-Catch', an expert assistant to an ophthalmologist.
[CRITICAL] Write your entire response ONLY in {lang_name}. Do NOT use English or other languages.

Based on the following test results, write a personalized screening opinion for the patient.
[Screening Results]
1. Cataract AI analysis: {cataract}
2. Macular Degeneration (Amsler Grid): {amsler}
3. Patient survey symptoms: {symptom_text}
{reference_block}[Guidelines]
- Start naturally with a polite, patient-facing greeting in {lang_name}.
- Base your advice strictly on the provided [Reference Medical Information] if available. Do not make up any medical facts or details that are not in the reference information.
- Quote the specific findings/numbers from the [Screening Results] in your text, and explain what they mean for the patient's eye health. (e.g. high cataract probability points to lens cloudiness, Amsler grid distortion implies macular issues, narrow field of vision implies glaucoma connection, etc.){asym_line}
- Distinguish the urgency of findings: which items require prompt medical attention vs. those that can just be monitored.
- Mention 1-2 specific clinical exams the patient might undergo at an ophthalmology clinic (e.g., Slit-lamp exam, OCT, intraocular pressure measurement, fundus exam) depending on their findings.
- Conclude with 1-2 personalized lifestyle or management tips directly related to these findings.
- Do not write generic advice like "eyes are precious, take care." Every sentence must relate to this patient's results.
- Keep the length between 6 to 9 sentences. Write in natural paragraphs without markdown formatting like bolding (**) or headings (##).""".strip()


def _build_chat_prompt(user_msg: str, context: str, lang: str, reference: str = "") -> str:
    lang_name = _lang_name(lang)
    reference_block = f"\n{reference}\n" if reference else ""
    if lang == "ko":
        return f"""당신은 안과 전문 상담 AI입니다.
[가장 중요] 답변 전체를 반드시 {lang_name}로만 작성하세요. (Write your ENTIRE response ONLY in {lang_name}.)
[진단결과 요약]
{context}
{reference_block}[응답 지침]
- 위 [참고 의학 정보]가 있으면 그 내용에 근거해 정확히 답하고, 없는 사실은 지어내지 마세요.
- 환자의 질문에 친절하고 구체적으로 답변하세요. "안내해 드릴 수 없다"는 식의 회피성 답변은 절대 하지 마세요.
- 일반적인 눈 건강 관리 수칙은 적극적으로 알려주세요. (예: 자외선 차단 선글라스, 금연, 혈당·혈압 관리, 눈 휴식, 어두운 곳 독서 피하기, 정기 검진 등 질문과 관련된 것)
- 단, 확정 진단·약 처방은 하지 말고, 정확한 진단을 위해 안과 방문도 함께 권하세요.
- 마크다운 문법(**, ##, 번호 목록 기호)을 쓰지 말고 자연스러운 평문 문장으로 3~6문장 작성하세요.
환자 질문: {user_msg}""".strip()
    else:
        return f"""You are an ophthalmology consultation assistant.
[CRITICAL] Write your entire response ONLY in {lang_name}. Do NOT use English or other languages.

[Patient Diagnosis Summary]
{context}
{reference_block}[Response Guidelines]
- If [Reference Medical Information] is provided, base your answer strictly on those facts. Do not make up any facts or details that are not in the reference information.
- Answer the patient's question kindly, professionally, and directly. Do not use evasive phrases like "I cannot help with this."
- Actively share general eye health care tips related to the question (e.g., UV sunglasses, smoking cessation, blood sugar/pressure management, resting eyes, avoiding reading in the dark, regular eye checks).
- Do not provide a final medical diagnosis or prescribe medications. Suggest visiting an ophthalmologist for a formal diagnosis.
- Keep the length between 3 to 6 sentences. Write in natural paragraphs without markdown formatting like bolding (**) or headings (##).
Patient Question: {user_msg}""".strip()


def _build_next_question_prompt(lang: str, cataract_res: str, amsler_res: str, history_text: str) -> str:
    lang_name = _lang_name(lang)
    if lang == "ko":
        return f"""당신은 안과 전문의 조수 AI입니다.
[가장 중요] 응답 언어는 반드시 {lang_name}로만 하세요. (Write your question ONLY in {lang_name}.)
현재 환자 상태:
- 백내장 AI 판독: {cataract_res}
- 황반변성 자가진단: {amsler_res}
[지금까지의 문진 내역]
{history_text}
위 상태와 문진 내역을 바탕으로, 환자의 눈 건강 상태를 더 자세히 파악하기 위한 새로운 맞춤형 질문을 딱 1개만 생성해주세요. 부가 설명 없이 질문 한 문장만 출력하세요.""".strip()
    else:
        return f"""You are an assistant to an ophthalmologist.
[CRITICAL] Write your question ONLY in {lang_name}. Do NOT use English or other languages.

Current Patient State:
- Cataract AI result: {cataract_res}
- Macular Degeneration (Amsler Grid): {amsler_res}
[Ophthalmology Screening History]
{history_text}

Based on the patient's state and history, generate exactly one new personalized question to better understand their eye health. Output ONLY the friendly question sentence itself, with no explanations, greetings, or extra words.""".strip()

async def stream_ollama(prompt: str):
    timeout = httpx.Timeout(connect=10.0, read=settings.ollama_timeout_seconds, write=30.0, pool=10.0)
    # keep_alive=-1: 모델을 VRAM에 영구 상주시켜 콜드스타트(최초 로딩 ~45초) 제거
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", settings.ollama_url, json={"model": settings.ollama_model, "prompt": prompt, "stream": True, "keep_alive": -1}) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line: continue
                try:
                    data = json.loads(line)
                    if token := data.get("response"): yield token
                except json.JSONDecodeError: continue


async def stream_with_keepalive(prompt: str):
    """Ollama 스트림을 소비하되, 첫 토큰이 느리면(콜드스타트/CPU) 주기적으로
    하트비트를 내보내 ngrok·모바일에서 연결이 끊기는 것을 방지한다.
    실제 토큰이 하나라도 오면 그 뒤로는 그대로 흘려보낸다."""
    q: asyncio.Queue = asyncio.Queue()

    async def producer():
        try:
            async for tok in stream_ollama(prompt):
                await q.put(("tok", tok))
        except Exception:
            # 내부 예외 메시지(호스트·포트 등)는 서버 로그에만 남기고, 클라이언트에는
            # 일반 코드만 전달한다 (네트워크 응답에 내부 정보가 노출되지 않도록).
            logger.error("⚠️  Ollama 스트리밍 오류", exc_info=True)
            await q.put(("err", "AI_SERVER_ERROR"))
        finally:
            await q.put(("end", None))

    task = asyncio.create_task(producer())
    try:
        while True:
            try:
                kind, val = await asyncio.wait_for(q.get(), timeout=KEEPALIVE_INTERVAL)
            except asyncio.TimeoutError:
                yield KEEPALIVE          # 아직 생성 중 → 연결 유지용 하트비트
                continue
            if kind == "end":
                break
            if kind == "err":
                yield ERROR_MARKER + val   # 오류는 마커를 붙여 정상 토큰과 구분
                break
            yield val                      # 실제 토큰
    finally:
        task.cancel()

async def generate_ollama(prompt: str) -> str:
    timeout = httpx.Timeout(connect=10.0, read=settings.ollama_timeout_seconds, write=30.0, pool=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(settings.ollama_url, json={"model": settings.ollama_model, "prompt": prompt, "stream": False, "keep_alive": -1})
        response.raise_for_status()
        return response.json().get("response", "").strip()


async def warmup_ollama():
    """서버 시작 시 Gemma 모델을 미리 VRAM에 올려둔다(콜드스타트 제거).
    Ollama가 꺼져 있어도 서버는 정상 기동하도록 실패는 조용히 무시."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            await client.post(settings.ollama_url, json={
                "model": settings.ollama_model, "prompt": "ok", "stream": False, "keep_alive": -1,
            })
        return True
    except Exception:
        logger.warning("⚠️  Gemma 워밍업 실패(Ollama 미실행 가능)", exc_info=True)
        return False

async def get_gemma_opinion_stream(cataract: str, amsler: str, symptoms: list[str], lang: str = "ko",
                                   cataract_code: str = "", amsler_abnormal: bool = False,
                                   symptom_codes: list[str] = None, eye_asymmetric: bool = False):
    # RAG: 환자 결과에 맞는 안과 참고지식을 검색해 프롬프트에 주입
    reference = knowledge.format_reference(
        knowledge.retrieve_for_opinion(cataract_code, amsler_abnormal, symptom_codes)
    )
    prompt = _build_opinion_prompt(cataract, amsler, symptoms, lang, reference, eye_asymmetric)
    try:
        async for chunk in stream_with_keepalive(prompt): yield chunk
    except Exception:
        logger.error("⚠️  소견서 스트리밍 오류", exc_info=True)
        yield ERROR_MARKER + "AI_SERVER_ERROR"

async def chat_with_gemma_stream(user_msg: str, context: str, lang: str = "ko"):
    # RAG: 질문 키워드로 관련 참고지식을 검색해 주입
    reference = knowledge.format_reference(knowledge.retrieve_for_chat(user_msg))
    try:
        async for chunk in stream_with_keepalive(_build_chat_prompt(user_msg, context, lang, reference)): yield chunk
    except Exception:
        logger.error("⚠️  챗봇 응답 스트리밍 오류", exc_info=True)
        yield ERROR_MARKER + "AI_SERVER_ERROR"

async def generate_next_question(lang: str, cataract_res: str, amsler_res: str, chat_history: list) -> str:
    # ChatHistoryItem은 Pydantic 모델이므로 .q / .a 속성으로 접근
    history_text = "\n".join([f"- 의사: {item.q}\n- 환자: {item.a}" for item in chat_history]).strip() or "아직 진행된 문진 대화가 없습니다."
    try:
        return await generate_ollama(_build_next_question_prompt(lang, cataract_res, amsler_res, history_text)) or "추가적으로 눈이 불편하신 곳이 있나요?"
    except Exception:
        return "추가적으로 눈이 불편하신 곳이 있나요?"