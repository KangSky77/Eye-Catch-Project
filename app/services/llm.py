import json
import logging
import asyncio
import httpx
from app.core.config import settings
from app.services import knowledge
from app.services import safety

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
    """생활 관리 조언용 프롬프트.

    이 프롬프트는 의도적으로 '검사 결과 해석'을 시키지 않는다. 편측(eye_asymmetric)을
    포함한 모든 의학적 해석은 프론트가 코드로 결정론적으로 생성한다(app-findings.js).
    LLM에게 해석을 맡겼더니 실제로 "암슬러가 정상이므로 녹내장 가능성이 낮다" 같은
    문장을 만들어냈기 때문이다. 인자는 호출부 호환을 위해 남기되 프롬프트에 넣지 않는다."""
    symptom_text = ", ".join(symptoms) if symptoms else "없음" if lang == "ko" else "None"
    lang_name = _lang_name(lang)
    reference_block = f"\n{reference}\n" if reference else ""
    if lang == "ko":
        return f"""당신은 안과 검진을 앞둔 분에게 생활 관리 조언을 드리는 도우미입니다.
[가장 중요] 답변 전체를 반드시 {lang_name}로만 작성하세요.

[이미 확정된 검사 요약 — 참고만 하고 절대 재해석하지 마세요]
1. 백내장 AI 판독: {cataract}
2. 황반변성 자가진단(암슬러 격자): {amsler}
3. 문진에서 확인된 항목: {symptom_text}
{reference_block}[절대 금지 — 어기면 답변이 폐기됩니다]
- 검사 결과를 해석하거나 의미를 설명하지 마세요. 해석은 이미 앱이 따로 제공합니다.
- 어떤 질환의 가능성이 '높다/낮다'고 말하지 마세요. 특히 '가능성이 낮다', '안심하셔도 된다'는 금지입니다.
  (선별검사는 질환을 배제할 수 없습니다)
- 숫자나 퍼센트를 쓰지 마세요. '확률'이라는 단어도 쓰지 마세요.
- 한 문장에서 서로 다른 질환을 연결짓지 마세요. (예: 암슬러 결과로 녹내장을 논하는 것)
- 진단하지 마세요.

[해야 할 일]
- 환자분이라고 부르며 짧게 시작하세요.
- 위 [참고 의학 정보]에 근거해, 안과에 가면 받게 될 검사를 1~2개 소개해 마음의 준비를 돕세요.
  (예: 세극등 현미경 검사, 안저 검사, 안압 측정, OCT)
- 문진에서 확인된 항목과 관련된 생활 관리 조언을 2~3개 구체적으로 알려주세요.
  (자외선 차단, 금연, 혈당·혈압 관리, 눈 휴식, 정기 검진 등 참고 정보에 있는 것)
- "눈은 소중합니다" 같은 뻔한 일반론은 쓰지 마세요.
- 4~6문장, 마크다운 없이 자연스러운 평문으로 작성하세요.""".strip()
    else:
        return f"""You help someone prepare for an eye clinic visit with practical lifestyle advice.
[CRITICAL] Write your entire response ONLY in {lang_name}.

[Already-finalized screening summary — for context only. Do NOT reinterpret it.]
1. Cataract AI analysis: {cataract}
2. Macular self-test (Amsler grid): {amsler}
3. Items flagged in the questionnaire: {symptom_text}
{reference_block}[STRICTLY FORBIDDEN — violations cause the answer to be discarded]
- Do NOT interpret or explain what the results mean. The app already provides that separately.
- Do NOT say any condition is likely or unlikely. Never say "low risk", "unlikely", or "no need to worry".
  (A screening test cannot rule out disease.)
- Do NOT use numbers or percentages. Do NOT use the word "probability".
- Do NOT link two different conditions in one sentence (e.g. drawing a glaucoma conclusion from an Amsler result).
- Do NOT diagnose.

[What to do]
- Start with a short, polite greeting in {lang_name}.
- Based on the [Reference Medical Information], name 1-2 exams they may receive at the clinic
  (e.g. slit-lamp exam, fundus exam, intraocular pressure measurement, OCT) so they know what to expect.
- Give 2-3 concrete lifestyle tips related to the flagged questionnaire items
  (UV protection, smoking cessation, blood sugar/pressure control, eye rest, regular check-ups).
- Avoid generic filler like "eyes are precious".
- 4-6 sentences, plain prose, no markdown.""".strip()


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
- 단, 확정 진단·약 처방은 하지 마세요.
- 어떤 질환의 가능성이 '낮다'거나 '안심해도 된다'고 말하지 마세요. 선별검사는 질환을 배제할 수 없습니다.
- 숫자·퍼센트·'확률'이라는 표현을 쓰지 마세요.
- 한 문장에서 서로 다른 질환을 연결짓지 마세요.
- 정확한 진단을 위해 안과 방문을 함께 권하세요.
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
- Do not provide a final medical diagnosis or prescribe medications.
- Never say a condition is unlikely or that there is no need to worry — a screening test cannot rule out disease.
- Do not use numbers, percentages, or the word "probability".
- Do not link two different conditions in a single sentence.
- Suggest visiting an ophthalmologist for a formal diagnosis.
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

def _ollama_timeout() -> httpx.Timeout:
    return httpx.Timeout(connect=10.0, read=settings.ollama_timeout_seconds, write=30.0, pool=10.0)


def _ollama_payload(prompt: str, stream: bool) -> dict:
    # keep_alive=-1: 모델을 VRAM에 영구 상주시켜 콜드스타트(최초 로딩 ~45초) 제거
    return {"model": settings.ollama_model, "prompt": prompt, "stream": stream, "keep_alive": -1}


