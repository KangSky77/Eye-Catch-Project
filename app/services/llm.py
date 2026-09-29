import json
import logging
import asyncio
import httpx
from app.core.config import settings
from app.services import knowledge
from app.services import safety
from app.services import advice
from app.services import explain_check
from app.services import questions as followup_questions

from app.services.llm_prompts import (
    LANG_NAMES, _lang_name, _build_opinion_prompt, _build_chat_prompt,
    _build_next_question_prompt, _care_examples,
)
from app.services.question_validation import (
    MAX_QUESTION_CHARS, _is_compound_question, _is_yes_no_question,
    _valid_question_output,
)

logger = logging.getLogger(__name__)

# 하트비트 문자: 생성이 느려도(Ollama 콜드스타트/CPU) 스트림 연결이 끊기지 않도록
# 첫 토큰 전까지 주기적으로 보낸다. 폭이 0인 제로폭 공백이라 프론트가 무시/제거.
KEEPALIVE = chr(0x200B)     # zero-width space (U+200B)
KEEPALIVE_INTERVAL = 5.0    # 초
# 오류 마커: 스트림 중 발생한 오류를 '정상 소견'과 구분하기 위한 접두사.
# 프론트가 이 마커를 감지하면 에러로 처리(알림·DB저장 건너뜀). 일반 텍스트엔 안 나오는 시퀀스.
ERROR_MARKER = "⛔__ECERR__"   # ⛔__ECERR__

# 챗봇 답이 '문진 답과 어긋나는 문장'만으로 이루어져 전부 지워졌을 때 빈 화면 대신 보여 주는 고정 문구.
# 일부만 지워졌을 때는 붙이지 않는다 — 고혈압·당뇨 '아니오'인 사람의 평범한 질문에서 7번 중 7번 붙었고,
# 예전 문구의 '입력한 답변을 다시 확인해 주세요'는 틀린 쪽이 AI인데 사용자가 잘못 답한 것처럼 읽혔다(2026-09-29).
FACT_FILTER_NOTICE = {
    "ko": "문진에서 답하신 내용과 맞지 않는 답변만 나와서 보여 드리지 않았어요. 질문을 조금 바꿔 다시 물어봐 주세요.",
    "en": "The only answer I produced conflicted with your questionnaire answers, so I did not show it. Please try asking in a different way.",
    "es": "La única respuesta generada contradecía sus respuestas al cuestionario, así que no la mostré. Pruebe a preguntar de otra forma.",
    "fr": "La seule réponse produite contredisait vos réponses au questionnaire, je ne l’ai donc pas affichée. Essayez de reformuler votre question.",
    "ja": "問診の回答と合わない答えしか出なかったため、表示しませんでした。聞き方を少し変えてもう一度お試しください。",
    "zh": "生成的回答与您的问卷回答不符，因此没有显示。请换一种方式再问一次。",
}

# Emergency action must not depend on an LLM following its prompt. A real
# rf_acute session returned rest/sunglasses advice despite the urgent card.
# Sources: https://www.nhs.uk/symptoms/eye-pain/
# https://www.nhs.uk/symptoms/floaters-and-flashes-in-the-eyes/
_URGENT_ADVICE = {
    "ko": (
        "지금 바로 안과 진료를 받으세요.",
        "지금 바로 수술한 병원이나 응급 안과에 연락하고, 연락이 되지 않으면 응급실에서 진료를 받으세요.",
        "앱의 나머지 검사나 AI 답변을 기다리며 진료를 미루지 마세요.",
        "이 앱으로 증상의 원인을 진단하거나 질환을 배제할 수 없습니다.",
    ),
    "en": (
        "Seek urgent eye care now.",
        "Contact the hospital that performed your surgery or an emergency eye service now; if unavailable, go to an emergency department.",
        "Do not delay care while waiting for more app tests or AI replies.",
        "This app cannot diagnose the cause of your symptoms or rule out disease.",
    ),
    "es": (
        "Acuda a un servicio de atención oftalmológica urgente ahora.",
        "Contacte ahora al hospital que le operó o a un servicio de urgencias oftalmológicas; si no puede contactar, acuda a urgencias.",
        "No retrase la atención esperando más pruebas de la aplicación o respuestas de la IA.",
        "Esta aplicación no puede diagnosticar la causa de sus síntomas ni descartar enfermedades.",
    ),
    "fr": (
        "Consultez un service d'urgence ophtalmologique maintenant.",
        "Contactez maintenant l'hôpital qui vous a opéré ou les urgences ophtalmologiques ; s'ils sont injoignables, allez aux urgences.",
        "Ne retardez pas les soins en attendant d'autres tests de l'application ou des réponses de l'IA.",
        "Cette application ne peut ni diagnostiquer la cause de vos symptômes ni exclure une maladie.",
    ),
    "ja": (
        "今すぐ眼科を受診してください。",
        "今すぐ手術を受けた病院または救急の眼科に連絡し、連絡がつかなければ救急外来を受診してください。",
        "アプリの残りの検査やAIの回答を待って受診を遅らせないでください。",
        "このアプリでは症状の原因を診断したり、病気を否定したりすることはできません。",
    ),
    "zh": (
        "请立即就诊眼科。",
        "请立即联系为您手术的医院或眼科急诊；如无法联系，请前往急诊。",
        "不要因等待应用的其他检查或AI回复而延误就医。",
        "本应用不能诊断症状的原因，也不能排除疾病。",
    ),
}

