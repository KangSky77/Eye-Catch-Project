"""Malformed model output must not be displayed as a screening question.

맞춤 질문 경로(personalized_questions.generate)가 모델 출력을 화면에 올리기 전에 쓰는 검사를
직접 확인한다. 예전 자유 생성 경로(llm.generate_next_question)는 2026-09-29에 지웠지만
형식·언어·중복 검사 규칙은 같은 함수(question_validation)로 그대로 쓰인다.
"""
import pytest

from app.schemas.ai import ChatHistoryItem
from app.services.question_validation import _is_yes_no_question, _valid_question_output


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
def test_rejects_non_question_multiple_sentences_and_wrong_script(lang, reply):
    assert not _valid_question_output(reply, lang, [])


@pytest.mark.parametrize("lang, reply, kind", [
    ("ko", "눈을 다친 적이 있나요?", "yesno"),
    ("en", "Have you had an eye injury?", "yesno"),
    ("es", "¿Ha sufrido alguna lesión en un ojo?", "yesno"),
    ("fr", "Avez-vous déjà eu une blessure à un œil ?", "yesno"),
    ("ja", "目をけがしたことがありますか？", "yesno"),
    ("zh", "您是否曾经眼睛受伤？", "yesno"),
    ("ko", "불편한 눈은 한쪽 눈인가요, 양쪽 눈인가요?", "text"),
])
def test_preserves_single_questions_and_free_text_controls(lang, reply, kind):
    assert _valid_question_output(reply, lang, [])
    assert ("yesno" if _is_yes_no_question(reply) else "text") == kind


def test_rejects_question_already_answered():
    question = "눈을 다친 적이 있나요?"
    history = [ChatHistoryItem(q=question, a="아니오")]
    assert not _valid_question_output(question, "ko", history)
