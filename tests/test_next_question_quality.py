"""Malformed model output must not be displayed as a screening question."""
import pytest

from app.schemas.ai import ChatHistoryItem
from app.services import llm


@pytest.mark.anyio
@pytest.mark.parametrize("lang, reply", [
    ("ko", "백내장입니다. 지금 수술을 받으세요."),
    ("ko", "백내장일 수 있습니다. 눈이 아프신가요?"),
    ("ko", "눈을 다친 적이 있나요? 스테로이드 안약을 쓰시나요?"),
    ("ko", "증상이 언제부터 시작됐는지"),
    ("ko", "Have you had an eye injury?"),
    ("en", "눈을 다친 적이 있나요?"),
    ("ja", "您是否曾经眼睛受伤？"),
    ("zh", "目をけがしたことがありますか？"),
    ("fr", "Your eyes are healthy."),
])
async def test_rejects_non_question_multiple_sentences_and_wrong_script(monkeypatch, lang, reply):
    async def generate(_):
        return reply
    monkeypatch.setattr(llm, "generate_ollama", generate)
    assert await llm.generate_next_question(lang, "", "", []) == ("", "yesno")


@pytest.mark.anyio
@pytest.mark.parametrize("lang, reply, kind", [
    ("ko", "눈을 다친 적이 있나요?", "yesno"),
    ("en", "Have you had an eye injury?", "yesno"),
    ("es", "¿Ha sufrido alguna lesión en un ojo?", "yesno"),
    ("fr", "Avez-vous déjà eu une blessure à un œil ?", "yesno"),
    ("ja", "目をけがしたことがありますか？", "yesno"),
    ("zh", "您是否曾经眼睛受伤？", "yesno"),
    ("ko", "불편한 눈은 한쪽 눈인가요, 양쪽 눈인가요?", "text"),
])
async def test_preserves_single_questions_and_free_text_controls(monkeypatch, lang, reply, kind):
    async def generate(_):
        return reply
    monkeypatch.setattr(llm, "generate_ollama", generate)
    assert await llm.generate_next_question(lang, "", "", []) == (reply, kind)


@pytest.mark.anyio
async def test_rejects_question_already_answered(monkeypatch):
    question = "눈을 다친 적이 있나요?"
    async def generate(_):
        return question
    monkeypatch.setattr(llm, "generate_ollama", generate)
    history = [ChatHistoryItem(q=question, a="아니오")]
    assert await llm.generate_next_question("ko", "", "", history) == ("", "yesno")
