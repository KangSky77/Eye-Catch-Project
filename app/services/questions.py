"""Curated follow-up questions. These collect context and never determine triage.

Eligibility uses explicit structured answers, not model interpretations of prose.
The same stable ID and translations are retained across language switches.
"""
LANGUAGES = ("ko", "en", "es", "fr", "ja", "zh")


def _copy(*values):
    return dict(zip(LANGUAGES, values, strict=True))


QUESTIONS = {
    "eye_injury": _copy(
        "눈을 다친 적이 있나요?",
        "Have you ever injured an eye?",
        "¿Alguna vez se ha lesionado un ojo?",
        "Vous êtes-vous déjà blessé un œil ?",
        "目をけがしたことがありますか？",
        "您的眼睛以前受过伤吗？",
    ),
    "eye_drops": _copy(
        "최근 한 달 동안 안약을 사용한 적이 있나요?",
        "Have you used eye drops in the past month?",
        "¿Ha usado gotas para los ojos en el último mes?",
        "Avez-vous utilisé des gouttes pour les yeux au cours du dernier mois ?",
        "この1か月に目薬を使ったことがありますか？",
        "过去一个月内，您使用过眼药水吗？",
    ),
    "screen_fatigue": _copy(
        "화면을 오래 보면 눈이 쉽게 피곤해지나요?",
        "Do your eyes tire easily when you look at a screen for a long time?",
        "¿Se le cansan fácilmente los ojos al mirar una pantalla durante mucho tiempo?",
        "Vos yeux se fatiguent-ils facilement quand vous regardez longtemps un écran ?",
        "画面を長く見ていると、目が疲れやすくなりますか？",
        "长时间看屏幕时，您的眼睛容易疲劳吗？",
    ),
    "outdoor_time": _copy(
        "햇볕이 강한 낮에 야외에서 오래 지내는 편인가요?",
        "Do you often spend a long time outdoors in strong sunlight?",
        "¿Suele pasar mucho tiempo al aire libre cuando el sol es intenso?",
        "Passez-vous souvent beaucoup de temps dehors quand le soleil est fort ?",
        "日差しの強い日中に、屋外で長く過ごすことが多いですか？",
        "阳光强烈的白天，您经常长时间待在户外吗？",
    ),
    "symptom_duration": _copy(
        "말씀하신 눈의 불편함이 한 달 넘게 이어졌나요?",
        "Has the eye discomfort you reported lasted more than a month?",
        "¿Las molestias oculares que ha mencionado duran desde hace más de un mes?",
        "La gêne oculaire que vous avez signalée dure-t-elle depuis plus d’un mois ?",
        "お答えいただいた目の不快感は、1か月以上続いていますか？",
        "您提到的眼部不适已经持续一个多月了吗？",
    ),
    "daily_impact": _copy(
        "눈의 불편함 때문에 평소 하던 활동을 줄인 적이 있나요?",
        "Have you reduced your usual activities because of the eye discomfort?",
        "¿Ha reducido sus actividades habituales por las molestias en los ojos?",
        "Avez-vous réduit vos activités habituelles à cause de votre gêne oculaire ?",
        "目の不快感のために、普段の活動を減らしたことがありますか？",
        "您是否因为眼部不适而减少了平常的活动？",
    ),
}

# History/risk questions (e.g. high pressure or an overdue exam) are not symptoms.
SYMPTOM_CODES = {"cat_glare", "cat_foggy", "amd_center", "gla_field"}
MAX_FOLLOWUPS = 2
# Topics identify missing information, not prewritten questions.
GENERATED_TOPICS = {
    "symptom_side", "symptom_pattern", "symptom_trigger",
    "sugar_off_target", "bp_off_target", "quit_interest",
    # 2026-09-28에 뺀 주제 — 예전 클라이언트가 보낸 '이미 물은 주제' 기록은 계속 인식한다.
    "care_access", "photo_followup", "amsler_followup",
}


def asked_ids(request):
    asked = set(request.asked_question_ids) & (QUESTIONS.keys() | GENERATED_TOPICS)
    # Also recognise older clients or history restored without IDs in any language.
    history = {item.q.strip() for item in request.chat_history}
    asked.update(key for key, texts in QUESTIONS.items() if history.intersection(texts.values()))
    return asked


def eligible_ids(request):
    if request.postoperative or request.red_flags:
        return []
    asked = asked_ids(request)
    if len(asked) >= MAX_FOLLOWUPS:
        return []
    choices = ["eye_injury", "eye_drops", "screen_fatigue", "outdoor_time"]
    # Only an explicit yes permits a question that presumes existing discomfort.
    if any(request.symptom_answers.get(code) is True for code in SYMPTOM_CODES):
        choices = ["symptom_duration", "daily_impact"] + choices
    return [key for key in choices if key not in asked]


def response(question_id=None, lang="ko", source="none"):
    if question_id is None:
        return {"question": "", "answer_type": "yesno", "question_id": None,
                "question_texts": {}, "done": True, "source": source}
    texts = QUESTIONS[question_id]
    return {"question": texts.get(lang, texts["en"]), "answer_type": "yesno",
            "question_id": question_id, "question_texts": texts,
            "done": False, "source": source}
