from pydantic import BaseModel, Field

class ChatHistoryItem(BaseModel):
    q: str = Field(..., min_length=1, max_length=500)
    a: str = Field(default="", max_length=500)

class GemmaRequest(BaseModel):
    lang: str = Field(default="ko", max_length=10)
    cataract_res: str = Field(..., max_length=100)
    amsler_res: str = Field(..., max_length=100)
    # 실제 문진 흐름은 고정 질문 몇 개 + 동적 질문 1개뿐이라 항목 수가 적음.
    # 그래도 요청 본문 크기를 무제한으로 열어두지 않도록 넉넉히 상한선을 둠.
    chat_symptoms: list[str] = Field(default_factory=list, max_length=30)
    # RAG용 언어 중립 신호 (프론트가 안 보내도 기본값으로 동작 — 하위 호환)
    cataract_code: str = Field(default="", max_length=20)
    amsler_abnormal: bool = Field(default=False)
    symptom_codes: list[str] = Field(default_factory=list, max_length=30)
    eye_asymmetric: bool = Field(default=False)   # 편측(한쪽 눈만) 백내장 위험

class ChatRequest(BaseModel):
    lang: str = Field(default="ko", max_length=10)
    user_msg: str = Field(..., min_length=1, max_length=1000)
    context: str = Field(default="", max_length=5000)

class QuestionGenRequest(BaseModel):
    lang: str = Field(default="ko", max_length=10)
    cataract_res: str = Field(..., max_length=100)
    amsler_res: str = Field(..., max_length=100)
    chat_history: list[ChatHistoryItem] = Field(default_factory=list, max_length=50)

class SaveDiagnosisRequest(BaseModel):
    cataract_result: str = Field(..., max_length=200)
    amsler_result: str = Field(..., max_length=100)
    chat_symptoms: list[str] = Field(default_factory=list, max_length=30)
    gemma_opinion: str = Field(default="", max_length=5000)