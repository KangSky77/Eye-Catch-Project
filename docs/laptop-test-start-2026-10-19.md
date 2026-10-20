# 노트북 시험 서버 다시 실행하기 — 2026-10-19

확인한 장치: DESKTOP-98MM046 / RTX 3060 Laptop 6GB / Tailscale 100.68.198.29.
학교 메인 서버: 100.105.157.88. 장치 재등록으로 IP가 바뀌면 먼저 다시 확인한다.

## 첫 번째 창: 생성형 AI

Tailscale을 연결하고 트레이의 Ollama를 종료한 다음 관리자 PowerShell에서 실행한다. 이미 시험 Ollama가 실행 중이라면 중복 실행하지 않는다.

```powershell
New-NetFirewallRule -DisplayName 'EyeCatch-laptop-test' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8003,11434 -LocalAddress '100.68.198.29' -RemoteAddress '100.105.157.88' -Profile Any
$env:OLLAMA_HOST='100.68.198.29:11434'
$env:OLLAMA_NO_CLOUD='1'
$env:OLLAMA_NUM_PARALLEL='2'
ollama serve
```

방화벽 규칙은 첫 설정 때 한 번이면 된다. 같은 규칙이 이미 있으면 첫 줄을 제외하고 실행한다. 이 설정은 VPN 주소와 학교 서버 IP로 범위를 제한한다. 기존에 더 넓은 허용 규칙이 있으면 실제 접근 범위는 별도 확인한다.

## 두 번째 창: 사진 AI

새 PowerShell 창에서 실행한다. 프로젝트가 다른 위치에 있으면 첫 줄을 실제 프로젝트 경로로 바꾼다.

```powershell
Set-Location -LiteralPath 'C:\eye_catch'
$env:OLLAMA_URL='http://100.68.198.29:11434/api/generate'
$env:OLLAMA_URLS=''
$env:PHOTO_WORKER_URLS=''
$env:WAITING_ROOM_ENABLED='false'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 100.68.198.29 --port 8003 --workers 1
```

worker URL 목록을 비워 노트북 사진 서버가 다시 다른 PC에 요청을 분산하는 중첩 구성을 피한다. 두 창은 실행 상태로 두고 전원·인터넷·Tailscale 연결을 유지한다. 운영 서버를 변경하거나 입장 정원을 자동으로 늘리는 명령은 아니다.

2026-10-19 확인: Ollama API 200, 짧은 실제 생성 성공, 사진 준비 상태 200, 합성 2000×1500 사진의 실제 분석 성공. 두 서비스 모두 살아 있어야 노트북을 포함한 전체 흐름 시험을 할 수 있다.
