from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    db_host: str = "localhost"
    db_name: str = "eyecatch_db"
    db_user: str = "postgres"
    db_password: str = ""  # .env에서 읽어옴
    db_port: int = 5432
    # 현재 배포 모델 = EfficientNet-B0 v6(익상편 정상군 편입). v6도 v4 파일명을 그대로
    # 덮어쓰는 운영 방식이라 경로에 _v4가 남아 있다(메타데이터 version 필드 참고).
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
    # 무거운 추론/LLM 작업이 동시에 몰릴 때 CPU·VRAM이 고갈되지 않도록 제한한다.
    max_inference_concurrency: int = 1
    max_llm_concurrency: int = 2

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
    # 눈 분포 중심과의 코사인 유사도 임계값.
    #
    # 0.55 → 0.62 (2026-08-29). 왜 올렸나:
    #   기존 0.55는 "눈 최소 0.62 / 비-눈 최대 0.50"이라는 실측의 중간값이었다.
    #   그런데 그때의 비-눈 표본에 '단색 배경 + 가운데 큰 블롭' 계열이 없었다.
    #   실사용 테스트에서 초록 배경에 빨간 사각형만 그린 이미지가 게이트를 통과해
    #   "AI 위험 점수 43.2 / 경계 단계 (안과 검진 권장)"이라는 의료 결과를 받았다.
    #   ImageNet 임베딩에서 '가운데 덩어리 + 배경'은 눈의 거친 구조와 실제로 닮았다.
    #
    # 재실측 (scripts/probe_eye_gate.py, dataset 무작위 600장 + 합성 비-눈 88장):
    #   눈       : 최소 0.595 / 그다음 0.633 / p5 0.716 / 중앙값 0.81
    #   비-눈    : 최대 0.620 (블롭 계열) / 문서 0.536 / 단색 0.401 / 노이즈 0.371
    #   임계값별 : 0.55 → 눈 거부 0.00%, 비-눈 통과 56.8%
    #             0.62 → 눈 거부 0.17%(1/600), 비-눈 통과  1.1%(1/88)
    #             0.65 → 눈 거부 0.67%(4/600), 비-눈 통과  0.0%
    #
    # 0.62를 고른 이유: 비-눈 통과를 57%에서 1%로 줄이면서 눈 거부는 600장 중 1장.
    #   더 올리면(0.65+) 합성 표본은 0%가 되지만, 여기 쓴 양성 표본은 centroid를
    #   만든 데이터셋과 같은 분포라 실제 사용자 사진은 이보다 낮게 나올 수 있다.
    #   실사용 사진에서 오거부가 보고되면 이 값을 먼저 의심하고 재실측할 것.
    # 재현: python scripts/probe_eye_gate.py --dataset dataset --n 300
    eye_sim_threshold: float = 0.62
    # 눈/비-눈 게이트(eye_gate.npz) 통과 하한. npz에 기록된 학습 임계값(0.183)과
    # 이 값 중 큰 쪽이 적용된다 — 즉 낮출 수는 없고 조이기만 할 수 있다.
    #
    # 이 값을 정하기까지 (전부 실측, scripts/evaluate_eye_gate.py · build_eye_gate.py):
    #   0.207  학습 임계값. 도서관 사진(vision-scene.jpg, 0.390)이 통과해 '정상'이 나갔다.
    #   0.40   그 사진 점수 바로 위로 올렸다. 그런데 같은 사진의 3x3 상단 중앙 조각이
    #          0.612로 여전히 통과했다 — 사진 한 장에 맞춘 값은 부류를 막지 못한다.
    #   0.65   저장소 사진에서 만든 음성 136개로 정했다. 그 표본에서는 통과 0%였다.
    #   ⇒ 그런데 Wikimedia Commons에서 '처음 보는' 비-눈 사진 60장(크롭 840개)을 받아
    #     다시 재보니 0.65에서도 7.6%가 통과했다. 내부 표본이 낙관적이었던 것이다.
    #     → 임계값이 아니라 게이트 자체를 고쳐야 한다는 결론.
    #
    # 게이트 재학습 (2026-09-05, dataset_noneye/ 실사진 108장 학습 · 60장은 평가용으로 제외):
    #   처음 보는 비-눈 사진 840개 크롭 기준 최고점 0.930 → 0.487로 내려갔다.
    #
    #   구성                          비-눈 통과   정상 눈 거부   백내장 거부   가려진 눈 거부
    #   구 게이트 @0.65 (직전)           7.6%        5.3%         1.0%        99.0%
    #   새 게이트 @0.60 (현재)           0.0%        4.7%         0.7%        98.2%
    #   새 게이트 @0.65                  0.0%        6.0%         1.0%        98.5%
    #
    # 0.60을 고른 이유: 네 지표 중 셋이 직전보다 좋고, 나빠지는 것은 '가려진 눈' 0.8%p뿐이다
    # (그 경로는 MTCNN·선명도 게이트가 한 겹 더 막는다). 관측된 비-눈 최고점 0.487보다
    # 0.113 위라 여유도 있다 — 0.50은 여유가 0.013뿐이라 0.40 때의 실수를 반복하게 된다.
    #
    # ⚠️ 여전한 한계: 평가 사진 60장은 13개 범주에서 골랐을 뿐 실사용 오입력의 분포가 아니다.
    #    "0% 통과"는 이 60장에 대한 것이지 모든 사진에 대한 보장이 아니다.
    #    실사용에서 오거부·오통과가 보이면 dataset_noneye/에 그 사진을 추가하고
    #    build_eye_gate.py를 다시 돌린 뒤 evaluate_eye_gate.py로 표부터 다시 만들 것.
    eye_gate_threshold: float = 0.60
    # 좌우반전 TTA. v5에서는 사용자 관점(3단계 안내)으로 동률이었지만, v6(익상편 편입 재학습)에서는
    # test FN 7→9, FP 2→3으로 손해(2026-09-02 재측정)라 기본 OFF. 백본·데이터를 바꾸면 재측정 후 결정.
    use_tta: bool = False

    @property
    def allowed_origins_list(self) -> list[str]:
        """쉼표 구분 문자열 → origin 리스트. 빈 항목·주변 공백은 버린다."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def model_file(self) -> Path:
        """상대 MODEL_PATH를 프로세스 cwd가 아니라 저장소 루트 기준으로 해석한다."""
        path = Path(self.model_path).expanduser()
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def model_metadata_path(self) -> Path:
        path = self.model_file
        return path.with_name(f"{path.stem}_metadata.json")

    @model_validator(mode="after")
    def validate_runtime_ranges(self):
        """잘못된 환경변수로 판정 구간이 겹치는 상태는 기동 전에 차단한다."""
        if not (0 <= self.uncertain_threshold < self.borderline_threshold < self.risk_threshold <= 100):
            raise ValueError(
                "임계값은 0 <= UNCERTAIN_THRESHOLD < BORDERLINE_THRESHOLD "
                "< RISK_THRESHOLD <= 100 이어야 합니다."
            )
        if self.max_upload_size_bytes <= 0:
            raise ValueError("MAX_UPLOAD_SIZE_BYTES는 0보다 커야 합니다.")
        if self.ollama_timeout_seconds <= 0:
            raise ValueError("OLLAMA_TIMEOUT_SECONDS는 0보다 커야 합니다.")
        if self.max_inference_concurrency <= 0:
            raise ValueError("MAX_INFERENCE_CONCURRENCY는 0보다 커야 합니다.")
        if self.max_llm_concurrency <= 0:
            raise ValueError("MAX_LLM_CONCURRENCY는 0보다 커야 합니다.")
        if not (0 < self.eye_gate_threshold < 1):
            raise ValueError("EYE_GATE_THRESHOLD는 0과 1 사이여야 합니다.")
        return self

    # IDE·서비스 관리자가 저장소 밖 cwd에서 서버를 띄워도 같은 설정을 읽는다.
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

settings = Settings()
