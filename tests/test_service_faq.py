import re
from pathlib import Path

import pytest

from app.services import llm
from app.services.service_faq import SCORE_NOTE, SCORE_LIMIT, is_score_question

QUESTIONS = [
    ("ko", "AI 특징 점수 0/100이 무슨 뜻인가요?"),
    ("en", "What does the AI score mean?"),
    ("es", "¿Qué significa la puntuación de IA?"),
    ("fr", "Que signifie le score de signes IA ?"),
    ("ja", "AI特徴スコアはどういう意味ですか？"),
    ("zh", "AI特征评分是什么意思？"),
]

@pytest.mark.anyio
@pytest.mark.parametrize("lang,message", QUESTIONS)
async def test_score_definition_never_calls_model_and_matches_photo_screen(monkeypatch, lang, message):
    async def forbidden(*args, **kwargs):
        raise AssertionError("A reviewed tool definition must not call the model")
        yield ""
    monkeypatch.setattr(llm, "sanitized_stream", forbidden)
    actual = "".join([chunk async for chunk in llm.chat_with_gemma_stream(message, "", lang)])
    assert actual == SCORE_NOTE[lang] + " " + SCORE_LIMIT[lang]
    # The screen and API must preserve the exact same definition across all languages.
    source = (Path(__file__).parents[1] / "static/data.js").read_text(encoding="utf-8")
    assert SCORE_NOTE[lang] in source
    copy = (Path(__file__).parents[1] / "static/app-ux-copy.js").read_text(encoding="utf-8")
    assert SCORE_LIMIT[lang] in copy

@pytest.mark.parametrize("message", ["안약 사용에 대해 궁금해요", "How do I protect my eyes?", "혈당이 높아요", "Tell me about cataracts"])
def test_other_questions_still_use_regular_chat(message):
    assert not is_score_question(message)

@pytest.mark.anyio
async def test_score_api_does_not_wait_for_model_slot(client, monkeypatch):
    from app.api import routes
    class ForbiddenSlots:
        async def acquire(self):
            raise AssertionError("Fixed explanations do not consume model slots")
    monkeypatch.setattr(routes, "_llm_slots", ForbiddenSlots())
    response = client.post("/api/chat-with-gemma", json={"user_msg": "AI 점수 0/100", "context": "", "lang": "ko"})
    assert response.status_code == 200
    assert SCORE_NOTE["ko"] in response.text

@pytest.mark.anyio
async def test_skipping_optional_question_cancels_work_and_releases_model_slot(monkeypatch):
    import asyncio
    from app.api import routes
    from app.schemas.ai import QuestionGenRequest
    finished = asyncio.Event()
    async def generation(req):
        try:
            await asyncio.sleep(60)
        finally:
            finished.set()
    class DisconnectedRequest:
        async def is_disconnected(self):
            await asyncio.sleep(0.01)
            return True
    slots = asyncio.Semaphore(1)
    monkeypatch.setattr(routes, "_llm_slots", slots)
    monkeypatch.setattr(routes, "generate_personalized_question", generation)
    with pytest.raises(routes.HTTPException) as error:
        await routes._question_until_disconnect(QuestionGenRequest(lang="ko", cataract_res="synthetic", amsler_res="not performed"), DisconnectedRequest())
    assert error.value.status_code == 499
    assert finished.is_set()
    assert not slots.locked()

@pytest.mark.anyio
async def test_completed_question_stops_disconnect_monitor_without_hanging(monkeypatch):
    import asyncio
    from app.api import routes
    entered = asyncio.Event()
    async def generation(req):
        await entered.wait()
        return {"done": True}
    class ConnectedRequest:
        async def is_disconnected(self):
            entered.set()
            try:
                await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                pass  # Model Request.is_disconnected's cancellation scope.
            return False
    monkeypatch.setattr(routes, "_llm_slots", asyncio.Semaphore(1))
    monkeypatch.setattr(routes, "generate_personalized_question", generation)
    result = await asyncio.wait_for(routes._question_until_disconnect(None, ConnectedRequest()), timeout=1)
    assert result == {"done": True}