def _ollama_timeout() -> httpx.Timeout:
    return httpx.Timeout(connect=10.0, read=settings.ollama_timeout_seconds, write=30.0, pool=10.0)


def _ollama_payload(prompt: str, stream: bool, fmt: dict | None = None) -> dict:
    # keep_alive=-1: 모델을 VRAM에 영구 상주시켜 콜드스타트(최초 로딩 ~45초) 제거
    # options를 비워 두면 모델 파일 기본값(Gemma: temperature 1.0)이 쓰인다 — 명시적으로 낮춘다.
    payload = {"model": settings.ollama_model, "prompt": prompt, "stream": stream, "keep_alive": -1,
               "options": {"temperature": settings.ollama_temperature}}
    if fmt is not None:
        payload["format"] = fmt   # JSON 스키마 — 모델이 스키마 밖의 값을 낼 수 없게 제약한다
    return payload


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

async def sanitized_stream(prompt: str, facts: list[str] | None = None, night_context: bool = False,
                           driving_context: bool = False, filtered_reasons: set[str] | None = None):
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
            why = safety.check_sentence(sentence.strip(), facts, night_context, driving_context)
            if why:
                dropped.append(why)
                if filtered_reasons is not None:
                    filtered_reasons.add(why)
                logger.warning("⚠️  안전 필터가 LLM 문장을 제거: %s | %s", why, sentence.strip()[:120])
            else:
                # 공백만 내보낸 것은 '내용을 냈다'고 볼 수 없다 — 화면에는 빈 칸으로 보인다
                emitted = emitted or bool(sentence.strip())
                yield sentence
    # 마지막 문장(종결부호 없이 끝난 경우)
    tail = buf.strip()
    if tail:
        why = safety.check_sentence(tail, facts, night_context, driving_context)
        if why:
            dropped.append(why)
            if filtered_reasons is not None:
                filtered_reasons.add(why)
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


async def generate_json(prompt: str, schema: dict):
    """JSON 스키마로 출력을 제약한 한 번짜리 호출. 파싱 실패는 None(호출부가 재시도·대체)."""
    async with httpx.AsyncClient(timeout=_ollama_timeout()) as client:
        response = await client.post(settings.ollama_url, json=_ollama_payload(prompt, stream=False, fmt=schema))
        response.raise_for_status()
        text = response.json().get("response", "")
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


async def generate_personalized_question(request):
    from app.services import personalized_questions
    return await personalized_questions.generate(request, generate_json, _valid_question_output)


async def translate_personalized_question(request):
    from app.services import personalized_questions
    return await personalized_questions.translate(request, generate_json, _valid_question_output)


