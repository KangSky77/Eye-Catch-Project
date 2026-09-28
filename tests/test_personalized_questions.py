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
    # 방금 앱에서 찍은 사진·격자를 '의사와 이야기했나'로 묻던 주제는 뺐다(2026-09-28 실측 7/50 어색).
    for removed in ("photo_followup", "amsler_followup", "care_access"):
        assert removed not in personal.topics_for(req(cataract_code="uncertain", amsler_answers={"left": True}))
    # 안경 주제는 AI가 '예'의 뜻을 뒤집어 물어서 뺐다(15번 중 8번)
    assert "glasses_help" not in personal.topics_for(req(cataract_code="uncertain", risk_answers={"age": "70s"}))
    assert not personal.topics_for(req(asked_question_ids=["symptom_side", "care_access"]))


def test_위험요인이_있으면_그_사람만의_주제가_먼저_온다():
    topics = personal.topics_for(req(risk_answers={"diabetes": True, "hypertension": False, "smoking": True}))
    assert topics[:2] == ["sugar_off_target", "quit_interest"]
    assert "bp_off_target" not in topics
    # '모르겠어요'나 '아니오'는 위험요인이 아니다
    assert "sugar_off_target" not in personal.topics_for(req(risk_answers={"diabetes": "unknown"}))


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
    assert "symptom_trigger" not in personal.topics_for(request)
    request.symptom_answers["cat_foggy"] = True
    assert "symptom_side" in personal.topics_for(request)  # foggy-vision side is still unknown

@pytest.mark.anyio
async def test_reviewer_receives_server_topic_definition_and_yes_polarity(monkeypatch):
    prompts = []
    async def fake(prompt, schema):
        prompts.append(prompt)
        if len(prompts) == 1:
            return {'topic': 'sugar_off_target', 'question': '혈당이 목표보다 자주 높아지나요?'}
        return {'verdict': 'ok'}
    monkeypatch.setattr(llm, 'generate_json', fake)
    result = await llm.generate_personalized_question(req(risk_answers={'diabetes': True}))
    assert result['source'] == 'generated'
    assert 'topic_definition' in prompts[1] and 'Yes = often above target' in prompts[1]
    assert 'Reject reversed polarity' in prompts[1]


def test_yesno_question_may_contain_when_without_being_open_ended():
    request = req(lang="en")
    assert personal.basic_error({"topic": "screen_fatigue", "question": "Do your eyes tire when using a screen?"},
                                request, personal.topics_for(request), llm._valid_question_output) is None
    assert personal.basic_error({"topic": "screen_fatigue", "question": "When do your eyes tire?"},
                                request, personal.topics_for(request), llm._valid_question_output) == "not_yesno_question"


def test_daily_impact_cannot_repeat_reading_symptom_instead_of_changed_activity():
    request = req(symptom_answers={"amd_center": True})
    topics = personal.topics_for(request)
    repeated = {"topic": "daily_impact", "question": "중심 시야가 휘는 증상이 글자를 읽을 때 더 불편하게 느껴지나요?"}
    assert personal.basic_error(repeated, request, topics, llm._valid_question_output).startswith("daily_impact_must_")
    changed = {"topic": "daily_impact", "question": "가운데가 흐리게 보여 독서 시간을 줄인 적이 있나요?"}
    assert personal.basic_error(changed, request, topics, llm._valid_question_output) is None

@pytest.mark.anyio
async def test_result_explanation_uses_report_only_without_general_advice_reference(monkeypatch):
    from app.services import llm
    captured = []
    def forbidden(*_):
        pytest.fail('Result explanation must not retrieve general health advice')
    async def fake(prompt, **kwargs):
        captured.append(prompt)
        yield 'Existing results explained.'
    monkeypatch.setattr(llm.knowledge, 'retrieve_for_chat', forbidden)
    monkeypatch.setattr(llm, 'sanitized_stream', fake)
    result = ''.join([c async for c in llm.chat_with_gemma_stream('Explain my results', 'REPORT FACTS', 'en', explain_results=True)])
    assert result == 'Existing results explained.'
    assert 'REPORT FACTS' in captured[0]
    assert 'Do not add lifestyle advice' in captured[0]
    assert 'Unknown or missing answers do not mean No' in captured[0]
