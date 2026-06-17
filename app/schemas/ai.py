from pydantic import BaseModel, Field

class ChatHistoryItem(BaseModel):
    q: str = Field(..., min_length=1, max_length=500)
    a: str = Field(default="", max_length=500)

class GemmaRequest(BaseModel):
    lang: str = Field(default="ko", max_length=10)
    cataract_res: str = Field(..., max_length=100)
    amsler_res: str = Field(..., max_length=100)
    chat_symptoms: list[str] = Field(default_factory=list)

class ChatRequest(BaseModel):
    lang: str = Field(default="ko", max_length=10)
    user_msg: str = Field(..., min_length=1, max_length=1000)
    context: str = Field(default="", max_length=5000)

class QuestionGenRequest(BaseModel):
    lang: str = Field(default="ko", max_length=10)
    cataract_res: str = Field(..., max_length=100)
    amsler_res: str = Field(..., max_length=100)
    chat_history: list[ChatHistoryItem] = Field(default_factory=list)

class SaveDiagnosisRequest(BaseModel):
    cataract_result: str = Field(..., max_length=200)
    amsler_result: str = Field(..., max_length=100)
    chat_symptoms: list[str] = Field(default_factory=list)
    gemma_opinion: str = Field(default="", max_length=5000)