async def select_next_question(request):
    """Offline selection-only baseline; the live API uses generate_personalized_question."""
    eligible = followup_questions.eligible_ids(request)
    if not eligible:
        return followup_questions.response()
    picked, source = eligible[0], "rule"
    if len(eligible) > 1:
        schema = {"type": "object", "properties": {"question_id": {"type": "string", "enum": eligible}},
                  "required": ["question_id"], "additionalProperties": False}
        # No patient prose is placed in the instruction context.
        facts = {key: value for key, value in request.symptom_answers.items()
                 if key in followup_questions.SYMPTOM_CODES}
        prompt = ("Select one useful follow-up question ID from the allowed list. "
                  "Return JSON only. Explicit true means a reported symptom; unknown is not true.\n"
                  + json.dumps({"answers": facts, "choices": {
                      key: followup_questions.QUESTIONS[key]["en"] for key in eligible}}, ensure_ascii=False))
        try:
            raw = await asyncio.wait_for(generate_json(prompt, schema), timeout=12)
            candidate = raw.get("question_id") if isinstance(raw, dict) else None
            if isinstance(candidate, str) and candidate in eligible:
                picked, source = candidate, "ai"
        except Exception:
            logger.info("Question selection unavailable; using an eligible catalog question")
    return followup_questions.response(picked, request.lang, source)


async def pick_advice(facts: "advice.Facts", opts: dict) -> tuple[dict, str]:
    """AI가 선택지 중에서 고른다. 형식이 틀리면 한 번 더, 그래도 틀리면 규칙 기반 선택.
    Ollama 자체에 연결할 수 없으면 예외를 그대로 올린다 — AI가 없는데 'AI 소견'이라고 내보내지 않는다."""
    prompt, schema = advice.selection_prompt(facts, opts), advice.schema_for(facts, opts)
    for attempt in range(2):
        choice = advice.validate_choice(await generate_json(prompt, schema), facts, opts)
        if choice:
            prioritized = advice.apply_choice_priorities(choice, facts, opts)
            source = "ai" if attempt == 0 else "ai_retry"
            if prioritized != choice:
                source += "_adjusted"
            return prioritized, source
    fallback = advice.apply_choice_priorities(advice.fallback_choice(facts, opts), facts, opts)
    return fallback, "fallback"


