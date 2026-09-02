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

    # 이 API를 호출하도록 허용할 외부 origin 목록(쉼표 구분). 기본은 빈 값 = CORS 미적용.
    # 프론트가 같은 서버(/static)에서 서빙되므로 평소에는 same-origin이라 CORS 헤더 자체가
    # 필요 없다 — ngrok으로 공유해도 페이지와 API가 같은 도메인이라 마찬가지다.
    # 예전에는 allow_origins=["*"]로 전부 열어뒀는데, 쓰지도 않는 개방이라 좁혔다.
    # 프론트를 별도 도메인에 올려 이 API를 부를 때만 여기에 나열한다.
    #   예) ALLOWED_ORIGINS=http://localhost:8000,https://myapp.example.com
    allowed_origins: str = ""

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
    # '판단 어려움(uncertain)' 하한(%): 이 값 이상 ~ borderline 미만은 '뚜렷한 특징 없음'이 아니라
    # '사진만으로 판단 어려움 — 눈 클로즈업 재촬영'으로 안내한다. 외부 테스트(2026-09-02, AI 생성 얼굴 5장):
    # 옅은 초기 혼탁이 0~4.9점으로 나와 전부 '정상'으로 표시됐다. v6 test(라벨 정정) 분포: 정상 2,230장 중
    # 1~25점 8장(0.4%), 백내장은 0장 — 이 구간을 따로 안내해도 비용이 거의 없다.
    uncertain_threshold: float = 2.0
    # MTCNN 얼굴 검출 확신도 하한 — 눈 클로즈업 사진을 얼굴로 오인하는 것을 방지
    face_prob_threshold: float = 0.95
    # 눈 분포 중심과의 코사인 유사도 임계값. 실측: 눈 최소 0.62 / 비-눈 최대 0.50 → 중간값 0.55
    eye_sim_threshold: float = 0.55
    # 좌우반전 TTA. v5에서는 사용자 관점(3단계 안내)으로 동률이었지만, v6(익상편 편입 재학습)에서는
    # test FN 7→9, FP 2→3으로 손해(2026-09-02 재측정)라 기본 OFF. 백본·데이터를 바꾸면 재측정 후 결정.
    use_tta: bool = False

    @property
    def allowed_origins_list(self) -> list[str]:
        """쉼표 구분 문자열 → origin 리스트. 빈 항목·주변 공백은 버린다."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
