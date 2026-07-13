"""요청 스키마 계약 — 특히 'fr/es 경계+두눈 문자열 110자' 422 회귀 방지."""
import pytest
from pydantic import ValidationError

from app.schemas.ai import GemmaRequest, ChatRequest, QuestionGenRequest, SaveDiagnosisRequest


def test_긴_판독문자열_110자_허용():
    # 프랑스어 경계 판정 + 얼굴 모드(두 눈 수치) 문자열이 110자까지 나옴 —
    # max_length를 100으로 되돌리면 fr/es 소견서 요청이 422로 깨진다(실측 재현했던 버그)
    long_res = "R" * 110
    req = GemmaRequest(cataract_res=long_res, amsler_res="normal")
    assert req.cataract_res == long_res
    # QuestionGenRequest도 같은 문자열을 받으므로 함께 보장
    QuestionGenRequest(cataract_res=long_res, amsler_res="normal")


def test_판독문자열_상한_초과는_거부():
    with pytest.raises(ValidationError):
        GemmaRequest(cataract_res="R" * 201, amsler_res="normal")


def test_구버전_프론트_하위호환_기본값():
    # cataract_code 등 RAG 신호를 안 보내는 구버전 프론트도 동작해야 함
    req = GemmaRequest(cataract_res="정상", amsler_res="정상")
    assert req.cataract_code == ""
    assert req.amsler_abnormal is False
    assert req.symptom_codes == []
    assert req.eye_asymmetric is False
    assert req.lang == "ko"


def test_챗봇_빈_메시지_거부():
    with pytest.raises(ValidationError):
        ChatRequest(user_msg="")


def test_문진내역_형식():
    req = QuestionGenRequest(
        cataract_res="정상", amsler_res="정상",
        chat_history=[{"q": "눈부심이 있나요?", "a": "네"}],
    )
    assert req.chat_history[0].q == "눈부심이 있나요?"
    assert req.chat_history[0].a == "네"


def test_저장요청_증상목록_상한():
    with pytest.raises(ValidationError):
        SaveDiagnosisRequest(
            cataract_result="정상", amsler_result="정상",
            chat_symptoms=["s"] * 31,       # max_length=30
        )
