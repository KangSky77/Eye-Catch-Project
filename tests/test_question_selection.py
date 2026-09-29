"""Eligibility, model boundary and language-independent follow-up identity."""
import itertools

import pytest

from app.schemas.ai import QuestionGenRequest, ChatHistoryItem
from app.services import questions


def request(**values):
    return QuestionGenRequest(cataract_res="normal", amsler_res="normal", **values)


def test_all_answer_combinations_only_explicit_symptoms_enable_symptom_questions():
    codes = sorted(questions.SYMPTOM_CODES)
    for answers in itertools.product((True, False, "unknown"), repeat=len(codes)):
        req = request(symptom_answers=dict(zip(codes, answers)))
        eligible = questions.eligible_ids(req)
        assert ("symptom_duration" in eligible) == any(a is True for a in answers)
        assert ("daily_impact" in eligible) == any(a is True for a in answers)
    assert "daily_impact" not in questions.eligible_ids(request(symptom_answers={"gla_iop": True, "chk_recent": True}))


def test_every_question_has_six_single_question_translations_and_is_excluded_by_history():
    for key, texts in questions.QUESTIONS.items():
        assert set(texts) == set(questions.LANGUAGES)
        for lang, text in texts.items():
            assert text and len(text) <= 500
            assert text.count("?") + text.count("？") == 1
            req = request(lang=lang, chat_history=[ChatHistoryItem(q=text, a="unknown")])
            assert key not in questions.eligible_ids(req)


@pytest.mark.parametrize("answer", [True, False, "unknown"])
def test_asked_id_remains_excluded_after_answer_and_language_change(answer):
    for lang in questions.LANGUAGES:
        req = request(lang=lang, asked_question_ids=["eye_injury"],
                      chat_history=[ChatHistoryItem(q=questions.QUESTIONS["eye_injury"]["ko"], a=str(answer))])
        assert "eye_injury" not in questions.eligible_ids(req)
        req.asked_question_ids.append("eye_drops")
        assert questions.eligible_ids(req) == []


def test_schema_preserves_unknown_and_rejects_truthy_strings():
    from pydantic import ValidationError
    assert request(symptom_answers={"cat_foggy": "unknown"}).symptom_answers["cat_foggy"] == "unknown"
    with pytest.raises(ValidationError):
        request(symptom_answers={"cat_foggy": "true"})
