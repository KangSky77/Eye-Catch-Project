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

[해야 할 일 — 정확히 3줄 요약]
아래 순서로 딱 3줄만 쓰세요. 한 줄은 한 문장이고, 줄과 줄 사이는 줄바꿈 하나로만 구분합니다.
번호·글머리 기호·마크다운·제목·인사말은 쓰지 마세요. 3줄을 넘기면 답변이 폐기됩니다.
1줄째: 위 [참고 의학 정보]에 근거해, 안과에 가면 받게 될 검사 1~2개를 소개해 마음의 준비를 돕는 문장.
       (예: 세극등 현미경 검사, 안저 검사, 안압 측정, OCT)
2줄째: 문진에서 확인된 항목과 직접 관련된 생활 관리 조언 한 가지.
       (자외선 차단, 금연, 혈당·혈압 관리, 눈 휴식 등 참고 정보에 있는 것)
3줄째: 또 다른 생활 관리 조언 한 가지, 또는 정기 검진 권유.
- "눈은 소중합니다" 같은 뻔한 일반론은 쓰지 마세요. 각 줄은 이 환자의 문진 항목과 연결돼야 합니다.""".strip()
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

[What to do — exactly a 3-line summary]
Write exactly 3 lines in this order. Each line is one sentence; separate lines with a single line break only.
No numbering, bullets, markdown, headings, or greetings. More than 3 lines and the answer is discarded.
Line 1: Based on the [Reference Medical Information], name 1-2 exams they may receive at the clinic
        (e.g. slit-lamp exam, fundus exam, intraocular pressure measurement, OCT) so they know what to expect.
Line 2: One concrete lifestyle tip directly related to the flagged questionnaire items
        (UV protection, smoking cessation, blood sugar/pressure control, eye rest — from the reference).
Line 3: One more lifestyle tip, or a reminder to get regular check-ups.
- Avoid generic filler like "eyes are precious". Every line must connect to this patient's flagged items.""".strip()


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


# 고정 문진 18문항(static/data.js의 riskQuestions + symptomQuestions)이 이미 다루는 주제.
# 프롬프트에 금지 목록으로 넣지 않으면 LLM이 거의 매번 이 중 하나를 되묻는다 —
# 실사용에서 "안개가 낀 것처럼 뿌옇게 보이나요?"(고정 문항)를 물은 직후
# "사물의 경계가 흐릿하게 보이나요?"를 생성했다(2026-09-04 실기기 확인).
# data.js의 문항을 고치면 이 목록도 함께 갱신할 것.
_COVERED_TOPICS_KO = (
    "나이, 당뇨, 고혈압, 가족력, 흡연, "
    "급성 눈 통증·두통·무지개 테, 갑작스러운 시력 저하, "
    "빛 번짐·눈부심, 안개처럼 뿌옇게 보임, 안경 도수 변경, "
    "중심 시야의 글자 빠짐, 안압, 고도근시, 주변 시야, "
    "당뇨 유병 기간, 안저 검사 여부, 비문증, 최근 안과 검진 여부"
)
_COVERED_TOPICS_EN = (
    "age, diabetes, hypertension, family history, smoking, "
    "acute eye pain with headache/halos, sudden vision loss, "
    "glare/light scatter, foggy or hazy vision, changing glasses prescription, "
    "missing letters in central vision, intraocular pressure, high myopia, peripheral vision, "
    "diabetes duration, fundus exam history, floaters, recent eye check-up"
)