async def _choice_opinion_stream(facts: "advice.Facts", lang: str):
    opts = advice.options_for(facts)
    task = asyncio.create_task(pick_advice(facts, opts))
    try:
        while not task.done():
            # 모델이 고르는 동안에도 연결을 유지한다(ngrok·모바일) — 자유 작문 경로의 하트비트와 같은 역할
            done, _ = await asyncio.wait({task}, timeout=KEEPALIVE_INTERVAL)
            if not done:
                yield KEEPALIVE
        choice, source = task.result()
    except Exception:
        logger.error("⚠️  AI 조언 선택 오류", exc_info=True)
        yield ERROR_MARKER + "AI_SERVER_ERROR"
        return
    finally:
        if not task.done():
            task.cancel()
    logger.info("AI 조언 선택 %s (%s)", choice, source)
    yield advice.compose(choice, facts, lang)


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
                                   symptom_codes: list[str] | None = None, eye_asymmetric: bool = False,
                                   red_flags: list[str] | None = None, triage_level: str = "",
                                   flag_codes: list[str] | None = None):
    if red_flags or triage_level == "urgent":
        copy = _URGENT_ADVICE.get(lang, _URGENT_ADVICE["en"])
        postoperative = cataract_code == "postop" or any("Eye surgery:" in item for item in symptoms)
        # Use the same summary protocol as ordinary advice; no model call or
        # lifestyle suggestion may weaken the app's emergency action.
        yield "<<<SUMMARY>>>\n" + "\n".join((copy[1] if postoperative else copy[0], copy[2], copy[3]))
        return
    if settings.opinion_mode == "choice":
        # AI는 검수된 조언 목록에서 고르기만 한다(app/services/advice.py). 문진 사실을 문장으로
        # 다시 쓰게 하면 작은 모델·큰 모델 모두 20번 중 3번꼴로 사실을 잘못 옮겼다(2026-09-27 측정).
        facts = advice.facts_from(symptoms, flag_codes, symptom_codes, cataract_code, amsler_abnormal, triage_level)
        async for chunk in _choice_opinion_stream(facts, lang):
            yield chunk
        return
    # RAG: 환자 결과에 맞는 안과 참고지식을 검색해 프롬프트에 주입
    reference = knowledge.format_reference(
        knowledge.retrieve_for_opinion(cataract_code, amsler_abnormal, symptom_codes)
    )
    prompt = _build_opinion_prompt(cataract, amsler, symptoms, lang, reference, eye_asymmetric,
                                   urgent=bool(red_flags))
    if cataract_code == 'postop' or any('Eye surgery:' in item for item in symptoms):
        # 권장 조치는 앱이 이미 정했다(computeTriage). LLM이 스스로 판단하게 두면
        # 카드는 '예정된 진료를 따르세요'인데 소견 3줄은 전부 '지금 수술팀에 연락하세요'가
        # 되어 같은 화면에서 두 안내가 충돌한다 — 실사용 점검에서 그대로 재현됐다.
        # An API caller can provide a stale or contradictory triage_level. A reported
        # emergency sign must always win, regardless of the browser's card state.
        level = "urgent" if red_flags else (triage_level or "monitor")
        action = {
            "urgent": (
                "Begin by telling them to contact the surgical team or emergency eye service NOW. "
                "If unreachable, advise emergency care. Never suggest waiting, and do NOT mention "
                "any planned or scheduled follow-up at all."
            ),
            "now": (
                "Tell them to contact the surgical team about the reported symptoms and to ask "
                "whether they can wait until the scheduled review."
            ),
            "confirm": (
                "They reported NO warning symptoms, but they are unsure about, or cannot follow, their "
                "discharge and aftercare instructions. Tell them to contact the surgical team to re-confirm "
                "how to care for the eye and when the next review is. Do NOT say they reported symptoms, "
                "and do NOT tell them to seek emergency care."
            ),
        }.get(level, (
            "Tell them to follow their discharge instructions and the review already scheduled. "
            "Do NOT tell them to contact the team right now; instead say to contact the team if "
            "symptoms are new, get worse, or do not improve."
        ))
        prompt = f"""Write ONLY in {_lang_name(lang)}.
This person has ALREADY COMPLETED eye surgery, not scheduled future surgery.
This is a postoperative symptom questionnaire, NOT a photo diagnosis.
Patient-reported facts: {json.dumps(symptoms, ensure_ascii=False)}
Emergency warning signs reported: {bool(red_flags)}.
Do not invent diagnoses, reassurance, medications, exams, smoking, diabetes or hypertension.
Never say the patient has a complication: only a clinician can determine the cause.
Do not describe absence of pain as evidence of successful or normal healing.
REQUIRED ACTION (already decided by the app — follow it exactly, do not soften or escalate it):
{action}
Do not declare glare or any symptom normal.
Do not recommend changing prescribed treatment or invent a recovery duration.
Explain in 6 short sentences: the appropriate next action, what reported symptoms to tell
the team, limitations of this questionnaire, and the importance of the team's aftercare.
Do not repeat the same advice. No headings or numbered lists.
Call the surgical team "the hospital or clinic that performed the surgery" in the reader's language
(Korean: "수술한 병원"); never write the bare word "team". Keep one polite tone throughout
(Korean: end every sentence with -세요 or -습니다, not -하십시오).
Then put <<<SUMMARY>>> on a separate line.
Copy exactly THREE important sentences VERBATIM from your detailed explanation,
each on its own line. The first must preserve urgency when emergency signs are true.
Do not add any fact in the summary. Output nothing else."""
    try:
        # 안전 필터 경유 — 해석·확률·배제·질환 교차 문장은 화면에 닿기 전에 제거된다
        async for chunk in sanitized_stream(
            prompt, symptoms, driving_context=any(safety.mentions_driving(item) for item in symptoms)
        ): yield chunk
    except Exception:
        logger.error("⚠️  소견서 스트리밍 오류", exc_info=True)
        yield ERROR_MARKER + "AI_SERVER_ERROR"

