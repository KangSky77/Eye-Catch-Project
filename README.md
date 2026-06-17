# 👁️ Eye-Catch — 안구질환 AI 스크리닝 앱

> **AI 사진 분석 + LLM 맞춤형 소견서**로 안구질환을 조기 발견하세요.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue" />
  <img src="https://img.shields.io/badge/FastAPI-Latest-green" />
  <img src="https://img.shields.io/badge/PyTorch-2.1+-red" />
  <img src="https://img.shields.io/badge/Languages-6-orange" />
</p>

---

## 🎯 주요 기능

### 1️⃣ **백내장 AI 자동 진단**
- **전이학습 ResNet18** 모델 (ImageNet 사전학습)
- 테스트셋 정확도: **99.9%** | 민감도: **100%** (FN=0)
- 정상 14,993장 + 백내장 1,823장으로 학습
- 임계값 50% (운영 최적화)

### 2️⃣ **멀티모달 안구질환 검사**
- 🖼️ **백내장 AI 분석** — 이미지 기반
- 📊 **황반변성 자가진단** — Amsler Grid 테스트
- 📋 **문진 기반 스크리닝** — 녹내장·당뇨망막병증 의심 질문

### 3️⃣ **Gemma LLM 맞춤형 소견서**
- 환자의 검사 결과를 분석해 **개인화된 의료 조언** 생성
- 수치 직접 인용 + 검사 안내 + 생활팁 포함
- 로컬 Ollama 서버로 개인정보 보호

### 4️⃣ **6개국어 지원** 🌍
- 🇰🇷 한국어 | 🇺🇸 English | 🇪🇸 Español
- 🇫🇷 Français | 🇯🇵 日本語 | 🇨🇳 中文
- 브라우저 언어 자동 감지 + 사용자 선택 저장

### 5️⃣ **고품질 PDF 리포트**
- 4섹션 진단 리포트 (AI·황반·문진·소견서)
- 다국어 자동 번역
- 페이지 경계 깔끔하게 분할
- 병원 근처 안과 찾기 링크 포함

### 6️⃣ **외부 공유** (ngrok)
```bash
ngrok http 8000
# 공개 HTTPS URL 자동 생성 → 모바일·원격 공유 가능
```

---

## 🏗️ 아키텍처

```
Eye-Catch (C:\eye_catch_claude)
│
├── 🔙 백엔드 (FastAPI, Python)
│   ├── app/
│   │   ├── main.py              # 앱 진입점
│   │   ├── core/config.py       # 환경 설정 (.env 연동)
│   │   ├── api/routes.py        # REST API
│   │   ├── models/
│   │   │   └── cataract_model.py  # ResNet18 신경망
│   │   └── services/
│   │       ├── vision.py        # AI 추론 + 임계값 로직
│   │       ├── eye_detector.py  # MTCNN 얼굴→눈 크롭
│   │       ├── llm.py           # Gemma 프롬프트
│   │       └── database.py      # 진단 기록 저장
│   ├── train_ai.py              # 모델 학습 스크립트
│   ├── eval_v2.py               # 모델 평가 (v2 검증용)
│   ├── requirements.txt          # 의존성 패키지
│   └── dataset/                 # 이미지 데이터셋
│       ├── 0_normal/            # 정상 안구 14,993장
│       └── 1_cataract/          # 백내장 1,823장
│
├── 🎨 프론트엔드 (Vanilla JS + Tailwind CSS)
│   ├── static/
│   │   ├── index.html           # SPA 마크업
│   │   ├── app.js               # 메인 로직 (i18n, 상태관리)
│   │   ├── data.js              # 6개국어 번역 데이터
│   │   └── style.css            # 커스텀 스타일
│   └── .claude/launch.json      # VS Code 프리뷰 설정
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

# 의존성 설치
pip install -r requirements.txt

# 추가 패키지 (선택)
pip install --no-deps facenet-pytorch  # 얼굴→눈 크롭용
```

