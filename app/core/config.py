from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_host: str = "localhost"
    db_name: str = "eyecatch_db"
    db_user: str = "postgres"
    db_password: str = ""  # .env에서 읽어옴
    db_port: int = 5432
    model_path: str = "cataract_resnet18_v3.pth"  # train_ai_v3.py가 생성하는 그룹분할 재학습 가중치
    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_model: str = "gemma4:e4b-it-qat"
    ollama_timeout_seconds: float = 120.0
    kakao_rest_key: str = ""   # 카카오 로컬 REST API 키(.env의 KAKAO_REST_KEY) — 안과 검색용
    max_upload_size_bytes: int = 10 * 1024 * 1024  # .env의 MAX_UPLOAD_SIZE_BYTES로 덮어쓰기 가능

    # --- 판정 임계값 (여러 서비스 파일에 흩어져 있던 것을 한 곳으로 모음) ---
    # 백내장 위험 판정(%): v2 모델 테스트셋 기준 75%에서는 FN=2, 50%에서는 FN=0.
    # 스크리닝은 FN 최소화가 우선이라 50% 채택.
    risk_threshold: float = 50.0
    # MTCNN 얼굴 검출 확신도 하한 — 눈 클로즈업 사진을 얼굴로 오인하는 것을 방지
    face_prob_threshold: float = 0.95
    # 눈 분포 중심과의 코사인 유사도 임계값. 실측: 눈 최소 0.62 / 비-눈 최대 0.50 → 중간값 0.55
    eye_sim_threshold: float = 0.55

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