async def chat_with_gemma_stream(user_msg: str, context: str, lang: str = "ko", explain_results: bool = False,
                                 facts: list[str] | None = None, explain_required: list[str] | None = None,
                                 explain_fallback: list[str] | None = None):
    if explain_results:
        # Word presence cannot establish meaning: a negated finding or urgency
        # can contain every required term. Use the same reviewed wording as the
        # report for all results, including normal, unmeasured and postoperative.
        text = await explain_check.fallback_text(explain_fallback or [], lang)
        yield text if text else ERROR_MARKER + "EXPLANATION_UNAVAILABLE"
        return
    # RAG: 질문 키워드로 관련 참고지식을 검색해 주입
    reference = "" if explain_results else knowledge.format_reference(knowledge.retrieve_for_chat(user_msg))
    try:
        # 자유 질문은 소견서보다 더 자유롭게 흘러가므로 필터가 더 중요하다
        # facts: 고혈압 '아니오'인 사람에게 "혈압을 관리하세요"가 3번 중 2번 나갔다(2026-09-29 실측) —
        # 지시문의 일반 관리 수칙 예시를 모델이 그대로 따라 했다. AI 소견과 같은 사실 필터로 막는다.
        filtered_reasons: set[str] = set()
        async for chunk in sanitized_stream(
            _build_chat_prompt(user_msg, context, lang, reference, explain_results=explain_results, facts=facts),
            facts=facts or [],
            night_context=safety.mentions_night(user_msg),
            driving_context=safety.mentions_driving(user_msg),
            filtered_reasons=filtered_reasons,
        ):
            # If every sentence was removed for contradicting known answers, give
            # the user a clear explanation instead of making the chat look broken.
            if chunk == ERROR_MARKER + "AI_FILTER_EMPTY" and "contradicts_facts" in filtered_reasons:
                yield FACT_FILTER_NOTICE.get(lang, FACT_FILTER_NOTICE["en"])
                return
            yield chunk
            if chunk.startswith(ERROR_MARKER):
                return
    except Exception:
        logger.error("⚠️  챗봇 응답 스트리밍 오류", exc_info=True)
        yield ERROR_MARKER + "AI_SERVER_ERROR"

async def generate_next_question(lang: str, cataract_res: str, amsler_res: str, chat_history: list) -> tuple[str, str]:
    """Legacy offline comparison helper. HTTP requests use generate_personalized_question only."""
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
        prompt = _build_next_question_prompt(lang, cataract_res, amsler_res, history_text)
        q = (await generate_ollama(prompt) or "").strip()
        # '한쪽 눈인가요, 양쪽인가요?' 같은 선택형은 이미 자유 입력칸으로 받으므로 묶음으로 보지 않는다.
        if _is_yes_no_question(q) and _is_compound_question(q):
            # 한 번만 다시 쓰게 한다 — 그래도 묶여 있으면 검수된 기본 질문(프론트 폴백)이 낫다.
            logger.info("동적 문진 질문이 두 상황을 묶음 — 재생성: %r", q)
            retry_note = ("\n\n[다시 쓰기] 방금 쓴 질문은 두 상황을 묶었습니다. 한 가지만 물으세요: "
                          if lang == "ko" else
                          "\n\n[REWRITE] Your question combined two situations. Ask about only one: ")
            q = (await generate_ollama(prompt + retry_note + q) or "").strip()
            if _is_yes_no_question(q) and _is_compound_question(q):
                return "", "yesno"
        if not q:
            return "", "yesno"
        # 맞춤 질문이 2회차부터는 chat_history로 되돌아오는데, ChatHistoryItem.q의 상한이
        # 500자다(app/schemas/ai.py). 넘기면 다음 요청이 422로 거부되고 프론트는 그것을
        # 조용히 기본 질문으로 폴백해버린다. 애초에 이 길이면 '한 문장 질문'이 아니라
        # 모델이 장황하게 늘어놓은 것이므로, 자르지 말고 버려서 기본 질문을 쓰게 한다.
        if len(q) > MAX_QUESTION_CHARS:
            logger.warning("⚠️  동적 문진 질문이 너무 김(%d자) — 기본 질문으로 폴백", len(q))
            return "", "yesno"
        if not _valid_question_output(q, lang, chat_history):
            logger.info("동적 문진 형식·언어·중복 검사 실패 — 기본 질문으로 폴백")
            return "", "yesno"
        # 프롬프트로 예/아니오를 요구하지만 LLM이 가끔 서술형을 낸다.
        # 예전에는 그런 질문을 버렸는데, 좋은 질문인 경우가 많아 버리기 아깝다.
        # 대신 종류를 알려주고 프론트가 자유 입력칸을 띄우게 한다.
        return q, ("yesno" if _is_yes_no_question(q) else "text")
    except Exception:
        logger.warning("⚠️  동적 문진 질문 생성 실패 — 프론트 기본 질문으로 폴백", exc_info=True)
        return "", "yesno"
