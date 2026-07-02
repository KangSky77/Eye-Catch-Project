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

### 1️⃣ **백내장 AI 자동 진단 (눈별 판정)**
- **전이학습 EfficientNet-B0** 모델 (ImageNet 사전학습) — v4 백본 비교에서 ResNet18을 이겨 채택
- v4: 그룹 단위 분할(근접중복 누수 차단) 기준 테스트셋 민감도 **98.2%** | 특이도 **99.9%** | AUC **0.9996** (자세한 내용은 "모델 성능" 섹션 참고)
- 원본 16,816장 중 절반(8,639장)이 근접중복 그룹에 속했습니다. 이미지를 삭제하지 않고, 같은 그룹이 서로 다른 split에 갈라지지 않도록 분할합니다.
- 추론 시 **좌우반전 TTA**(원본+거울상 평균) 적용 — 운영과 평가가 같은 방식
- **3단계 판정**: 위험(≥50%) / **경계(25~50%** — 재촬영·검진 권장) / 정상(<25%).
  경계 구간은 "정상으로 안심시키기엔 애매한" 확률대를 안내로 돌려, 문턱 바로 아래의 놓침(FN)을 줄입니다.
- 🆕 **좌/우 눈 개별 분석** — 얼굴 사진에서 양쪽 눈을 따로 판정하고,
  한쪽만 위험하면 **"편측 의심" 배지** 표시 (편측 백내장 대응)
- MTCNN 얼굴→눈 크롭 (얼굴 사진/눈 클로즈업 모두 지원)

### 2️⃣ **멀티모달 안구질환 검사**
- 🖼️ **백내장 AI 분석** — 이미지 기반
- 📊 **황반변성 자가진단** — Amsler Grid 테스트
- 📋 **문진 기반 스크리닝** — 녹내장·당뇨망막병증 의심 질문

### 3️⃣ **Gemma LLM 맞춤형 소견서 (RAG 그라운딩)**
- 환자의 검사 결과를 분석해 **개인화된 의료 조언** 생성
- 🆕 **RAG (Retrieval-Augmented Generation)** — 안과 4대 질환 참고지식
  베이스에서 환자 결과에 맞는 내용을 검색해 프롬프트에 주입 →
  모델이 **검증된 의학 정보에 근거**해 답변 (환각 위험↓, 전문성↑)
- 수치 직접 인용 + 검사 안내(세극등·OCT 등) + 생활팁 포함
- 🆕 **하트비트 스트리밍** — 생성 지연 시에도 연결을 유지해 모바일·ngrok
  환경에서 답변이 중간에 끊기지 않음
- 로컬 Ollama 서버로 개인정보 보호 (모델: `gemma4:e4b-it-qat`)

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
- 4섹션 진단 리포트 (AI·황반·문진·소견서)
- 다국어 자동 번역
- 페이지 경계 깔끔하게 분할

### 7️⃣ **외부 공유** (ngrok)
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
│   │   │   └── cataract_model.py  # 백본 빌더 (resnet18 | efficientnet_b0)
│   │   └── services/
│   │       ├── vision.py        # AI 추론 + 임계값 + 눈별/편측 판정
│   │       ├── eye_detector.py  # MTCNN 얼굴→눈 크롭 (좌/우)
│   │       ├── llm.py           # Gemma 프롬프트 + RAG + 하트비트 스트리밍
│   │       ├── knowledge.py     # 🆕 RAG 안과 참고지식 베이스 + 검색
│   │       ├── clinics.py       # 🆕 주변 안과 검색 (카카오/Overpass)
│   │       └── database.py      # 진단 기록 저장
│   ├── dedup_dataset.py         # 근접중복 탐지 (phash, 정확한 O(n²)) → dataset_group_map.json
│   ├── train_ai_v3.py           # 그룹 분할 + 라벨충돌 제외 + 불균형 보정 학습 스크립트
│   ├── train_ai_v4.py           # 🆕 백본 비교 학습 (--backbone resnet18|efficientnet_b0)
│   ├── validate_real_photos.py  # 🆕 실사진(폰 촬영)으로 배포 파이프라인 검증 (시연 전 필수)
│   ├── requirements.txt          # 의존성 패키지
│   └── dataset/                 # 이미지 데이터셋 (원본 16,816장, 8,177개 근접중복 그룹)
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

# LLM (Ollama) — GPU(8GB급)에 잘 맞는 QAT 모델 권장
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=gemma4:e4b-it-qat
OLLAMA_TIMEOUT_SECONDS=120

# 주변 안과 검색 (선택) — 카카오 로컬 REST API 키
# developers.kakao.com → 내 앱 → REST API 키, 그리고 [제품 설정 → 카카오맵] 활성화 필수
# 비워두면 해외는 OSM Overpass, 그것도 없으면 외부 검색 링크로 폴백
KAKAO_REST_KEY=
```

### 4️⃣ AI 모델 학습 (또는 사전학습 가중치 다운로드)
```bash
python dedup_dataset.py                            # 1회 — dataset_group_map.json 생성
python train_ai_v4.py --backbone efficientnet_b0   # → cataract_efficientnet_b0_v4.pth (현재 배포 모델)
python train_ai_v4.py --backbone resnet18          # (선택) 백본 비교용