async def stream_ollama(prompt: str):
    async with httpx.AsyncClient(timeout=_ollama_timeout()) as client:
        async with client.stream("POST", settings.ollama_url, json=_ollama_payload(prompt, stream=True)) as response:
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

async def sanitized_stream(prompt: str):
    """스트림을 문장 단위로 버퍼링해 안전 필터를 통과한 문장만 내보낸다.

    왜 문장 단위인가: 토큰을 그대로 흘리면 위험한 문장이 화면에 찍힌 뒤에야 걸러낼 수 있다.
    반대로 전체를 다 받고 검사하면 스트리밍의 이점이 사라진다. 문장이 끝나는 순간에
    검사해서 통과한 것만 내보내면 둘 다 지킬 수 있다.

    하트비트와 오류 마커는 검사 대상이 아니므로 그대로 통과시킨다.
    """
    buf = ""
    dropped: list[str] = []
    async for chunk in stream_with_keepalive(prompt):
        if chunk == KEEPALIVE:
            yield chunk                     # 연결 유지용 — 내용이 아니다
            continue
        if chunk.startswith(ERROR_MARKER):
            yield chunk
            return
        buf += chunk
        # 완성된 문장이 생길 때마다 검사해서 내보낸다
        while True:
            m = safety._SENT_SPLIT.search(buf)
            if not m:
                break
            sentence, buf = buf[:m.end()], buf[m.end():]
            why = safety.check_sentence(sentence.strip())
            if why:
                dropped.append(why)
                logger.warning("⚠️  안전 필터가 LLM 문장을 제거: %s | %s", why, sentence.strip()[:120])
            else:
                yield sentence
    # 마지막 문장(종결부호 없이 끝난 경우)
    tail = buf.strip()
    if tail:
        why = safety.check_sentence(tail)
        if why:
            dropped.append(why)
            logger.warning("⚠️  안전 필터가 LLM 문장을 제거: %s | %s", why, tail[:120])
        else:
            yield tail
    if dropped:
        logger.warning("⚠️  LLM 안전 필터 제거 %d문장 (사유: %s)", len(dropped), ", ".join(sorted(set(dropped))))


async def generate_ollama(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=_ollama_timeout()) as client:
        response = await client.post(settings.ollama_url, json=_ollama_payload(prompt, stream=False))
        response.raise_for_status()
        return response.json().get("response", "").strip()


async def warmup_ollama():
    """서버 시작 시 Gemma 모델을 미리 VRAM에 올려둔다(콜드스타트 제거).
    Ollama가 꺼져 있어도 서버는 정상 기동하도록 실패는 조용히 무시."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            await client.post(settings.ollama_url, json=_ollama_payload("ok", stream=False))
        return True
    except Exception:
        logger.warning("⚠️  Gemma 워밍업 실패(Ollama 미실행 가능)", exc_info=True)
        return False

async def get_gemma_opinion_stream(cataract: str, amsler: str, symptoms: list[str], lang: str = "ko",
                                   cataract_code: str = "", amsler_abnormal: bool = False,
                                   symptom_codes: list[str] | None = None, eye_asymmetric: bool = False):
    # RAG: 환자 결과에 맞는 안과 참고지식을 검색해 프롬프트에 주입
    reference = knowledge.format_reference(
        knowledge.retrieve_for_opinion(cataract_code, amsler_abnormal, symptom_codes)
    )
    prompt = _build_opinion_prompt(cataract, amsler, symptoms, lang, reference, eye_asymmetric)
    try:
        # 안전 필터 경유 — 해석·확률·배제·질환 교차 문장은 화면에 닿기 전에 제거된다
        async for chunk in sanitized_stream(prompt): yield chunk
    except Exception:
        logger.error("⚠️  소견서 스트리밍 오류", exc_info=True)
        yield ERROR_MARKER + "AI_SERVER_ERROR"

async def chat_with_gemma_stream(user_msg: str, context: str, lang: str = "ko"):
    # RAG: 질문 키워드로 관련 참고지식을 검색해 주입
    reference = knowledge.format_reference(knowledge.retrieve_for_chat(user_msg))
    try:
        # 자유 질문은 소견서보다 더 자유롭게 흘러가므로 필터가 더 중요하다
        async for chunk in sanitized_stream(_build_chat_prompt(user_msg, context, lang, reference)): yield chunk
    except Exception:
        logger.error("⚠️  챗봇 응답 스트리밍 오류", exc_info=True)
        yield ERROR_MARKER + "AI_SERVER_ERROR"

async def generate_next_question(lang: str, cataract_res: str, amsler_res: str, chat_history: list) -> str:
    # ChatHistoryItem은 Pydantic 모델이므로 .q / .a 속성으로 접근
    history_text = "\n".join([f"- 의사: {item.q}\n- 환자: {item.a}" for item in chat_history]).strip() or "아직 진행된 문진 대화가 없습니다."
    try:
        # 실패/빈 응답이면 빈 문자열 반환 → 프론트(app-chat.js)가 선택 언어의
        # 기본 질문(nextq_fallback)으로 대체한다. 여기서 한국어 문장을 고정 반환하면
        # 영어 등 다른 언어 사용자에게 한국어 질문이 나가므로 폴백은 프론트에 위임.
        return await generate_ollama(_build_next_question_prompt(lang, cataract_res, amsler_res, history_text))
    except Exception:
        logger.warning("⚠️  동적 문진 질문 생성 실패 — 프론트 기본 질문으로 폴백", exc_info=True)
        return ""