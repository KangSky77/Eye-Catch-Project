# 로컬 도구

외부 공유에 사용하는 `ngrok.exe` 같은 실행파일은 이 폴더에 둘 수 있습니다.
실행파일은 Git에 포함되지 않으며, 팀원은 각자 공식 배포본을 설치해야 합니다.

무료 대안(설치 후 명령 하나로 공개 HTTPS 주소가 나옵니다):

- `cloudflared tunnel --url http://localhost:8000` — 계정 불필요, 중간 경고 페이지 없음
  (`winget install --id Cloudflare.cloudflared`)
- `tailscale funnel 8000` — 주소가 매번 바뀌지 않아 링크를 미리 공유할 때 좋습니다
  (`winget install tailscale.tailscale`)

ngrok 무료 플랜은 계정당 동시 세션이 1개라, 두 대에서 동시에 공유하려면
한쪽은 위 대안을 쓰세요. 포트는 실제 uvicorn 실행 포트에 맞춰야 합니다(F5 프리뷰는 8001).
