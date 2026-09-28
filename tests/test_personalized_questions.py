import pytest
from app.schemas.ai import QuestionGenRequest, ChatHistoryItem, QuestionTranslationRequest
from app.services import llm, questions, personalized_questions as personal


def req(**kw):
    return QuestionGenRequest(cataract_res="normal", amsler_res="normal", **kw)


def approved(**changes):
    return {"verdict": next((key for key, value in changes.items() if value is not True), "ok")}


def test_topics_require_explicit_symptoms_and_test_results():
    for value in (False, "unknown"):
        assert "symptom_side" not in personal.topics_for(req(symptom_answers={"cat_foggy": value}))
    assert "symptom_side" in personal.topics_for(req(symptom_answers={"cat_foggy": True}))
    assert "photo_followup" not in personal.topics_for(req(cataract_code="normal"))
    assert "photo_followup" in personal.topics_for(req(cataract_code="uncertain"))
    assert "amsler_followup" in personal.topics_for(req(amsler_answers={"left": True}))
    assert "amsler_followup" not in personal.topics_for(req(amsler_answers={"left": "unable"}))
    assert not personal.topics_for(req(asked_question_ids=["symptom_side", "care_access"]))


@pytest.mark.anyio
async def test_real_generated_words_reach_client_only_after_review(monkeypatch):
    calls = []
    draft = {"topic": "symptom_side", "question": "흐리게 보이는 느낌이 한쪽 눈에만 있나요?"}
    async def fake(prompt, schema):
        calls.append(prompt)
        return draft if len(calls) == 1 else approved()
    monkeypatch.setattr(llm, "generate_json", fake)
    result = await llm.generate_personalized_question(req(symptom_answers={"cat_foggy": True}, cataract_code="uncertain"))
    assert result["question"] == draft["question"]
    assert result["source"] == "generated"
    assert result["question_texts"] == {"ko": draft["question"]}
    assert '"photo_screening": "uncertain"' in calls[0]
    assert '"foggy vision": true' in calls[1]


@pytest.mark.anyio
@pytest.mark.parametrize("failed", personal.REVIEW_FIELDS)
async def test_every_review_failure_triggers_rewrite_before_display(monkeypatch, failed):
    responses = iter([{"topic": "screen_fatigue", "question": "화면을 오래 보면 눈이 피곤해지나요?"},
                      approved(**{failed: False}),
                      {"topic": "eye_drops", "question": "최근 한 달 동안 안약을 넣은 적이 있나요?"}, approved()])
    async def fake(*_):
        return next(responses)
    monkeypatch.setattr(llm, "generate_json", fake)
    result = await llm.generate_personalized_question(req())
    assert result["question_id"] == "eye_drops" and result["source"] == "generated_retry"


@pytest.mark.anyio
@pytest.mark.parametrize("raw", [None, [], {}, {"topic": "symptom_side", "question": "한쪽 눈이 불편한가요?"},
    {"topic": "eye_injury", "question": "백내장이 있으므로 수술을 원하시나요?"},
    {"topic": "eye_injury", "question": "눈을 다친 적이 있나요? 어디인가요?"}])
async def test_invalid_or_ungrounded_drafts_use_catalog_after_two_failures(monkeypatch, raw):
    count = 0
    async def fake(*_):
        nonlocal count
        count += 1
        return raw
    monkeypatch.setattr(llm, "generate_json", fake)
    result = await llm.generate_personalized_question(req(symptom_answers={"cat_foggy": "unknown"}))
    assert result["source"] == "rule" and result["question"] == questions.QUESTIONS["eye_injury"]["ko"]
    assert count == 2


@pytest.mark.anyio
async def test_timeout_and_exhaustion_fail_closed(monkeypatch):
    async def fail(*_):
        raise TimeoutError()
    monkeypatch.setattr(llm, "generate_json", fail)
    assert (await llm.generate_personalized_question(req()))["source"] == "rule"
    assert (await llm.generate_personalized_question(req(asked_question_ids=["symptom_side", "symptom_trigger"])))["done"]
    assert (await llm.generate_personalized_question(req(red_flags=["rf_pain"])))["done"]


@pytest.mark.anyio
async def test_semantic_repeat_rejected_by_review_and_topic_id_excluded(monkeypatch):
    original = "한쪽 눈에서만 흐리게 보이나요?"
    responses = iter([{"topic": "symptom_pattern", "question": "흐리게 보이는 것이 한 눈에만 나타나나요?"},
                      approved(new_information=False), None])
    async def fake(*_):
        return next(responses)
    monkeypatch.setattr(llm, "generate_json", fake)
    request = req(symptom_answers={"cat_foggy": True}, asked_question_ids=["symptom_side"],
                  chat_history=[ChatHistoryItem(q=original, a="unknown")])
    assert "symptom_side" not in personal.topics_for(request)
    assert (await llm.generate_personalized_question(request))["source"] == "rule"


@pytest.mark.anyio
@pytest.mark.parametrize("equivalent", [True, False, "true"])
async def test_translation_requires_explicit_semantic_equivalence(monkeypatch, equivalent):
    responses = iter([{"question": "Is the blurred vision in only one eye?"}, {"equivalent": equivalent}])
    async def fake(*_):
        return next(responses)
    monkeypatch.setattr(llm, "generate_json", fake)
    result = await llm.translate_personalized_question(QuestionTranslationRequest(
        question="한쪽 눈에서만 흐리게 보이나요?", source_lang="ko", target_lang="en"))
    assert result["translated"] is (equivalent is True)
    if equivalent is not True:
        assert result["question"] == ""


def test_grid_side_already_known_is_not_asked_again():
    request = req(symptom_answers={"amd_center": True}, amsler_answers={"left": True, "right": False})
    assert "symptom_side" not in personal.topics_for(request)
    request.symptom_answers["cat_foggy"] = True
    assert "symptom_side" in personal.topics_for(request)  # foggy-vision side is still unknown
