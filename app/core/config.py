from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_host: str = "localhost"
    db_name: str = "eyecatch_db"
    db_user: str = "postgres"
    db_password: str = ""  # .env에서 읽어옴
    db_port: int = 5432
    # 현재 배포 모델 = EfficientNet-B0 v5(밝은 홍채 보강). v5는 v4 파일명을 그대로
    # 덮어쓰는 운영 방식이라 경로에 _v4가 남아 있다(README "모델 성능" 참고).
    # .env가 없는 새 클론도 배포 모델을 그대로 쓰도록 기본값을 여기에 맞춘다 —
    # 기본값이 구세대(v3)면 학습↔서빙 일관성 테스트가 엉뚱한 메타데이터를 검증하게 된다.
    model_path: str = "cataract_efficientnet_b0_v4.pth"
    model_backbone: str = "efficientnet_b0"   # 가중치와 짝이 맞아야 함 (resnet18 | efficientnet_b0)
    ollama_url: str = "http://localhost:11434/api/generate"
    # 노트북(6GB급 VRAM)에서는 e4b가 120초 타임아웃에 걸린다 — 경량 e2b를 기본으로.
    # VRAM이 넉넉한 실습실 PC에서는 .env의 OLLAMA_MODEL로 e4b를 지정하면 된다.
    ollama_model: str = "gemma4:e2b-it-qat"
    ollama_timeout_seconds: float = 120.0
    kakao_rest_key: str = ""   # 카카오 로컬 REST API 키(.env의 KAKAO_REST_KEY) — 안과 검색용
    max_upload_size_bytes: int = 10 * 1024 * 1024  # .env의 MAX_UPLOAD_SIZE_BYTES로 덮어쓰기 가능

    # --- 판정 임계값 (여러 서비스 파일에 흩어져 있던 것을 한 곳으로 모음) ---
    # 백내장 위험 판정(%): v2 모델 테스트셋 기준 75%에서는 FN=2, 50%에서는 FN=0.
    # 스크리닝은 FN 최소화가 우선이라 50% 채택.
    risk_threshold: float = 50.0
    # 경계(borderline) 판정 하한(%): 이 값 이상 ~ risk_threshold 미만이면 '정상' 대신
    # '경계 — 재촬영/검진 권장'으로 안내. efficientnet_b0 v4 + TTA 분석 근거:
    # test에서 놓친 백내장 5건 중 2건이 39.7%로 이 구간에 있었고, 정상 사진이
    # 경계로 분류되는 부담은 val 1/2305 · test 1/2268 (0.04%)에 불과.
    # 확률 분포가 양극단에 몰려 있어(20~50% 구간 test 4/2540장) 비용이 거의 없다.
    borderline_threshold: float = 25.0
    # MTCNN 얼굴 검출 확신도 하한 — 눈 클로즈업 사진을 얼굴로 오인하는 것을 방지
    face_prob_threshold: float = 0.95
    # 눈 분포 중심과의 코사인 유사도 임계값. 실측: 눈 최소 0.62 / 비-눈 최대 0.50 → 중간값 0.55
    eye_sim_threshold: float = 0.55

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
