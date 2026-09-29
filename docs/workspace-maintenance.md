# 폴더 관리

실행에 필요한 코드는 `app/`과 `static/`, 회귀 테스트는 `tests/`, 학습·평가·정리 도구는 `scripts/`에 둡니다.

- `app/services/llm.py`: 모델 호출, 스트리밍, 오류 처리
- `app/services/llm_prompts.py`: 프롬프트 작성
- `app/services/question_validation.py`: 질문 형식·언어 검증
- `static/app-report.js`: 리포트 화면과 AI 소견
- `static/app-report-chat.js`: 추가 질문과 검사 결과 설명
- `static/app-report-pdf.js`: PDF 생성과 다운로드

현재 사용하지 않는 시력·대비감도 검사 구현과 관련 번역·CSS는 제거했습니다. 암슬러 검사와 질환 시야 체험은 계속 제공합니다.

## 보관할 파일

현재 모델 `cataract_efficientnet_b0_v4.pth`와 메타데이터는 루트에 둡니다. 이전 모델 가중치와 학습 로그는 `model_archive/`에 두고 비교·복구에 사용합니다. `dataset*` 폴더와 `data/`의 출처·분할·검수 기록은 재학습에 필요하므로 유지합니다.

`.env`, `.venv/`, `node_modules/`, `ngrok.exe` 및 개인 도구 설정은 실행·개발 환경입니다. 파일이 Git에 없다는 이유로 삭제하지 않습니다.

## 다시 생성할 수 있는 캐시 정리

프로젝트 루트의 PowerShell에서 실행합니다. 테스트와 학습이 끝난 뒤 사용하세요.

```powershell
npm run clean:preview
npm run clean
```

미리보기는 아무 파일도 지우지 않습니다. 실제 정리도 Python 캐시, pytest 임시 폴더, 검사 도구 캐시와 커버리지 산출물만 지웁니다. 루트와 경로 경계를 확인하며 연결 경로(junction/symlink)가 있는 대상은 거부합니다. 의존성·데이터·모델·설정·다른 도구의 작업 폴더는 지우지 않습니다.

캐시는 다음 실행·테스트 때 다시 생기며 `.gitignore`로 제외됩니다. 삭제한 시력검사 구현은 Git 이력에, 정리 직전 작업 파일은 로컬 임시 폴더 `EyeCatchCleanup20260929/baseline/`에 보관했습니다.