### 3️⃣ 환경변수 설정
`.env` 파일 생성:
```ini
APP_NAME=Eye-Catch API
DEBUG=true
MODEL_PATH=cataract_resnet18_v2.pth

# 데이터베이스
DB_HOST=localhost
DB_NAME=eyecatch_db
DB_USER=postgres
DB_PASSWORD=your_password

# LLM (Ollama)
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=gemma4:e4b
OLLAMA_TIMEOUT_SECONDS=120
```

### 4️⃣ AI 모델 학습 (또는 사전학습 가중치 다운로드)
```bash
# 모델 학습 (데이터셋 필요)
python train_ai.py

# 또는 사전학습 가중치 사용
# → cataract_resnet18_v2.pth 를 프로젝트 루트에 배치
```

### 5️⃣ Ollama 서버 실행
```bash
# 별도 터미널에서
ollama serve

# Gemma 모델 다운로드 (최초 1회)
ollama pull gemma4:e4b
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

### ResNet18 v2 (16,816장 학습)

| 지표 | 값 |
|------|-----|
| **정확도 (Accuracy)** | 99.9% |
| **민감도 (Sensitivity)** | 100% (FN=0) |
| **특이도 (Specificity)** | 99.9% |
| **AUC-ROC** | 1.000 |

**테스트셋:** 2,521장 (정상 2,248 + 백내장 273)  
**혼동행렬 (임계값 50%):** TN=2245, FP=3, FN=0, TP=273

---

## 🔍 API 엔드포인트

### 📸 백내장 AI 분석
```bash
POST /api/predict-cataract
Content-Type: multipart/form-data

# 응답
{
  "probability": 72.5,           # 백내장 확률 (%)
  "result": "백내장 위험 단계",
  "result_code": "risk",         # "normal" | "risk"
  "mode": "face",                # "face" 얼굴 크롭 | "eye" 원본
  "eyes_detected": 2,            # 감지된 눈 개수
  "eye_probs": [72.5, 65.3]      # 각 눈별 확률
}
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

# 응답: 스트리밍 텍스트 (Server-Sent Events)
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

---

## 🛠️ 개발 팁

### VS Code 프리뷰
```bash
# .claude/launch.json이 이미 설정됨
# F5 또는 Run → "eye-catch-api" 선택
# → 포트 8001에서 프리뷰 서버 실행
```

### 프론트엔드 수정 후 캐시 무효화
- 각 수정마다 `static/index.html`의 `?v=` 버전을 올립니다
- 예: `?v=20260616d` → `?v=20260616e`
- 모바일 폰이 새 파일을 받게 됩니다 (`no-cache` 헤더 + 버전 쿼시 활용)

### 언어 저장 (localStorage)
- `changeLanguage(lang)` 호출 시 자동으로 `localStorage.setItem('ec_lang', lang)` 
- 새로고침/재방문 후에도 선택 언어 유지

### PDF 생성 레시피
- `buildReportPdf()` → HTML 조립 후 html2pdf.js로 캡처
- **핵심:** printDiv를 `position:fixed;top:0;left:0`로 **body에 실제 부착** (detached 상태로 캡처하면 브라우저 내 좌표 계산 오류 발생)
- 소견서(긴 텍스트)는 `page-break-inside:avoid` 문단으로 분할 → 페이지 경계가 깔끔함

---

## 🐛 알려진 이슈 & 해결책

| 이슈 | 원인 | 해결 |
|------|------|------|
| 백내장 분석이 멈춤 | AI 모델 가중치 미로드 | `eval_v2.py` 실행 후 검증 |
| LLM 소견서 안 나옴 | Ollama 서버 미실행 | `ollama serve` 실행 |
| 폰에서 버튼 삐져나감 | flex 입력칸 `min-width:auto` 버그 | `min-w-0` 클래스 추가 |
| 영어로 깨져 보임 | 캐시된 구 버전 | 시크릿창 또는 `Ctrl+Shift+R` 하드리프레시 |
| PDF 2페이지 공백 | 소견서 한 줄이 페이지 경계에서 잘림 | `toAvoidBreakParagraphs()` 로 문단 분할 |

---

## 📚 데이터셋 구조

```
dataset/
├── 0_normal/          # 정상 안구 (14,993장)
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

**마지막 업데이트: 2026-06-16**

🌟 유용하셨다면 **Star** ⭐ 부탁드립니다!