# 또는 사전학습 가중치 사용 → 프로젝트 루트에 배치 후 .env의 MODEL_PATH/MODEL_BACKBONE 수정
# 참고: RTX 3060 노트북 기준 efficientnet_b0 약 90분, resnet18 약 15분
```

### 5️⃣ Ollama 서버 실행
```bash
# 별도 터미널에서
ollama serve

# Gemma 모델 다운로드 (최초 1회)
ollama pull gemma4:e4b-it-qat
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

### EfficientNet-B0 v4 (백본 비교 — 현재 배포 모델)

라벨 수정으로 파일 2장이 클래스를 옮기면서 v3 학습 당시의 train/val/test 분할이
같은 시드로도 재현 불가능해졌습니다(클래스별 그룹 목록이 달라져 셔플 결과가 바뀜).
이를 해소하기 위해 `dataset_group_map.json`을 재생성하고 **동일 조건에서 두 백본을
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
  ResNet18 v4에선 오히려 해로움(FN 7→10), 채택된 EfficientNet-B0에선 무득실.
  실사진의 거울 대칭 변화에 대한 보험으로 유지하되, **백본을 바꾸면 반드시 재측정**해야 합니다.
- **3단계 판정(경계 구간 25~50%)**: 확률 분포가 양극단에 몰려 있어(20~50% 구간이 test
  2,540장 중 4장뿐) 경계 안내 비용이 거의 없는데, test에서 놓친 백내장 5건 중 2건(39.7%)이
  이 구간에 있어 "경계 — 재촬영·검진 권장"으로 구제됩니다. 정상이 경계로 분류되는 부담은
  val 1/2,305 · test 1/2,268 (0.04%).
- **알려진 약점**: test 오탐 3건은 모두 **밝은 색(청록·파랑·녹색) 홍채의 정상 눈**이었습니다
  (98.5~99.9% 확신으로 오판). 데이터셋이 어두운 홍채 위주라 밝은 홍채의 뿌연 느낌을 수정체
  혼탁으로 착각하는 것으로 보이며, 개선하려면 밝은 홍채 정상 눈 데이터 보강이 필요합니다.
- **시연 전 실사진 점검**: 위 수치는 데이터셋 내부 수치입니다. 실제 폰 사진은 도메인 갭으로
  성능이 낮아질 수 있으니, `python validate_real_photos.py <사진폴더>`로 배포 파이프라인
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
배정합니다(`dataset_group_map.json`). 정상/백내장 두 클래스에 걸친 라벨 충돌 그룹(같은 사진이
양쪽에 라벨링된 경우)은 **학습/검증/테스트 전부에서 제외**하고 `label_conflicts.json`에
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
python dedup_dataset.py                            # 1회 — dataset_group_map.json 생성
python train_ai_v4.py --backbone efficientnet_b0   # 현재 배포 모델 재학습
```
>
> 또한 비-눈 이미지 차단(OOD 검증, `eye_validator.py`)은 ImageNet 사전학습 ResNet18 가중치를 런타임에 받아옵니다. **서버를 처음 띄우는 환경(신규 배포·팀원 PC 등)에서는 최초 1회 인터넷 연결이 필요**하며, 실패하면 눈 클로즈업 분석이 503으로 막힙니다(의도된 fail-closed 동작).

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

`1_cataract`(1,821장) 중 phash로 확인된 위험 등급(Unknown/© Original Authors) 출처 비중만
최소 **338장(약 18.6%)** — #8 nandanp6 306장 + #10 akshayramakrishnan28 32장 (#5·#7은
다운로드 전이라 미포함, 합치면 더 늘어날 수 있음). 전부 제거하는 방안도 검토했으나, 아래
이유로 **그대로 유지하고 투명한 공개로 대응**하기로 결정했습니다:

1. **대체할 데이터가 없습니다.** 공개된 백내장 안구 사진 데이터셋 대다수는 안저(망막)
   사진이라, 이 모델이 학습한 "눈 클로즈업(세극등 사진과 유사한 각도)" 형식과 맞지 않습니다.
   백내장은 소수 클래스(1,821장)라 여기서 18%+를 더 빼면 데이터가 더 부족해집니다.
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
  "result_code": "risk",         # "normal" | "risk"
  "mode": "face",                # "face" 얼굴 크롭 | "eye" 원본
  "eyes_detected": 2,            # 감지된 눈 개수
  "eye_probs": [72.5, 12.3],     # 각 눈별 확률
  "eyes": [                      # 🆕 눈별 상세 (좌/우)
    {"side": "left",  "probability": 72.5, "code": "risk"},
    {"side": "right", "probability": 12.3, "code": "normal"}
  ],
  "asymmetric": true             # 🆕 편측(한쪽만 위험) 여부
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

**마지막 업데이트: 2026-06-23**

🌟 유용하셨다면 **Star** ⭐ 부탁드립니다!