# 고정 문항이 의도적으로 다루지 않는 영역. 여기로 유도해야 새로운 정보가 들어온다.
_OPEN_AREAS_KO = (
    "- 증상이 언제부터 시작됐는지 / 최근 몇 달 사이 빠르게 나빠졌는지\n"
    "- 한쪽 눈만 그런지, 양쪽 다 그런지 (편측성)\n"
    "- 일상 활동에 미치는 영향 (밤 운전을 피하게 됐는지, 책이나 휴대폰 글씨를 예전보다 키웠는지, 계단·문턱에서 불안한지)\n"
    "- 스테로이드(먹는 약·안약·연고)를 오래 쓴 적이 있는지\n"
    "- 눈 수술이나 눈을 다친 적이 있는지\n"
    "- 야외에서 오래 일하거나 자외선에 많이 노출되는지"
)
_OPEN_AREAS_EN = (
    "- When the symptoms started / whether they worsened quickly in recent months\n"
    "- Whether it affects one eye only or both (laterality)\n"
    "- Impact on daily life (avoiding night driving, enlarging text on books or phone, feeling unsure on stairs)\n"
    "- Long-term steroid use (oral, eye drops, or ointment)\n"
    "- Past eye surgery or eye injury\n"
    "- Working outdoors for long hours or heavy UV exposure"
)


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
위 상태와 문진 내역을 바탕으로, 아직 확인되지 않은 정보를 얻기 위한 질문을 딱 1개만 생성해주세요.

[이미 물어본 주제 — 절대 다시 묻지 마세요]
{_COVERED_TOPICS_KO}
위 주제를 표현만 바꿔서 되묻는 것도 금지입니다.
(예: '뿌옇게 보이나요'를 이미 물었으므로 '흐릿하게 보이나요', '선명하지 않나요'도 금지)
[지금까지의 문진 내역]에 이미 나온 질문과 비슷한 것도 금지입니다.

[대신 이런 영역에서 고르세요 — 아직 아무도 묻지 않았습니다]
{_OPEN_AREAS_KO}

[반드시 지켜야 할 제약]
- 화면에는 '네'와 '아니오' 버튼 두 개뿐입니다. 환자는 그 둘 중 하나로만 답할 수 있습니다.
- 따라서 반드시 '네' 또는 '아니오'로 답할 수 있는 질문만 만드세요.
- 서술형 질문은 절대 금지입니다: "설명해 주시겠어요", "어떤가요", "어떻게", "얼마나", "무엇을", "말씀해 주세요" 같은 표현을 쓰지 마세요.
- 진단하거나 질환 이름을 말하지 마세요. 증상·이력·생활만 물으세요.
- 한 문장, 60자 이내로 쓰세요.
- 좋은 예: "요즘 밤에는 운전을 되도록 피하게 되셨나요?" / "한쪽 눈만 유독 불편하신가요?"
- 나쁜 예: "시력 변화에 대해 자세히 설명해 주시겠어요?" (네/아니오로 답할 수 없음)

부가 설명 없이 질문 한 문장만 출력하세요.""".strip()
    else:
        return f"""You are an assistant to an ophthalmologist.
[CRITICAL] Write your question ONLY in {lang_name}. Do NOT use English or other languages.

Current Patient State:
- Cataract AI result: {cataract_res}
- Macular Degeneration (Amsler Grid): {amsler_res}
[Ophthalmology Screening History]
{history_text}

Generate exactly one question that gathers information not yet collected.

[ALREADY ASKED — never ask about these again]
{_COVERED_TOPICS_EN}
Rewording them is also forbidden (e.g. "foggy vision" was asked, so "blurry" or "not sharp" is also banned).
Anything similar to a question already in the screening history above is forbidden.

[Choose from these areas instead — nothing has asked about them yet]
{_OPEN_AREAS_EN}

[HARD CONSTRAINTS]
- The screen has only two buttons: "Yes" and "No". The patient can answer ONLY with one of those.
- Therefore the question MUST be answerable with a plain Yes or No.
- Open-ended questions are forbidden. Never use "describe", "explain", "how", "how much", "what", "which", "tell me about".
- Do NOT diagnose or name a disease. Ask only about symptoms, history, or daily life.
- One sentence, under 100 characters.
- Good: "Have you started avoiding driving at night?" / "Is only one of your eyes bothering you?"
- Bad: "Could you describe your vision changes in detail?" (cannot be answered Yes/No)

