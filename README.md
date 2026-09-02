# 👁️ Eye-Catch — 안구질환 AI 스크리닝 앱

> **AI 사진 분석 + LLM 맞춤형 소견서**로 안구질환을 조기 발견하세요.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue" />
  <img src="https://img.shields.io/badge/FastAPI-Latest-green" />
  <img src="https://img.shields.io/badge/PyTorch-2.12-red" />
  <img src="https://img.shields.io/badge/Languages-6-orange" />
  <img src="https://img.shields.io/badge/tests-162%20passed-brightgreen" />
</p>

> ⚕️ **이 앱은 의료기기가 아닙니다.** 비상업적 학술 연구(졸업작품) 목적의 자가진단 보조
> 도구이며, 진단을 대체하지 않습니다. 성능 수치는 **공개 데이터셋 내부 기준**이고,
> 실제 폰 사진에서의 성능은 아직 검증되지 않았습니다. 한계는
> [모델의 한계](#️-모델의-한계-읽고-시작하세요)에 정리해두었습니다.

---

## 📑 목차

| | |
|---|---|
| [🎯 주요 기능](#-주요-기능) | 무엇을 하는 앱인가 |
| [🚀 시작 가이드](#-시작-가이드) | 설치부터 실행까지 |
| [🏗️ 아키텍처](#️-아키텍처) | 폴더 구조와 역할 |
| [📊 모델 성능](#-모델-성능) | v6/v5/v4/v3 실측 지표와 선택 근거 |
| [⚠️ 모델의 한계](#️-모델의-한계-읽고-시작하세요) | **먼저 읽어야 할 것** |
| [🔦 플래시 반사 대응](#-플래시-반사-대응) | 오탐 원인과 차단 방법 |
| [📜 데이터 출처 및 라이선스](#-데이터-출처-및-라이선스) | 출처별 위험도 전수 공개 |
| [🔍 API 엔드포인트](#-api-엔드포인트) | 6개 라우트 |
| [🛠️ 개발 팁](#️-개발-팁) | 테스트·CI·캐시·오프라인 |
| [📱 모바일·접근성](#-모바일접근성) | 글자 크기·카메라·폴더블·시야 체험 |
| [🐛 알려진 이슈](#-알려진-이슈--해결책) | 증상별 해결 |

---

## 🎯 주요 기능

### 1️⃣ **백내장 AI 자동 진단 (눈별 판정)**
- **전이학습 EfficientNet-B0** 모델 (ImageNet 사전학습) — v4 백본 비교에서 ResNet18을 이겨 채택
- v5(밝은 홍채 보강): 그룹 단위 분할(근접중복 누수 차단) 기준 테스트셋 민감도 **98.9%** | 특이도 **99.5%** | AUC **0.9999**, 밝은 홍채 정상 눈 오탐 **86%→18%** (자세한 내용은 "모델 성능" 섹션 참고)
- ⚠️ **현재 서빙 중인 가중치는 v6**(2026-08-26, 익상편 226장을 정상 클래스에 편입해 재학습)입니다.
  특이도는 99.9%로 올랐지만 민감도가 97.6%로 내려가(FN 1→7) **재검토 중**이며, v5 가중치는
  `cataract_efficientnet_b0_v5_prepterygium.pth`로 보관돼 한 줄로 되돌릴 수 있습니다 → [모델 성능](#-모델-성능), `docs_retrain_v6.md`
- 전체 17,017장 중 절반가량이 근접중복 그룹에 속합니다. 이미지를 삭제하지 않고, 같은 그룹이 서로 다른 split에 갈라지지 않도록 분할합니다.
- 추론 시 **좌우반전 TTA**(원본+거울상 평균) 적용 — 운영과 평가가 같은 방식
- **3단계 판정**: 위험(≥50%) / **경계(25~50%** — 재촬영·검진 권장) / 정상(<25%).
  경계 구간은 "정상으로 안심시키기엔 애매한" 확률대를 안내로 돌려, 문턱 바로 아래의 놓침(FN)을 줄입니다.
- **좌/우 눈 개별 분석** — 얼굴 사진에서 양쪽 눈을 따로 판정하고,
  한쪽만 위험하면 **"편측 의심" 배지** 표시 (편측 백내장 대응)
- MTCNN 얼굴→눈 크롭 (얼굴 사진/눈 클로즈업 모두 지원)
- 🆕 **플래시 반사 판독 보류** — 각막에 맺힌 플래시 반사를 모델이 수정체 혼탁으로
  오독하는 것을 막습니다. 눈동자 위 순백(포화) 픽셀이 기준을 넘으면 판정 대신
  재촬영을 요청합니다. 측정 근거와 임계값 산출은 ["플래시 반사 대응"](#-플래시-반사-대응) 참고.
- **흔들림 판독 보류** — 눈 부위 선명도(라플라시안 분산/대비)가 기준 미만이면 `blurry`로
  돌려보내 재촬영을 안내합니다. 실측(2026-09-02): 1280px 얼굴 사진 기준 손떨림 8px까지는
  통과, 12px(눈 폭의 5.5%)부터 보류. 초점 흐림에는 더 민감(2px). 모델 자체는 사진 폭 5%
  손떨림까지 판정이 거의 바뀌지 않아(정상 40장 0건, 백내장 40장 3건 변화), 이 게이트는
  "판독 불가한 입력을 되돌려보내는 장치"이지 정확도 장치가 아닙니다.

### 2️⃣ **멀티모달 안구질환 검사**
- 🖼️ **백내장 AI 분석** — 이미지 기반
- 📊 **황반변성 자가진단** — Amsler Grid 테스트 (좌/우 눈 각각)
- 📋 **위험도 층화 문진** — 위험요인 5문항 + 질환별 조건부 분기 문항
  (당뇨망막병증 문항은 당뇨가 있다고 답한 사람에게만 묻습니다)
- 🧭 **행동 권고(triage)** — 등급이 아니라 "언제 병원에 가야 하는가"를 먼저 보여줍니다

### 3️⃣ **Gemma LLM 3줄 요약 (RAG 그라운딩 + 안전 필터)**
- 리포트의 AI 섹션은 **정확히 3줄**입니다(팀 결정 2026-09-02): ① 안과에서 받게 될 검사
  ② 문진 항목과 연결된 생활 관리 조언 ③ 추가 조언 또는 정기 검진 권유. 6개 언어 모두 같은 구조이며,
  실제 Ollama 출력이 3줄로 나오는 것을 확인했습니다.
- **검사 결과의 해석은 LLM이 하지 않습니다.** 판정·편측·암슬러 해석은 프론트가 코드로 고정 문장을
  만들고(`app-findings.js`), LLM은 조언만 씁니다. 수치·확률·"가능성이 낮다" 같은 배제 표현·질환 교차
  문장은 서버 안전 필터(`safety.py`)가 문장 단위로 걸러냅니다.
- 🆕 **RAG (Retrieval-Augmented Generation)** — 안과 4대 질환 참고지식
  베이스(`data/medical_knowledge.json`)에서 환자 결과에 맞는 내용을 검색해 프롬프트에 주입 →
  모델이 **검증된 의학 정보에 근거**해 답변 (환각 위험↓)
- 🆕 **하트비트 스트리밍** — 생성 지연 시에도 연결을 유지해 모바일·ngrok
  환경에서 답변이 중간에 끊기지 않음
- 로컬 Ollama 서버로 개인정보 보호 (기본 모델: `gemma4:e2b-it-qat`)

### 4️⃣ **6개국어 지원** 🌍
- 🇰🇷 한국어 | 🇺🇸 English | 🇪🇸 Español
- 🇫🇷 Français | 🇯🇵 日本語 | 🇨🇳 中文
- 브라우저 언어 자동 감지 + 사용자 선택 저장

### 5️⃣ **주변 안과 찾기 (인터랙티브 지도)** 🗺️
- **Leaflet 지도**(OSM) 위에 내 위치 + 주변 안과를 **마커**로 표시
- 🆕 **카카오 로컬 API**로 한국 안과 검색 (이름·주소·거리·길찾기) — 서버에서
  호출하므로 **사이트 도메인 등록 불필요** (REST 키만 `.env`에)
- 🆕 해외는 **OSM Overpass**로 폴백 → 전 세계 best-effort, 실패 시 외부 검색 링크
- 목록 탭 → 지도 이동, 마커 클릭 → 팝업

### 6️⃣ **고품질 PDF 리포트**
- 4섹션 진단 리포트 (AI·황반·문진·AI 3줄 요약 — 요약은 줄마다 문단으로 나뉘어 PDF에서도 3줄)
- 다국어 자동 번역
- 페이지 경계 깔끔하게 분할

### 7️⃣ **외부 공유** (ngrok)
```bash
ngrok http 8000
# 공개 HTTPS URL 자동 생성 → 모바일·원격 공유 가능
```

### 8️⃣ **모바일 촬영·접근성** (2026-09-02 팀 피드백)
- 📷 **카메라로 바로 찍기** — 터치 기기에서는 파일 선택 대신 카메라 앱이 바로 열립니다(`capture`).
- 🖼️ **촬영 예시** — 촬영 팁 아래에 CC0 얼굴 사진으로 **좋은 예 / 흔들린 예**를 보여줍니다.
  흔들린 예는 실제 서버 파이프라인에서 `blurry`로 돌아오는 강도로 만들었습니다.
- 🔠 **글자 크기 3단계**(A−/A+, 16·18·20px) — 선택은 저장되고 첫 화면부터 적용. 3줄 요약 본문도 함께 커집니다.
- 👁️ **질환 시야 체험** — 질환 소개 탭 맨 아래 버튼 → 4개 질환을 칩으로 골라 CC0 실사진 위에서
  흐림·황변·중심 암점·터널 시야·출혈 얼룩을 슬라이더로 체험합니다.
- 📱 320px(폴드 커버)부터 1280px까지 폭별로 넘침·잘림을 점검했습니다 → [모바일·접근성](#-모바일접근성)

---

## 🏗️ 아키텍처

```
Eye-Catch (C:\eye_catch)
│
├── 🔙 백엔드 (FastAPI, Python)
│   ├── app/
│   │   ├── main.py              # 앱 진입점
│   │   ├── core/config.py       # 환경 설정 (.env 연동)
│   │   ├── api/routes.py        # REST API
│   │   ├── models/
│   │   │   └── cataract_model.py  # 백본 빌더 (resnet18 | efficientnet_b0)
│   │   └── services/
│   │       ├── vision.py        # AI 추론 + 임계값 + 눈별/편측 판정
│   │       ├── eye_detector.py  # MTCNN 얼굴→눈 크롭 (좌/우는 사진 x좌표로 확정)
│   │       ├── llm.py           # Gemma 3줄 요약 프롬프트 + RAG + 하트비트 스트리밍
│   │       ├── safety.py        # LLM 출력 안전 필터 (확률·배제·질환 교차·진단 표현 제거)
│   │       ├── knowledge.py     # 🆕 RAG 안과 참고지식 베이스 + 검색
│   │       ├── clinics.py       # 🆕 주변 안과 검색 (카카오/Overpass)
│   │       └── database.py      # 진단 기록 저장
│   ├── scripts/                 # 🆕 학습·데이터 도구 (저장소 어디서 실행해도 동작)
│   │   ├── dedup_dataset.py         # 근접중복 탐지 (phash, 정확한 O(n²)) → data/dataset_group_map.json
│   │   ├── train_ai_v3.py           # 그룹 분할 + 라벨충돌 제외 + 불균형 보정 학습 스크립트
│   │   ├── train_ai_v4.py           # 백본 비교 학습 (--backbone resnet18|efficientnet_b0)
│   │   ├── validate_real_photos.py  # 실사진(폰 촬영)으로 배포 파이프라인 검증 (시연 전 필수)
│   │   ├── smoke_eye_detect.py      # 사진 1장으로 얼굴→눈크롭→판정 경로 확인하는 수동 CLI
│   │   └── build_eye_centroid.py    # 눈 검증기(OOD) 기준 벡터 생성 + 임계값 근거 산출
│   ├── data/                    # 🆕 파이프라인 산출물 (이미지 아님)
│   │   ├── dataset_group_map.json    # dedup_dataset.py 출력 — 근접중복 그룹 매핑
│   │   ├── label_conflicts.json      # 학습에서 제외한 라벨 충돌 이미지 목록
│   │   └── brightiris_attributions.csv  # v5 보강분 201장 출처·라이선스 전수 기록
│   ├── tests/                   # 🆕 pytest 자동 테스트 (수 초 완료, GPU·Ollama·DB 불필요)
│   ├── requirements.txt         # 의존성 (CUDA torch) — 나머지는 requirements-base.txt
│   ├── .github/workflows/       # 🆕 CI — PR마다 pytest 자동 실행
│   └── dataset/                 # 이미지 데이터셋 (17,243장, 근접중복 그룹 단위 분할)
│       ├── 0_normal/            # 정상 안구 15,420장 (v5 밝은 홍채 201장 + v6 익상편 226장 포함)
│       └── 1_cataract/          # 백내장 1,823장
│
├── 🎨 프론트엔드 (Vanilla JS + Tailwind CSS)
│   └── static/
│       ├── index.html           # SPA 마크업
│       ├── app-core.js          # 공통 기반 (state·i18n·스트림 리더·로더) — 항상 먼저 로드
│       ├── app-vision.js        # 백내장 분석 요청/결과 렌더 (눈별·편측 표시)
│       ├── app-chat.js          # 문진 챗봇 (고정 질문 + 동적 질문)
│       ├── app-report.js        # 소견서 스트리밍 + PDF 생성
│       ├── app-disease.js       # 질환 카드/모달 + 시야 체험 패널
│       ├── app-map.js           # Leaflet 지도 + 주변 안과 목록
│       ├── data.js              # 6개국어 번역 + 문진 질문 + 질환 데이터
│       ├── style.css            # 커스텀 스타일 (글자 크기 단계·폴더블/소형 화면 규칙 포함)
│       └── assets/
│           ├── examples/        # 촬영 예시 얼굴 사진 (CC0 가공, ATTRIBUTION.md)
│           ├── vision-scene.jpg # 시야 체험 장면 (CC0, ATTRIBUTION-vision-scene.md)
│           └── diseases/        # 질환 임상 사진 (출처·라이선스 ATTRIBUTION.md)
│
└── 📦 배포 & 설정
    ├── .env                     # 환경변수 (DB 비번, LLM 설정)
    ├── .gitignore              # Git 제외 규칙
    ├── ngrok.exe               # 외부 공유 도구
    └── .venv/                  # 가상환경 (저장소에 제외)
```

---

## 🚀 시작 가이드

### 📋 사전 조건
- **Python 3.11+**
- **CUDA 가능한 GPU** (권장) 또는 CPU
- **Ollama** (LLM 소견서 생성용)
- **VS Code** (선택)

### 1️⃣ 저장소 클론
```bash
git clone https://github.com/KangSky77/Eye-Catch-Project.git
cd Eye-Catch-Project
```

### 2️⃣ 가상환경 & 패키지 설치
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 의존성 설치 (버전 고정 — GPU 환경용. CPU/CI는 requirements-base.txt + CPU torch)
pip install -r requirements.txt

# 추가 패키지 (선택)
pip install --no-deps facenet-pytorch  # 얼굴→눈 크롭용
```

### 3️⃣ 환경변수 설정
`.env.example`을 복사해 `.env`로 저장 후 값을 채우세요 (`MODEL_PATH`와 `MODEL_BACKBONE`은
**반드시 짝이 맞아야** 합니다):
```bash
cp .env.example .env
```
```ini
# .env.example 주요 항목 — 가중치(.pth)는 git에 없으므로 팀원에게 받거나 재학습
MODEL_PATH=cataract_efficientnet_b0_v4.pth
MODEL_BACKBONE=efficientnet_b0

# 데이터베이스
DB_HOST=localhost
DB_NAME=eyecatch_db
DB_USER=postgres
DB_PASSWORD=your_password

# LLM (Ollama) — 노트북(6GB급)에서 e4b는 120초 타임아웃에 걸려 e2b가 기본.
# VRAM이 넉넉하면 gemma4:e4b-it-qat로 올려도 됩니다.
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=gemma4:e2b-it-qat
OLLAMA_TIMEOUT_SECONDS=120

# 주변 안과 검색 (선택) — 카카오 로컬 REST API 키
# developers.kakao.com → 내 앱 → REST API 키, 그리고 [제품 설정 → 카카오맵] 활성화 필수
# 비워두면 해외는 OSM Overpass, 그것도 없으면 외부 검색 링크로 폴백
KAKAO_REST_KEY=
```

### 4️⃣ AI 모델 학습 (또는 사전학습 가중치 다운로드)
```bash
python scripts/dedup_dataset.py                            # 1회 — data/dataset_group_map.json 생성
python scripts/train_ai_v4.py --backbone efficientnet_b0 --batch 40 --version v5   # → cataract_efficientnet_b0_v4.pth (현재 배포 모델)
python scripts/train_ai_v4.py --backbone resnet18          # (선택) 백본 비교용

# --batch 40: 배포 중인 v5 모델과 동일 조건 (메타데이터 batch_size 기록과 일치).
#   6GB급 노트북에서 추론 서버·Ollama와 GPU를 나눠 쓸 때의 OOM 방지 겸용 —
#   학습이 GPU를 독점하는 큰 GPU에서도 v5 재현이 목적이면 40을 유지하세요.

# 또는 사전학습 가중치 사용 → 프로젝트 루트에 배치 후 .env의 MODEL_PATH/MODEL_BACKBONE 수정
# 참고: RTX 3060 노트북 기준 efficientnet_b0 약 90분, resnet18 약 15분
```

### 5️⃣ Ollama 서버 실행
```bash
# 별도 터미널에서
ollama serve

# Gemma 모델 다운로드 (최초 1회)
ollama pull gemma4:e2b-it-qat
```

### 6️⃣ FastAPI 서버 실행
```bash
# 포트 8000 (또는 .env에서 수정)
uvicorn app.main:app --port 8000 --reload

# ✅ http://localhost:8000 에서 앱 실행
```

### 7️⃣ (선택) 외부 공유 — Ollama
```bash
# 별도 터미널에서
ngrok http 8000

# 💬 공개 HTTPS URL 출력됨 → 모바일·원격 접속 가능
```

---

## 📊 모델 성능

### EfficientNet-B0 v6 (익상편 편입 재학습 — 현재 서빙 가중치, 재검토 중)

v5는 **익상편**(결막이 각막 위로 자라는 질환)을 백내장으로 88.0% 오분류했습니다(정리된 원본 150장 중
위험 120 + 경계 12). 모델이 "수정체 혼탁"이 아니라 "눈이 하얗게 덮였는가"를 학습한 결과이고, 밝은 홍채·
플래시 반사 오탐과 뿌리가 같습니다. 캐글 익상편 데이터 226장(225그룹)을 `0_normal`에 넣어 그 경계를 다시
가르쳤습니다(2026-08-26, 절차는 `docs_retrain_v6.md`). 배포 파일명은 그대로 `cataract_efficientnet_b0_v4.pth`이고
메타데이터 `version`이 `v6`입니다.

test 2,526장(정상 2,230 + 백내장 296, 그룹 단위 분할, 임계값 50%):

| 지표 | v5 | **v6 (현재)** |
|------|------|------|
| 민감도 | 99.6% (FN 1) | **97.6% (FN 7)** — TTA 적용 시 97.0% (FN 9) |
| 특이도 | 99.5% (FP 12) | **99.9% (FP 2)** |
| AUC | 0.9999 | 0.9975 |
| val 민감도 / 특이도 | — | 98.6% / 100% |

- 특이도는 의도대로 올랐지만 **민감도가 내려갔습니다.** `docs_retrain_v6.md`의 성공 기준("백내장 민감도가
  v5에서 떨어지지 않을 것")을 충족하지 못했고, 익상편 오분류율 재측정도 남아 있습니다. 스크리닝은 FN 최소화가
  우선이라 이 트레이드오프는 **팀 재검토 대상**입니다.
- 되돌리기: `cataract_efficientnet_b0_v5_prepterygium.pth`와 `..._v5_prepterygium_metadata.json`을 v4 파일명으로
  복사하면 됩니다(`docs_retrain_v6.md` 5장). `pytest`의 `weights_sha256` 대조가 어느 세대가 서빙 중인지 알려줍니다.

### EfficientNet-B0 v5 (밝은 홍채 데이터 보강 — v6 이전 배포 모델, 백업 보관)

v4의 알려진 약점(밝은 색 홍채의 정상 눈을 백내장으로 오판)을 해소하기 위해, Wikimedia
Commons에서 밝은 홍채(청록·파랑·녹색) 정상 눈 사진 **201장**을 수집해 정상 클래스에 보강하고
같은 레시피로 재학습했습니다(파일별 출처·라이선스는 `data/brightiris_attributions.csv`에 전수 기록).
dedup 전수 비교 결과 201장 중 **196장이 기존 데이터와 겹치지 않는 신규 그룹**이라, 부족하던
서브그룹을 실제로 늘린 것이 확인됐습니다. 배포 파일명은 `cataract_efficientnet_b0_v4.pth`
그대로 덮어썼고, 보강 전 모델은 `cataract_efficientnet_b0_v4_preaug.pth`로 백업해뒀습니다.
**파일명만으로는 세대를 알 수 없으므로**, 메타데이터 JSON의 `version` 필드가 유일한 구분자입니다
(`train_ai_v4.py --version` 로 기록). 로컬 `.pth`가 그 메타데이터와 같은 학습본인지는
`weights_sha256`으로 `pytest`가 대조합니다.

**공정한 before/after 비교**: 보강 후 test 분할에 배정된 밝은 홍채 44장은 **두 모델 모두
학습에 쓰지 않은** held-out입니다(보강 전 모델은 아예 못 봤고, 보강 후 모델은 test 분할이라
안 봤음). 이 44장과 전체 test셋에 대한 결과(임계값 50%, 운영과 동일한 TTA):

| 지표 | 보강 전(preaug) | **보강 후(v5, 채택)** |
|------|------|------|
| **밝은 홍채 held-out 오탐** | 38/44 (86.4%) | **8/44 (18.2%)** |
| **밝은 홍채 평균 백내장 확률** | 88.7% | **16.7%** |
| **전체 test 특이도** | 98.27% (FP=40) | **99.48% (FP=12)** |
| **전체 test 민감도** | 100% (FN=0) | 98.9% (FN=3) |
| **AUC-ROC** | — | **0.9999** |

- 보강 전 모델의 특이도가 v4 표(99.9%)보다 낮게 나온 것은 test 분할에 새로 들어온 밝은
  홍채들을 대거 오탐했기 때문입니다 — 바로 그 약점이 이번 보강의 대상이었습니다.
- 민감도는 FN 3건으로 소폭 내려갔지만, 확인 결과 **3건 전부**가 확률 25~50%(46.9%, 46.9%,
  25.5%)로 "정상"이 아니라 "경계 — 재촬영·검진 권장"으로 안내됩니다. 즉 3단계 판정을 실제로
  받는 사용자 기준으로는 놓치는 백내장이 없고, 오탐 28건 감소만 순수하게 남는 트레이드오프입니다.
- 학습 시 `--batch` 옵션(신규)으로 배치를 40으로 낮췄습니다 — 6GB급 노트북 VRAM에서 추론
  서버·Ollama와 겹치면 기본 64가 CUDA OOM을 내는 문제의 재발 방지책입니다.

#### TTA 재측정 (2026-08-20)

외부 리뷰에서 "메타데이터상 TTA가 FN을 1→3으로 늘리므로 꺼야 한다"는 지적을 받고, 배포
가중치로 test 2,600장을 TTA 유무로 나란히 재측정했습니다.

| 지표 | TTA 없음 | TTA 적용 |
|------|------|------|
| FN (50% 기준) | 1 | 3 |
| **정상으로 안내된 백내장** | **0** | **0** |
| 오탐 (FP) | 12 | 12 |
| 정상인데 경계로 안내 | 4 | 2 |

**지적의 사실관계는 맞지만 처방은 이 앱 구조에 맞지 않습니다.** 3단계 판정을 쓰므로
"놓쳤다"의 기준은 FN이 아니라 **경계에도 못 걸려 '정상'으로 안내된 백내장**이어야 하고,
그 수치는 양쪽 다 0입니다. 늘어난 FN 2건은 전부 경계 구간(25~50%)이 흡수합니다.
정상인을 경계로 보내는 부담도 TTA 쪽이 4→2로 적습니다. 따라서 **TTA를 유지**합니다.

다만 기존 코드 주석이 근거로 삼던 "실사진 변화에 대한 보험"은 측정된 사실이 아니었고,
"무득실"이라는 수치도 v4 시절 것이라 배포 모델(v5)과 맞지 않았습니다. 위 실측표로 교체했습니다.

### EfficientNet-B0 v4 (백본 비교 — v5 이전 기록)

라벨 수정으로 파일 2장이 클래스를 옮기면서 v3 학습 당시의 train/val/test 분할이
같은 시드로도 재현 불가능해졌습니다(클래스별 그룹 목록이 달라져 셔플 결과가 바뀜).
이를 해소하기 위해 `data/dataset_group_map.json`을 재생성하고 **동일 조건에서 두 백본을
재학습·비교**했습니다(`train_ai_v4.py`, v3 레시피 그대로 + `--backbone` 인자만 추가).

| 지표 (test, 임계값 50%) | ResNet18 v4 | **EfficientNet-B0 v4 (채택)** |
|------|------|------|
| **민감도 (Sensitivity)** | 97.4% (FN=7) | **98.2% (FN=5)** |
| **특이도 (Specificity)** | 99.9% (FP=3) | **99.9% (FP=3)** |
| **AUC-ROC** | 0.9997 | **0.9996** |
| **validation (선택 근거)** | 민감도 98.5% / 특이도 100% | **무결점 (2,565장 중 오류 0)** |
| **파라미터** | 11.2M | **5.3M** |

- **선택은 validation, test는 최종 확인 1회** — 데이터 스누핑 방지 원칙 유지.
- **TTA(좌우반전 평균)는 모델마다 득실이 달랐습니다**: v3에선 이득(FN 7→6),
  ResNet18 v4에선 오히려 해로움(FN 7→10). 배포 모델(v5)은 아래 "TTA 재측정" 참고.
  **백본이나 데이터를 바꾸면 반드시 재측정**해야 합니다.
- **3단계 판정(경계 구간 25~50%)**: 확률 분포가 양극단에 몰려 있어(20~50% 구간이 test
  2,540장 중 4장뿐) 경계 안내 비용이 거의 없는데, test에서 놓친 백내장 5건 중 2건(39.7%)이
  이 구간에 있어 "경계 — 재촬영·검진 권장"으로 구제됩니다. 정상이 경계로 분류되는 부담은
  val 1/2,305 · test 1/2,268 (0.04%).
- **알려진 약점**: test 오탐 3건은 모두 **밝은 색(청록·파랑·녹색) 홍채의 정상 눈**이었습니다
  (98.5~99.9% 확신으로 오판). 데이터셋이 어두운 홍채 위주라 밝은 홍채의 뿌연 느낌을 수정체
  혼탁으로 착각하는 것으로 보였고 → **v5 데이터 보강으로 해소**(위 섹션 참고).
- **시연 전 실사진 점검**: 위 수치는 데이터셋 내부 수치입니다. 실제 폰 사진은 도메인 갭으로
  성능이 낮아질 수 있으니, `python scripts/validate_real_photos.py <사진폴더>`로 배포 파이프라인
  그대로(MTCNN→OOD게이트→TTA→3단계 판정) 미리 확인하세요.

### ResNet18 v3 (근접중복 그룹 분할 — v4 이전 기록)

v2는 사진 단위로 무작위 train/val/test 분할을 했는데, `dedup_dataset.py`로 전수 검사한 결과
**원본 16,816장 중 8,639장(약 51%)이 다른 사진의 근접중복**이었습니다(여러 데이터셋을 합치며
같은 사진이 여러 번 들어간 것으로 추정, 고유 사진은 8,177장). 이 상태로는 같은 사진이
train과 test에 동시에 들어가는 누수가 거의 확실해서, v2의 "정확도 99.9% / AUC 1.000"은
부풀려진 수치였습니다.
> `dedup_dataset.py`는 처음엔 64비트 phash를 LSH 밴딩으로 비교해 속도를 아꼈는데, 전수
> 재검증해보니 밴드가 전부 어긋나 후보에서 빠진 근접중복 636쌍이 있었습니다. 16,816장
> 규모에서는 정확한 O(n²) 비교(numpy 바이트 popcount로 벡터화)도 1분 내로 끝나길래 근사
> 방식을 버리고 정확한 비교로 교체했습니다(현재 코드는 LSH 없이 정확 비교만 함). 위
> 수치(8,639장/8,177장)는 이 정확한 비교 결과입니다.

`train_ai_v3.py`는 근접중복을 삭제하지 않고 그룹으로 묶어 **그룹 전체를 하나의 split에만**
배정합니다(`data/dataset_group_map.json`). 정상/백내장 두 클래스에 걸친 라벨 충돌 그룹(같은 사진이
양쪽에 라벨링된 경우)은 **학습/검증/테스트 전부에서 제외**하고 `data/label_conflicts.json`에
기록합니다(3그룹, 33장 — 사람이 직접 확인 후 라벨을 고쳐 재포함할 대상). 또한 Codex 버전의
`WeightedRandomSampler`(배치 내 클래스 비율을 50:50으로 공급)와 `balanced_accuracy + 0.25·F1`
기준 모델 선택을 이식했습니다. 처음엔 손실 함수에도 클래스 가중치를 추가로 줬는데, 샘플러가
이미 배치를 균형 맞춰 공급하는 상태에서 손실까지 가중치를 주면 이중 보정이 된다는 지적(Antigravity
리뷰)을 반영해 **손실 함수는 가중치 없는 일반 `CrossEntropyLoss`로 변경**했습니다. 운영
threshold는 test set을 보지 않고 validation에서만 고른 뒤(`choose_threshold_on_val()`) test는
마지막 1회만 평가합니다.

| 지표 | v2 (누수 있음, 참고용) | **v3 (그룹분할+라벨충돌제외+이중보정해제, 최종)** |
|------|------|------|
| **정확도 (Accuracy)** | 99.9% | **99.3%** |
| **민감도 (Sensitivity)** | 100% (FN=0) | **97.7%** (FN=6) |
| **특이도 (Specificity)** | 99.9% | **99.5%** |
| **AUC-ROC** | 1.000 | **0.999** |
| **Balanced Accuracy** | — | **98.6%** |
| **Cataract F1** | — | **96.7%** |

**v3 테스트셋:** 2,505장 (정상 2,247 + 백내장 258), 그룹 단위 분할로 train/val과 완전히 분리됨.  
**혼동행렬 (임계값 50%):** TN=2236, FP=11, FN=6, TP=252

수치가 v2보다 살짝 낮아졌지만(특히 민감도 100%→97.7%), 이게 데이터 누수·라벨 충돌·이중 보정을
모두 제거한 뒤 측정한 실제 성능입니다. 여전히 임상 스크리닝 용도로는 충분히 높은 성능이며,
이중 보정 해제 전(FP=12)보다 오히려 FP가 1건 줄어(FP=11) 손실 가중치 제거가 성능을 깎지
않았다는 것도 확인됐습니다.

> **운영 threshold는 50%를 그대로 유지합니다.** `choose_threshold_on_val()`이 validation에서
> 목표 민감도 99% 기준으로 고른 threshold는 이전 학습에선 68%, 이번 학습에선 **95%**로
> 매번 다르게 나왔고, 두 번 다 이 threshold를 test에 적용하면 50%보다 결과가 나빴습니다
> (68%→FN 6→8, 95%→FN 6→12). validation의 백내장 샘플이 260장 안팎뿐이라 "딱 목표 민감도를
> 만족하는 경계"가 매번 불안정하게 흔들리는 것으로 보입니다(작은 표본 크기에서 흔한 일반화
> 격차). 스크리닝은 FN 최소화가 우선이므로, **튜닝하지 않은 기본값 50%가 두 차례의 validation
> 기반 탐색보다 일관되게 더 안전했습니다** — 데이터셋이 훨씬 커지기 전까지는 이 결정을 유지합니다.

재현하려면:
```bash
python scripts/dedup_dataset.py                            # 1회 — data/dataset_group_map.json 생성
python scripts/train_ai_v4.py --backbone efficientnet_b0 --batch 40 --version v5   # 현재 배포 모델(v5) 재학습 — batch 40 동일 조건
```
>
> 또한 비-눈 이미지 차단(OOD 검증, `eye_validator.py`)은 ImageNet 사전학습 ResNet18 가중치를 런타임에 받아옵니다. **서버를 처음 띄우는 환경(신규 배포·팀원 PC 등)에서는 최초 1회 인터넷 연결이 필요**하며, 실패하면 눈 클로즈업 분석이 503으로 막힙니다(의도된 fail-closed 동작).

---

## ⚠️ 모델의 한계 (읽고 시작하세요)

위의 테스트셋 지표(민감도 98.9% / 특이도 99.5% / **AUC 0.9999**)는 **이 데이터셋 안에서의**
수치입니다. AUC 0.9999는 의료 영상 과제에서 정상적으로 나오는 값이 아니며, 아래 이유로
**실제 사용 성능은 이보다 상당히 낮을 것으로 봅니다.**

### 1. 정상 클래스와 백내장 클래스의 출처가 다릅니다

| 클래스 | 장수 | 출처 |
|---|---|---|
| 백내장 | 1,823 | Kaggle 임상 사진 10종 (세극등 유사 각도) |
| 정상 | 15,194 | 얼굴 사진에서 크롭 + eye-detection-dataset 2,170 + 위키미디어 201 |

정상 중 최소 **2,371장(15.6%)** 은 백내장 이미지가 아예 없는 출처에서 왔습니다.
즉 모델이 *"수정체가 혼탁한가"* 가 아니라 *"임상 촬영 사진인가, 얼굴 크롭인가"* 를
배웠을 가능성이 있습니다. (`img (N)` 명명을 공유하는 정상도 많아 **부분적** 분리입니다.)

**방증**: v4는 밝은 색 홍채의 정상 눈을 **98.5~99.9% 확신으로** 백내장이라 했습니다.
수정체 혼탁을 보는 모델이라면 나올 수 없는 오류입니다. v5에서 밝은 홍채 201장을 보강해
오탐을 86% → 18%로 줄였지만, **여전히 18%** 입니다.

같은 뿌리의 문제가 플래시 반사에서도 재현됩니다 → [플래시 반사 대응](#-플래시-반사-대응)

### 2. 환자 단위 분할이 아닙니다

`dedup_group`은 근접중복만 막습니다. 같은 사람의 다른 사진이나 좌/우안이 서로 다른
split으로 갈릴 수 있습니다. Kaggle 덤프라 환자 ID가 없어 원천적으로 불가능합니다.

### 3. 실제 폰 사진 검증이 아직 없습니다

`scripts/validate_real_photos.py`는 만들어져 있지만 **아직 실행 기록이 없습니다.**
도메인 갭의 크기가 측정되지 않은 상태입니다. **시연 전에 반드시 돌려보세요.**

```bash
python scripts/validate_real_photos.py <사진폴더>
```

### 4. 안저(망막) 사진을 거르지 못합니다

OOD 게이트가 안저사진을 '눈'으로 통과시킵니다(실측 eye_score 0.63~0.64, 임계 0.55).
이 모델은 **외안부 사진 전용**인데 망막 사진에도 판정을 내립니다. 미해결 이슈입니다.

### 이 수치로 무엇을 말할 수 있나

- ✅ **졸업작품·발표**: 누수 발견 → 그룹 분할 → 약점 발견 → 표적 보강 → 공정한 before/after
  라는 방법론 자체가 강점입니다.
- ❌ **실제 스크리닝 도구**: 아닙니다. 위 4가지가 해소되기 전까지는 데이터셋 내부 성능일 뿐입니다.

---

## 🔦 플래시 반사 대응

> 앱은 원래 "플래시를 켜고 찍으세요"라고 안내했습니다. 측정해보니 **그 안내가 위양성을 만들고 있었습니다.**

### 무슨 일이 있었나

정상으로 잘 판정되던 눈 사진 60장에 플래시 반사를 합성해 다시 돌린 결과:

| 조건 | 정상 | 경계 | 위험 |
|---|---|---|---|
| 원본 | 60 | 0 | 0 |
| 캐치라이트(각막 반사점) 강 | 49 | 1 | **10** |
| 베일글레어(동공 위 뿌연 막) 강 | 40 | 4 | **16** |

반면 **사진 전체 밝기만 1.8배로 올린 대조군은 60장 중 1장**만 바뀌었습니다.
즉 모델은 '밝기'가 아니라 **'눈동자 위 국소 백색 패턴'** 에 반응하며, 그게 정확히
플래시 캐치라이트의 모습입니다. v4의 밝은 홍채 오탐과 같은 뿌리입니다.

### 지표를 고른 과정

처음엔 밝기로 자르려 했으나 실패했습니다 — **백내장 사진이 오히려 더 하얗습니다.**

| | 정상 | 백내장 | 플래시 반사 |
|---|---|---|---|
| 중앙부 순백비율 중앙값 | 0.00% | 0.01% | **3.54%** |

구분되는 건 **포화(saturation)** 였습니다. 플래시 캐치라이트는 세 채널이 모두 255에
붙는 작고 단단한 순백이고, 수정체 혼탁은 회백색이라 포화까지 가지 않습니다.

### 임계값 산출

감이 아니라 **모델이 실제로 속는 지점**을 측정해서 정했습니다.

| 반사점 반경 | 모델 오탐률 | 중앙부 순백비율 |
|---|---|---|
| 4% | 0.0% | 0.56% |
| 6% | 5.0% | 1.27% |
| **8%** | **15.0%** | **2.25%** ← 문제 시작 |
| 10% | 33.3% | 3.54% |
| 14% | 70.0% | 6.85% |

→ **임계 2%**: 눈 크롭 중앙 60% 영역에서 `min(R,G,B) >= 250`인 픽셀 비율
(`app/services/vision.py`의 `GLARE_MAX_FRACTION`)

### 적용 결과 (각 80장)

| | 게이트 전 | 게이트 후 |
|---|---|---|
| 정상 + 플래시 반사 | 위험 18 + 경계 9 | **hold 80/80** |
| 백내장 원본 | risk 80 | risk 79 / hold 1 |
| 정상 원본 | normal 80 | normal 79 / hold 1 |

오거부 1.25%는 '판정 실패'가 아니라 **'다시 찍어주세요' 안내**입니다.
틀린 의료 판정을 내보내는 것보다 비용이 훨씬 낮다고 판단했습니다.

> ⚠️ **이건 증상 차단이지 근본 해결이 아닙니다.** 모델이 '수정체 혼탁'이 아니라
> '눈이 하얗게 보이는 정도'를 학습한 문제는 그대로이며, 재학습 과제로 남습니다.
> 합성 반사이지 실제 플래시 사진이 아니라는 한계도 있습니다.

---

## 📜 데이터 출처 및 라이선스

> ⚠️ **저작권은 등록 없이 자동으로 발생합니다.** 라이선스 표시가 없는("Unknown") 데이터는
> "자유롭게 써도 된다"는 뜻이 아니라 **"아무 허락도 받지 않았다"**는 뜻입니다 — 기본값은
> 허용이 아니라 금지입니다. 이 표는 그 기준으로 출처별 위험도를 정리한 것입니다.

### 백내장 안구 사진 (9개 출처 + 검증 중 추가로 발견된 1건)

| # | 데이터셋 | 라이선스 | 판정 | 왜 그런가 |
|---|---|---|---|---|
| 1 | [Cataract (kershrita)](https://www.kaggle.com/datasets/kershrita/cataract) | MIT | 🟢 안전 | 출처 표기만 하면 자유 사용 명시적 허락 |
| 2 | Cataract Classification Dataset (미확인 출처) | CC BY-SA 4.0 | 🟡 조건부 | ShareAlike — **데이터셋 자체를 재배포**할 때만 동일 라이선스 적용 의무. 학습 전용 사용은 상대적으로 안전 |
| 3 | [Eye Disease Classifier EfficientNet-B3 (rrohit1289)](https://www.kaggle.com/datasets/rrohit1289/eye-disease-classifier-efficientnet-b3) | CC BY 4.0 | 🟢 안전 | 출처 표기만 하면 자유 사용 명시적 허락 |
| 4 | [Cataract Classification Dataset (sheemazain)](https://www.kaggle.com/datasets/sheemazain/cataract-classification-dataset-in-ds) | Apache 2.0 | 🟢 안전 | MIT와 동등(+특허 보호 조항), 우리 사용엔 차이 없음. **phash 검증: 410/410(100%) 완전일치** |
| 5 | [Cataract image (alexandramohammed)](https://www.kaggle.com/datasets/alexandramohammed/cataract-image) | Unknown | 🔴 위험 | 허락 명시 없음 — 기본값은 전부 금지 |
| 6 | Cataract Classification Dataset (미확인 출처) | Apache 2.0 | 🟢 안전 | 출처 표기만 하면 자유 사용 명시적 허락 |
| 7 | [cataract (hemooredaoo)](https://www.kaggle.com/datasets/hemooredaoo/cataract) | Unknown | 🔴 위험 | 허락 명시 없음 — 기본값은 전부 금지 |
| 8 | [Cataract dataset (nandanp6)](https://www.kaggle.com/datasets/nandanp6/cataract-image-dataset) | Data files © Original Authors | 🔴 위험 | 원저작자가 권리 보유를 명시, 사용 허락은 없음. **phash 검증: 306장 실사용 확인, 라벨링 오류 2건 발견·수정함(아래 참고)** |
| 9 | [Eye Diseases Classification (orvile)](https://www.kaggle.com/datasets/orvile/eye-diseases-classification) | CC BY 4.0 | 🟢 안전 | 출처 표기만 하면 자유 사용 명시적 허락 |
| 10 | [cataract-classification-dataset (akshayramakrishnan28)](https://www.kaggle.com/datasets/akshayramakrishnan28/cataract-classification-dataset) | Unknown | 🔴 위험 | 제목이 #2·#6과 같아 처음엔 그 중 하나로 추정했으나, 실제 라이선스가 Unknown으로 확인되어 별도 행으로 분리. **phash 검증: 32/32(100%) 완전일치, 실사용 확인** |

> #1·#3·#4·#5·#7·#8·#9·#10은 링크 확정. **#1·#4·#8·#10은 다운로드해 phash로 직접 대조까지
> 검증**(실제 사용 확정). **#2·#6("Cataract Classification Dataset", CC BY-SA 4.0 / Apache 2.0)은
> 여전히 정확한 링크를 못 찾았습니다** — `akshayramakrishnan28`도 같은 제목이라 후보로 봤었으나
> 라이선스가 Unknown으로 나와 둘 중 어느 쪽도 아닌 것으로 정정, 별도 #10으로 분리했습니다
> (제목만 보고 출처를 단정하면 안 된다는 사례로 기록해둠).

### 밝은 홍채 정상 눈 보강 데이터 (v5)

| # | 출처 | 라이선스 | 판정 | 왜 그런가 |
|---|---|---|---|---|
| 11 | Wikimedia Commons (201장) | Public domain/CC0 34장, CC BY 계열 37장, CC BY-SA 계열 125장, FAL·Copyrighted free use 5장 | 🟢 안전 | **201장 전부 자유 라이선스이며 저작자까지 확정**. 파일별 원저작자·라이선스·원본 링크를 [data/brightiris_attributions.csv](data/brightiris_attributions.csv)에 전수 기록 — CC BY(-SA) 조건인 출처 표기를 이 파일이 담당 |

> ✅ **귀속 정보 전수 확정(2026-08-19)**: Commons API로 전 파일을 재조회해 비어 있던 항목을
> 채웠습니다 — Artist 필드가 공란인 5장은 Commons 관례대로 업로더를 저작자로 기록하고 근거를
> CSV의 새 `notes` 열에 남겼고, `original_title`이 유실돼 있던 2장(`commons_Amber`,
> `commons_Hazel`)은 **phash 대조로 출처를 확정**했습니다(둘 다 해밍거리 0).
> 후자는 원본이 `.png`(File:Hazel eye1.png, CC BY-SA 3.0)라 파일명 기반 `.jpg` 조회로는
> 안 잡히던 건으로, 이름이 비슷한 `.jpg` 후보들은 거리 16~28로 전부 오답이었습니다 —
> **이름 유사도가 아니라 픽셀로 대조해야 하는 이유**의 사례입니다(#2·#6·#10 교훈과 동일).
> 검증 방법은 `dedup_dataset.py`와 같은 설정(phash 64비트, 해밍거리 ≤6)이며, 출처를 이미
> 알고 있던 파일 5건으로 방법 자체를 먼저 검증했습니다(전부 거리 0, 회전본 1건 포함).

> ⚠️ **데이터 품질 수정 기록(2026-06-23)**: #8(nandanp6) 출처와 `dataset/1_cataract`를
> phash로 대조하다가, 같은 사진(`img (175).png`, `img (246).png`)이 원본 출처에서는
> "normal"로 분류돼 있는데 우리 쪽엔 "백내장"으로 잘못 들어가 있는 걸 발견함. 육안 확인
> 결과(수정체 혼탁 없음)도 "정상"에 부합해 두 파일을 `dataset/1_cataract` → `dataset/0_normal`로
> 이동하고 `dedup_dataset.py`를 재실행해 그룹 매핑을 갱신함.

### 일반 안구(정상) 사진

| 데이터셋 | 라이선스 | 판정 | 비고 |
|---|---|---|---|
| [human-faces (ashwingupta3012)](https://www.kaggle.com/datasets/ashwingupta3012/human-faces) | CC0 (Public Domain) | 🟢 안전 | 저작자가 권리를 완전히 포기 — MIT보다도 제약이 적음. 팀원이 이 얼굴 사진에서 눈만 크롭해 정상 안구 데이터로 사용 |
| [eye-detection-dataset (icebearogo)](https://www.kaggle.com/datasets/icebearogo/eye-detection-dataset?select=Dataset) | CC BY-NC 4.0 | 🟡 조건부 | **NC(NonCommercial) = 상업적 이용 금지.** 비상업적 학술 목적(졸업작품)이면 안전하나, 추후 상업화 시 이 출처로 학습된 가중치는 재학습 필요. **phash로 직접 검증함**: 다운로드한 1,979장 중 655장(33.1%)이 `dataset/0_normal`과 해밍거리 ≤6(대부분 완전 일치, dist=0)로 매칭 — 실제 사용 확인됨 |

### 🔴 위험 등급 출처를 그대로 유지하기로 한 이유

`1_cataract`(1,823장) 중 phash로 확인된 위험 등급(Unknown/© Original Authors) 출처 비중만
최소 **338장(약 18.5%)** — #8 nandanp6 306장 + #10 akshayramakrishnan28 32장 (#5·#7은
다운로드 전이라 미포함, 합치면 더 늘어날 수 있음). 전부 제거하는 방안도 검토했으나, 아래
이유로 **그대로 유지하고 투명한 공개로 대응**하기로 결정했습니다:

1. **대체할 데이터가 없습니다.** 공개된 백내장 안구 사진 데이터셋 대다수는 안저(망막)
   사진이라, 이 모델이 학습한 "눈 클로즈업(세극등 사진과 유사한 각도)" 형식과 맞지 않습니다.
   백내장은 소수 클래스(1,823장)라 여기서 18%+를 더 빼면 데이터가 더 부족해집니다.
2. **재배포 리스크가 원천적으로 낮습니다.** 원본 이미지·가중치 파일은 `.gitignore`로
   GitHub에 올라간 적이 없고, 공개 데모(ngrok)도 "확률" 숫자만 돌려줄 뿐 이미지 자체를
   배포하지 않습니다.
3. **비상업적 학술 연구(졸업작품) 목적입니다.** 라이선스 없음 자체가 "절대 금지"를 뜻하는
   건 맞지만, 학술 연구 목적의 비영리 사용은 상업적 배포와는 위험 수준이 다릅니다.

### 완화 조치 (이미 적용됨)

- **`dataset/`(원본 이미지)와 `*.pth`(학습된 가중치)는 처음부터 `.gitignore`** — GitHub 공개
  저장소에 올라간 적이 없습니다. 배포/재배포 리스크는 낮습니다.
- ngrok 공개 데모도 사진을 받아 "확률" 숫자만 돌려줄 뿐, 원본 데이터나 가중치 자체를
  외부에 전달하지 않습니다.
- 남은 리스크는 **출처를 투명하게 공개하지 않는 것**입니다. 보고서/발표 자료에는 아래 문구를
  포함하는 것을 권장합니다:
  > "본 프로젝트는 비상업적 학술 연구 목적의 졸업작품으로, 위 백내장 데이터셋(9개 출처 + 검증
  > 중 추가로 발견된 1건)과 human-faces(CC0), eye-detection-dataset(CC BY-NC 4.0) 데이터셋을
  > 학습에 사용했습니다. 라이선스가 불명확한 출처(#5, #7, #8, #10 — 전체 백내장 데이터의
  > 약 18% 이상)와 NonCommercial 조건의 출처는, 동급의 눈 클로즈업 형식 공개 데이터셋을
  > 대체할 수 없어 비상업적 학술 연구 목적으로만 사용했으며, 원본 이미지는 어떤 형태로도
  > 재배포하지 않습니다. 원본 데이터·학습된 가중치는 GitHub 저장소에 포함되어 있지 않습니다."

> 📝 **남은 작업**: #2(CC BY-SA 4.0)·#6(Apache 2.0) "Cataract Classification Dataset"의
> 정확한 Kaggle 링크는 아직 못 찾았습니다. 앞으로 데이터를 추가할 때는 이미지 단위로 출처를
> 매니페스트(예: CSV)에 기록해두면, 이런 사후 정리가 필요 없어집니다.

---

## 🔍 API 엔드포인트

### 📸 백내장 AI 분석
```bash
POST /api/analyze-eye
Content-Type: multipart/form-data

# 응답
{
  "probability": 72.5,           # 전체 판정 확률(높은 쪽 눈 기준, %)
  "result": "백내장 위험 단계",
  "result_code": "risk",         # normal | borderline | risk | invalid | hold | blurry
  "mode": "face",                # "face" 얼굴 크롭 | "eye" 원본
  "eyes_detected": 2,            # 감지된 눈 개수
  "eye_probs": [72.5, 12.3],     # 각 눈별 확률
  "eyes": [                      # 🆕 눈별 상세 (좌/우)
    {"side": "left",  "probability": 72.5, "code": "risk"},
    {"side": "right", "probability": 12.3, "code": "normal"}
  ],
  "asymmetric": true,            # 🆕 편측(한쪽만 위험) 여부
  "sharpness": 0.0243            # blurry 판정 근거(선명도, 보류일 때만 의미 있음)
}
# invalid = 눈 사진 아님, hold = 플래시 반사, blurry = 흔들림/초점 — 셋 다 판정 대신 재촬영 안내
```

### 💬 Gemma LLM 소견서
```bash
POST /api/get-ai-opinion
Content-Type: application/json

{
  "lang": "ko",
  "cataract_res": "Risque de cataracte",
  "amsler_res": "Distortion détectée",
  "chat_symptoms": ["Suspicion de Glaucome"]
}

# 응답: 스트리밍 텍스트 — 줄바꿈으로 구분된 3줄(검사 안내 / 생활 조언 / 추가 조언·정기 검진)
# 생성이 느릴 때는 하트비트가 섞여 나가고, 오류는 ERROR_MARKER로 구분됩니다.
# 문장 단위 안전 필터를 거치므로 확률·배제·질환 교차 문장은 도착하지 않습니다.
```

### ❓ 맞춤형 문진 질문 생성
```bash
POST /api/generate-next-question
Content-Type: application/json

{
  "lang": "ko",
  "cataract_res": "특이 소견 없음 (정상)",
  "amsler_res": "정상",
  "chat_history": [{"q": "눈이 침침한가요?", "a": "아니오"}]
}

# 응답
{
  "question": "밝은 곳에서 눈이 부시는 느낌이 있나요?",
  "answer_type": "yesno"      # yesno = 네/아니오 버튼 | text = 자유 입력칸
}
```

> 화면에는 '네'/'아니오' 버튼뿐이라 프롬프트로 예/아니오 질문을 요구하지만,
> LLM이 가끔 서술형을 냅니다. 그때는 폐기하지 않고 `answer_type: "text"`로 알려
> 프론트가 자유 입력칸을 띄웁니다.

### 🗨️ 리포트 추가 질문 (챗봇)
```bash
POST /api/chat-with-gemma
Content-Type: application/json

{ "lang": "ko", "user_msg": "관리 방법 알려줘", "context": "백내장 정상 / 암슬러 정상" }

# 응답: 스트리밍 텍스트
```

### 📝 진단 저장
```bash
POST /api/save-diagnosis
Content-Type: application/json

{
  "cataract_result": "...",
  "amsler_result": "...",
  "chat_symptoms": [...],
  "gemma_opinion": "..."
}
```

### 🗺️ 주변 안과 검색
```bash
GET /api/nearby-clinics?lat=37.4979&lng=127.0276

# 응답 (source: "kakao" | "overpass" | "none")
{
  "source": "kakao",
  "clinics": [
    {"name": "지에스안과의원", "lat": 37.4977, "lng": 127.0285,
     "dist": 83.0, "phone": "02-3469-0900",
     "address": "서울 강남구 강남대로 390", "url": "http://place.map.kakao.com/..."}
  ]
}
# 한국 → 카카오, 결과 없으면(해외 등) → Overpass(OSM), 둘 다 실패 → 빈 목록
```

---

## 🛠️ 개발 팁

### 자동 테스트 (pytest)
```bash
pytest        # tests/ 전체 — 수 초 안에 완료
```
- **외부 의존성 없이 돕니다**: GPU 학습·Ollama·PostgreSQL·카카오 API를 전부 모킹해서,
  어느 팀원 PC에서든 클론 직후 바로 실행 가능. 가중치(.pth)·메타데이터가 없는 환경에서는
  해당 테스트만 자동 skip.
- **커버 범위**: 업로드 보안 가드(압축폭탄·가짜 이미지·EXIF 회전), 3단계 판정 경계값(25/50%),
  눈 검증기 fail-closed, 편측(asymmetric) 판정, API 계약(fr/es 110자 회귀 방지 포함),
  LLM 오류 마커·폴백 체인, RAG 검색, **학습↔서빙 전처리 일관성**(모델 메타데이터 교차검증),
  눈 좌/우 결정(MTCNN 랜드마크 순서 무관), 3줄 요약 프롬프트 구조, 정적 자원·번역 키 6개 언어 완비,
  모바일 회귀(알림 예외 격리·카메라 버튼·글자 크기·촬영 예시·시야 체험 위치). 2026-09-02 기준 **162개**.
- 코드를 고치면 커밋 전에 한 번 돌려보세요 — 특히 vision.py·schemas·config 임계값을 만질 때.

### 오프라인 동작 (발표장 대비)
발표장 인터넷이 끊겨도 **AI 검사·문진·리포트·PDF는 그대로 동작**합니다. 외부 CDN에 의존하던
핵심 자원을 `static/vendor/`로 번들했기 때문입니다.

| 자원 | 원본 | 로컬 |
|---|---|---|
| 글꼴 | Pretendard v1.3.8 (SIL OFL) | 가변 폰트 1개 (2.0MB) — 정적 5종 3.8MB를 대체 |
| PDF | html2pdf.js 0.10.1 | 885KB |
| 지도 | Leaflet 1.9.4 + 마커 이미지 | 160KB |

- `index.html`에는 **외부 URL이 하나도 없습니다**(`tests/test_static_assets.py`가 회귀를 막습니다).
- 지도 **타일**은 성격상 번들할 수 없습니다(전 세계 이미지). 오프라인이면 빈 회색 화면 대신
  안내 문구로 대체되고, 나머지 기능은 영향을 받지 않습니다.
- 로컬 파일에는 SRI `integrity`를 쓰지 않습니다 — 같은 출처에서 서빙되므로 불필요합니다.
  (CDN으로 되돌릴 경우 해시를 다시 계산해야 합니다)

### CI (GitHub Actions)
`.github/workflows/tests.yml` — push(master)·PR마다 pytest를 자동 실행합니다. GPU가 없는
러너라 torch는 CPU wheel을 쓰고(테스트는 추론을 전부 모킹), 나머지는 `requirements-base.txt`의
고정 버전을 설치합니다. `.pth`가 없으므로 가중치 관련 2건은 자동 skip됩니다.
Python **3.11·3.13 매트릭스**로 돌려 README가 광고하는 최소 버전(3.11)이 실제로 지켜지는지도
함께 확인합니다 — 3.11 + CPU torch + 고정 버전 조합은 클린 venv에서 68 passed 검증했습니다.

### ⚠️ 프론트 스타일을 고칠 때 (Tailwind 재빌드)
`static/tailwind.css`는 **빌드 산출물이 저장소에 커밋된 것**이고 `node_modules`는 없습니다.
Tailwind는 JIT라 빌드 시점에 쓰이지 않은 유틸리티는 번들에 없는데, **없는 클래스를 써도
브라우저는 에러 없이 조용히 무시**합니다(스타일만 사라짐). 새 유틸리티를 쓰면 반드시:
```bash
npm ci && npm run build:css
```
`tests/test_static_assets.py`가 마크업의 Tailwind 클래스가 빌드본에 있는지 검사하므로,
빼먹으면 CI에서 잡힙니다. (실제로 이 검사로 경계 판정 색상 `bg-amber-100`/`text-amber-600`이
빌드본에 없어 죽어 있던 것을 발견해 고쳤습니다.)

### 눈 검증기 기준 벡터 재생성
```bash
python scripts/build_eye_centroid.py                          # 계산 + 배포본과 비교만 (덮어쓰지 않음)
python scripts/build_eye_centroid.py --non-eye <비-눈 폴더>     # 임계값 근거까지 산출
```
`app/models/eye_centroid.npy`를 만드는 코드가 없어 "왜 임계값이 0.55인가"를 재현할 수 없던 것을
메운 스크립트입니다. **현재 배포본은 이 레시피로 재현되지 않습니다**(코사인 0.976, 부분집합·표본크기
가설 모두 기각 — 자세한 측정치는 스크립트 docstring 참고). 배포본은 실측상 잘 동작하므로
(데이터셋 눈 사진 중 0.09%만 거부, 밝은 홍채는 전부 통과) 그대로 두었고, 이 스크립트는
앞으로의 재현성을 위한 것입니다. 교체하려면 `--overwrite`와 함께 `eye_sim_threshold`도
반드시 다시 구해야 합니다.

### VS Code 프리뷰
`.claude/`는 개인 환경 설정이라 `.gitignore` 대상 — **클론하면 이 파일이 없습니다.**
직접 만드세요(`runtimeExecutable`의 파이썬 경로는 본인 가상환경에 맞게 수정):
```jsonc
// .claude/launch.json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "eye-catch-api",
      "runtimeExecutable": "C:\\eye_catch\\.venv\\Scripts\\python.exe",
      "runtimeArgs": ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0",
                      "--port", "8001", "--reload", "--reload-dir", "app", "--reload-dir", "static"],
      "port": 8001
    }
  ]
}
```
만든 뒤 F5 또는 Run → "eye-catch-api" 선택 → 포트 8001에서 프리뷰 서버 실행.

### 수동 스모크 테스트 (사진 1장)
```bash
python scripts/smoke_eye_detect.py <사진경로>   # 얼굴사진 → mode=face / 눈 클로즈업 → mode=eye
```
가중치·MTCNN이 실제로 붙어 있는지 눈으로 확인하는 CLI입니다. 파일명이 `test_`로 시작하지
않는 이유는 pytest가 수집하면 import 시점의 `SystemExit`로 스위트 전체가 죽기 때문입니다.

### 프론트엔드 수정 후 캐시 무효화
- 각 수정마다 `static/index.html`의 `?v=` 버전을 올립니다
- 예: `?v=20260616d` → `?v=20260616e`
- 모바일 폰이 새 파일을 받게 됩니다 (`no-cache` 헤더 + 버전 쿼시 활용)
- 정적 파일은 요청마다 디스크에서 읽으므로 서버 재시작이 필요 없지만, `app/core/config.py` 같은
  **설정 변경은 `--reload`가 놓치는 경우가 있어** 서버를 직접 재시작하는 편이 안전합니다(2026-09-02 실측).

### 언어 저장 (localStorage)
- `changeLanguage(lang)` 호출 시 자동으로 `localStorage.setItem('ec_lang', lang)` 
- 새로고침/재방문 후에도 선택 언어 유지

### PDF 생성 레시피
- `buildReportPdf()` → HTML 조립 후 html2pdf.js로 캡처
- **핵심:** printDiv를 `position:fixed;top:0;left:0`로 **body에 실제 부착** (detached 상태로 캡처하면 브라우저 내 좌표 계산 오류 발생)
- AI 3줄 요약은 줄마다 `page-break-inside:avoid` 문단으로 분할 → PDF에서도 3줄로 보이고 페이지 경계가 깔끔함

---

## 📱 모바일·접근성

2026-09-02 팀 실기기 테스트(갤럭시 S25 Ultra) 피드백으로 넣은 것들입니다.

### 글자 크기 (A− / A+)
- 3단계(root 16 → 18 → 20px). Tailwind 텍스트·여백이 rem 기반이라 화면 전체가 같은 비율로 커지고,
  px 임의값 클래스(`text-[11px]` 등)는 `style.css`에서 rem으로 재정의해 함께 커집니다.
- 선택은 `localStorage`(`ec_font`)에 저장되고 `<head>`의 인라인 스크립트가 스타일보다 먼저 복원해 첫 화면이
  깜빡이지 않습니다. 헤더(로고·버튼·언어 선택)는 도구라서 px로 고정합니다.
- 3줄 요약 본문은 `.9rem`(14.4 → 18px)으로 리포트에서 가장 크게 보입니다.

### 카메라로 바로 찍기
- `<input type="file" accept="image/*" capture>` — 값 없는 `capture`는 기기 기본 카메라이며 카메라 앱에서 전·후면을 바꿀 수 있습니다.
- 터치 기기 판별은 CSS `(hover: none)`이 아니라 JS `navigator.maxTouchPoints`입니다. S펜 갤럭시는 호버를
  지원한다고 보고해 미디어쿼리로는 버튼이 숨겨졌습니다(실기기 확인).

### 촬영 예시 · 시야 체험 사진
- `static/assets/examples/` — CC0 얼굴 사진 1장(Wikimedia Commons, William Stitt)을 가공한 좋은 예/흔들린 예.
- `static/assets/vision-scene.jpg` — CC0 거리 사진(Wikimedia Commons, Terry Kearney). 효과는 CSS 필터·덮개 층으로 실시간 적용.
- 둘 다 CC0라 표기 의무는 없지만 질환 사진과 같은 기준으로 `ATTRIBUTION*.md`와 화면에 출처를 남깁니다.

### 화면 폭별 점검 (에뮬레이션, 글자 크기 기본/최대)
| 기기 | 폭 | 결과 |
|---|---|---|
| 갤럭시 Z 폴드 커버 화면 | 320px | 헤더 축소 규칙 추가 후 정상 |
| 갤럭시 Z 플립·일반 안드로이드 | 360px | 정상 |
| 아이폰 SE / 13 mini | 375px | 정상 |
| 갤럭시 Z 폴드 펼침 | 673~800px | 하단 탭 메뉴로 통일 후 정상 |
| 태블릿·데스크톱 | 1024px 이상 | 상단 메뉴 한 줄 유지 |

실기기와 다를 수 있는 것: 폴드를 검사 중간에 접었다 펴면 시력검사 화면 보정(px/mm)은 다시 맞추는 편이 안전합니다.

---

## 🐛 알려진 이슈 & 해결책

| 이슈 | 원인 | 해결 |
|------|------|------|
| 백내장 분석이 멈춤 | AI 모델 가중치 미로드 | `.env`의 `MODEL_PATH`가 실제 `.pth` 파일을 가리키는지, 서버 로그에 "AI 모델 로드 완료" 가 찍히는지 확인 |
| LLM 소견서 안 나옴 | Ollama 서버 미실행 | `ollama serve` 실행 |
| 소견서가 중간에 끊김 | 생성 지연 중 모바일/ngrok 연결 끊김 | 하트비트 스트리밍(`stream_with_keepalive`)으로 연결 유지 |
| 소견서 첫 글자 느림 | Ollama 콜드스타트(모델 로딩) | `keep_alive:-1` + 서버 시작 시 워밍업으로 VRAM 상주 |
| LLM 응답 너무 느림 | 긴 RAG 프롬프트 prefill (모델 크기 무관) | 프롬프트 단축 또는 그대로 수용(하트비트가 끊김 방지). GPU에 맞는 QAT 모델 권장 |
| 안과 검색 403 `disabled OPEN_MAP_AND_LOCAL` | 카카오 앱에서 카카오맵 서비스 비활성화 | developers.kakao.com → 제품 설정 → 카카오맵 **활성화** |
| 폰에서 버튼 삐져나감 | flex 입력칸 `min-width:auto` 버그 | `min-w-0` 클래스 추가 |
| 일반 모드만 안 뜸/깨짐 | 옛 `index.html` 캐시 잔존 | 사이트 데이터 1회 삭제 → 이후 `no-cache` 헤더로 자동 갱신 |
| 영어로 깨져 보임 | 캐시된 구 버전 | 정적 파일 `?v=` 버전 쿼리 + 시크릿창/하드리프레시 |
| PDF 2페이지 공백 | 소견서 한 줄이 페이지 경계에서 잘림 | `toAvoidBreakParagraphs()` 로 문단 분할 |
| 소견서가 "연결이 끊어졌습니다"로 실패 | **개발 중 `--reload` 서버 재시작** / ngrok 끊김 / Ollama 콜드스타트 | 소견서 자리의 **[소견서 다시 생성]** 버튼으로 그 부분만 재시도 (검사 결과는 유지). 폰 시연 중에는 `--reload` 없이 띄우세요 |
| **안드로이드에서 소견이 다 나온 뒤** "연결이 끊어졌습니다"로 바뀜 | 안드로이드 크롬은 페이지의 `new Notification()`에 예외를 던지는데, 완료 알림이 스트림 오류와 같은 try 안에 있어 완성된 소견을 덮어썼음 | **해결됨(2026-09-02)** — 알림·저장 동의는 소견 수신 밖에서 각각 예외를 삼킴(`notifyOpinionDone`) |
| "카메라로 바로 찍기" 버튼이 안 보임 | S펜이 있는 갤럭시(Ultra·Note)는 크롬이 `hover: hover`로 보고해 CSS 미디어쿼리 판별이 빗나감 | **해결됨** — `navigator.maxTouchPoints`로 터치 기기를 판별(`body.touch-device`) |
| "사진이 흔들렸어요" 안내만 반복 | 눈 부위 선명도가 `BLUR_MIN_SHARPNESS`(0.030) 미만 | 폰을 고정하고 재촬영. 정상 사진도 걸리면 `vision.py`의 기준값을 낮추되, 백내장 눈은 원래 뿌옇게 보여 오거부가 늘어남 |
| 글자 크기 최대에서 상단 이름이 잘림 | 헤더 요소가 root 글자 크기를 따라 커짐 | **해결됨** — 헤더의 로고·버튼·언어 선택은 px 고정, 340px 이하는 한 단계 더 축소 |
| 폴드 펼침(730~1000px)에서 상단 메뉴 글자가 세로로 쪼개짐 | 768px부터 켜지는 데스크톱 메뉴 5개가 한 줄에 안 들어감 | **해결됨** — 1024px 미만은 폰과 같은 하단 탭 메뉴 사용 |
| 정상 눈인데 "백내장 위험"으로 나옴 | 플래시 반사를 혼탁으로 오독 | 플래시를 끄고 재촬영. 반사가 심하면 앱이 자동으로 판독 보류합니다 → [플래시 반사 대응](#-플래시-반사-대응) |
| 안저(망막) 사진을 올렸는데 판정이 나옴 | OOD 게이트가 안저사진을 '눈'으로 통과시킴 | **알려진 미해결 이슈.** 이 모델은 외안부 사진 전용입니다 |
| 눈별(좌/우) 결과가 안 보임 | MTCNN이 눈을 2개 못 찾음(눈 클로즈업이거나 조명·각도 문제) | 정상 동작입니다. 얼굴 사진 + 눈 2개 검출일 때만 표시됩니다 |

---

## 📚 데이터셋 구조

```
dataset/
├── 0_normal/          # 정상 안구 (15,194장 — v5 밝은 홍채 201장 포함)
│   ├── eye_001.jpg
│   ├── eye_002.jpg
│   └── ...
└── 1_cataract/        # 백내장 (1,823장)
    ├── cataract_001.jpg
    ├── cataract_002.jpg
    └── ...
```

**주의:** `dataset/` 폴더는 `.gitignore`에 포함되어 있어 저장소에 올라가지 않습니다.  
데이터셋은 팀원과 별도로 공유하거나 [`Git LFS`](https://git-lfs.github.com/)를 사용하세요.

---

## 📦 배포

### 클라우드 배포 (예: Heroku, Render)
1. `requirements.txt`를 프로젝트에 포함 ✅
2. Procfile 생성:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
3. 배포 플랫폼의 가이드 따르기

### Docker 배포
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📄 라이선스

MIT License — 자유롭게 사용, 수정, 배포 가능합니다.

---

## 👥 기여 & 연락

- **Issues & PRs 환영합니다!**
- 버그 신고: [GitHub Issues](https://github.com/KangSky77/Eye-Catch-Project/issues)
- 이메일: khn10520@gmail.com

---

## 🙏 감사의 말

- **PyTorch & torchvision** — 딥러닝 프레임워크
- **FastAPI** — 고성능 웹 API
- **Ollama & Gemma** — 로컬 LLM
- **html2pdf.js** — PDF 생성
- **Tailwind CSS** — 스타일링
- **MTCNN (facenet-pytorch)** — 얼굴 감지

---

**마지막 업데이트: 2026-06-23**

🌟 유용하셨다면 **Star** ⭐ 부탁드립니다!
