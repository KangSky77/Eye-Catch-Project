"""Reviewed service explanations. These describe the tool, never diagnose a visitor."""
import re

SCORE_NOTE = {
    "ko": "이 숫자는 질병에 걸릴 확률이 아니라, AI가 사진에서 백내장 특징을 얼마나 강하게 감지했는지를 나타내는 점수입니다.",
    "en": "This number is not the probability of having the disease. It shows how strongly the AI detected cataract-like features in the photo.",
    "es": "Este número no es la probabilidad de tener la enfermedad. Indica con qué intensidad la IA detectó rasgos de catarata en la foto.",
    "fr": "Ce nombre n'est pas la probabilité d'avoir la maladie. Il indique à quel point l'IA a détecté des signes de cataracte sur la photo.",
    "ja": "この数値は病気である確率ではありません。AIが写真から白内障らしい特徴をどれだけ強く検出したかを示す点数です。",
    "zh": "该数字不是患病概率，而是表示AI在照片中检测到白内障特征的强度评分。",
}
SCORE_LIMIT = {
    "ko": "0점이어도 초기 백내장이나 다른 눈 질환이 없다는 뜻은 아닙니다. 눈 전체의 건강 상태를 평가하는 점수도 아닙니다.",
    "en": "A score of 0 does not rule out early cataracts or other eye conditions. It is not an assessment of overall eye health.",
    "es": "Un 0 no descarta cataratas iniciales ni otras afecciones oculares. No es una evaluación de la salud ocular general.",
    "fr": "Un score de 0 n’exclut ni une cataracte débutante ni une autre affection oculaire. Ce n’est pas une évaluation globale de la santé des yeux.",
    "ja": "0点でも初期の白内障や他の目の病気がないとは言えません。目全体の健康状態を評価する点数ではありません。",
    "zh": "0分也不能排除早期白内障或其他眼病。这不是对整体眼部健康的评分。",
}

def is_score_question(message: str) -> bool:
    text = re.sub(r"\s+", " ", message.casefold())
    if re.search(r"(?<!\d)(?:100|[1-9]?\d)\s*/\s*100(?!\d)", text):
        return True
    terms = ("점수", "score", "puntuación", "puntuacion", "puntaje", "スコア", "点数", "评分", "分数")
    return any(term in text for term in terms) and any(
        marker in text for marker in ("ai", "ia", "특징", "feature", "rasgos", "signes", "特徴", "特征")
    )

def score_explanation(message: str, lang: str) -> str | None:
    if not is_score_question(message):
        return None
    language = lang if lang in SCORE_NOTE else "en"
    return SCORE_NOTE[language] + " " + SCORE_LIMIT[language]