Output ONLY the question sentence itself, with no explanations, greetings, or extra words.""".strip()

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
        # 취소를 요청만 하고 버리면 종료 시 "Task was destroyed" 경고가 날 수 있다.
        # 생산자가 정상 종료된 경우에도 gather는 즉시 끝난다.
        await asyncio.gather(task, return_exceptions=True)

async def sanitized_stream(prompt: str):
    """스트림을 문장 단위로 버퍼링해 안전 필터를 통과한 문장만 내보낸다.

    왜 문장 단위인가: 토큰을 그대로 흘리면 위험한 문장이 화면에 찍힌 뒤에야 걸러낼 수 있다.
    반대로 전체를 다 받고 검사하면 스트리밍의 이점이 사라진다. 문장이 끝나는 순간에
    검사해서 통과한 것만 내보내면 둘 다 지킬 수 있다.

    하트비트와 오류 마커는 검사 대상이 아니므로 그대로 통과시킨다.
    """
    buf = ""
    dropped: list[str] = []
    emitted = False
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
            m = safety.SENT_SPLIT.search(buf)
            if not m:
                break
            sentence, buf = buf[:m.end()], buf[m.end():]
            why = safety.check_sentence(sentence.strip())
            if why:
                dropped.append(why)
                logger.warning("⚠️  안전 필터가 LLM 문장을 제거: %s | %s", why, sentence.strip()[:120])
            else:
                # 공백만 내보낸 것은 '내용을 냈다'고 볼 수 없다 — 화면에는 빈 칸으로 보인다
                emitted = emitted or bool(sentence.strip())
                yield sentence
    # 마지막 문장(종결부호 없이 끝난 경우)
    tail = buf.strip()
    if tail:
        why = safety.check_sentence(tail)
        if why:
            dropped.append(why)
            logger.warning("⚠️  안전 필터가 LLM 문장을 제거: %s | %s", why, tail[:120])
        else:
            emitted = True
            yield tail
    if dropped:
        logger.warning("⚠️  LLM 안전 필터 제거 %d문장 (사유: %s)", len(dropped), ", ".join(sorted(set(dropped))))
    # 내용이 하나도 안 나갔으면 성공으로 넘겨선 안 된다.
    #
    # 'dropped가 있을 때'로만 막으면 세 경우 중 하나만 잡힌다:
    #   ① 금지 문장만 생성됨          → dropped 있음  (막힘)
    #   ② 모델이 아무것도 생성 안 함   → dropped 없음  (그냥 통과 → 빈 소견이 '완료'로)
    #   ③ 공백만 생성됨               → dropped 없음  (그냥 통과)
    # 셋 다 사용자에게는 '소견서가 비어 있다'는 같은 결과이고, 할 일도 같다(재생성).
    # 위 오류 경로는 return으로 먼저 빠져나가므로 여기서 마커가 중복될 일은 없다.
    if not emitted:
        reason = "AI_FILTER_EMPTY" if dropped else "AI_EMPTY_RESPONSE"
        logger.warning("⚠️  LLM 소견이 비어 있음 — 프론트에 재생성을 안내한다 (%s)", reason)
        yield ERROR_MARKER + reason


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

# 화면에는 '네/아니오' 버튼뿐이라, 서술형 질문이 나오면 사용자가 답할 방법이 없다.
# 프롬프트로 제약을 걸어도 LLM이 가끔 어기므로 서버에서 한 번 더 거른다.
# 여기 걸리면 빈 문자열을 반환 → 프론트가 선택 언어의 기본 질문으로 대체한다.
_OPEN_ENDED_MARKERS = (
    # 한국어
    "설명해", "말씀해", "말해 주", "어떤가요", "어떠신가요", "어떻게", "얼마나",
    "무엇", "어느 정도", "묘사", "알려주세요", "적어주",
    # 영어 및 기타 언어에서 공통으로 쓰이는 의문사
    "describe", "explain", "how much", "how long", "how often", "how would",
    "what ", "which ", "tell me", "décrivez", "expliquez", "comment ",
    "combien", "describa", "explique", "cómo", "cuánto", "詳しく", "どのように",
    "どのくらい", "説明", "教えてください", "详细", "如何", "多久", "描述",
    # 선택형 질문은 예/아니오로 어느 쪽인지 전달할 수 없어 자유 입력으로 받는다.
    "one eye or both", "one or both eyes", "한쪽인가요", "한쪽 눈인가요",
    "한쪽 눈 또는 양쪽", "한쪽 눈이나 양쪽", "한쪽 눈과 양쪽",
)


# 생성된 질문 길이 상한. app/schemas/ai.py의 ChatHistoryItem.q(max_length=500)와 맞춘다 —
# 맞춤 질문은 다음 회차 요청에 chat_history로 되돌아오므로 이 상한을 넘으면 422가 난다.
MAX_QUESTION_CHARS = 500


def _is_yes_no_question(q: str) -> bool:
    """네/아니오로 답할 수 있는 질문인지 대략 판별한다(보수적: 애매하면 거부)."""
    if not q or not q.strip():
        return False
    low = q.strip().lower()
    return not any(m in low for m in _OPEN_ENDED_MARKERS)

async def generate_next_question(lang: str, cataract_res: str, amsler_res: str, chat_history: list) -> tuple[str, str]:
    """(질문, 답변형식) 반환. 답변형식은 "yesno" | "text"."""
    # ChatHistoryItem은 Pydantic 모델이므로 .q / .a 속성으로 접근
    if lang == "ko":
        q_label, a_label, empty = "의사", "환자", "아직 진행된 문진 대화가 없습니다."
    else:   # 프롬프트 언어 일관성 — 한국어 라벨이 섞이면 모델이 한국어로 답할 확률이 올라간다
        q_label, a_label, empty = "Doctor", "Patient", "No screening conversation yet."
    history_text = "\n".join(
        [f"- {q_label}: {item.q}\n- {a_label}: {item.a}" for item in chat_history]
    ).strip() or empty
    try:
        # 실패/빈 응답이면 빈 문자열 반환 → 프론트(app-chat.js)가 선택 언어의
        # 기본 질문(nextq_fallback)으로 대체한다. 여기서 한국어 문장을 고정 반환하면
        # 영어 등 다른 언어 사용자에게 한국어 질문이 나가므로 폴백은 프론트에 위임.
        q = await generate_ollama(_build_next_question_prompt(lang, cataract_res, amsler_res, history_text))
        q = (q or "").strip()
        if not q:
            return "", "yesno"
        # 맞춤 질문이 2회차부터는 chat_history로 되돌아오는데, ChatHistoryItem.q의 상한이
        # 500자다(app/schemas/ai.py). 넘기면 다음 요청이 422로 거부되고 프론트는 그것을
        # 조용히 기본 질문으로 폴백해버린다. 애초에 이 길이면 '한 문장 질문'이 아니라
        # 모델이 장황하게 늘어놓은 것이므로, 자르지 말고 버려서 기본 질문을 쓰게 한다.
        if len(q) > MAX_QUESTION_CHARS:
            logger.warning("⚠️  동적 문진 질문이 너무 김(%d자) — 기본 질문으로 폴백", len(q))
            return "", "yesno"
        # 프롬프트로 예/아니오를 요구하지만 LLM이 가끔 서술형을 낸다.
        # 예전에는 그런 질문을 버렸는데, 좋은 질문인 경우가 많아 버리기 아깝다.
        # 대신 종류를 알려주고 프론트가 자유 입력칸을 띄우게 한다.
        return q, ("yesno" if _is_yes_no_question(q) else "text")
    except Exception:
        logger.warning("⚠️  동적 문진 질문 생성 실패 — 프론트 기본 질문으로 폴백", exc_info=True)
        return "", "yesno"
