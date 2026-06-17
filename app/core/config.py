from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_host: str = "localhost"
    db_name: str = "eyecatch_db"
    db_user: str = "postgres"
    db_password: str = ""  # .env에서 읽어옴
    db_port: int = 5432
    model_path: str = "cataract_resnet18.pth"  # train_ai.py가 생성하는 전이학습 가중치
    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_model: str = "gemma4:e4b"
    ollama_timeout_seconds: float = 120.0
    max_upload_size_bytes: int = 10 * 1024 * 1024  # .env의 MAX_UPLOAD_SIZE_BYTES로 덮어쓰기 가능

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()