# 팀원 PC를 Eye-Catch AI 처리에 연결하기

이 안내는 팀원 Windows PC의 Gemma 처리 서버를 준비하는 단계다. 연결만으로 사이트가 자동으로 이 PC를 사용하는 것은 아니다. 메인 서버의 분산 처리 대상에 등록하고 연결·모델·부하 시험을 해야 한다.

## 1-A. 팀원 계정 없이 등록하기: Auth key

팀원은 별도 계정을 만들지 않고 Tailscale 설치와 장치 등록 명령만 실행할 수 있다. 메인 서버 소유자의 기존 계정이 PC 등록과 접근 정책을 관리한다.

1. 소유자는 접근 정책에 `tag:eye-worker` 태그를 정의하고, 이 태그를 붙일 수 있는 관리자와 필요한 통신 권한을 설정한다. 태그가 붙은 PC에 소유자 개인 기기의 권한이 그대로 적용되지 않도록 서버용 태그를 사용한다.
2. 생성형 AI 전용 PC는 학교 서버 `100.105.157.88`에서 해당 태그의 `11434/TCP`로 요청을 받을 수 있게 한다. 사진 API도 설치하는 PC에는 `8003/TCP`를 추가한다. 기존 전체 허용 규칙이 있으면 태그를 추가하는 것만으로 접근이 좁아지지는 않으므로 실제 정책을 함께 확인한다.
3. 소유자는 https://login.tailscale.com/admin/settings/keys 에서 `Generate auth key`를 선택한다.
4. PC마다 별도 키를 발급한다. `Reusable` 끄기, `Ephemeral` 끄기, 등록 키 만료는 예를 들어 1일, 태그는 `tag:eye-worker`로 지정한다. 장치 승인이 켜져 있으면 등록 후 승인하거나 의도한 장치용 사전 승인 설정을 선택한다.
5. 각 키는 해당 팀원에게 개인적으로 전달한다. 이 안내 파일, Git, 공개 게시물, 이 채팅의 검증 자료에 실제 키를 넣지 않는다.
6. 팀원은 Tailscale을 설치하고 로그인 화면에서 계정을 만들지 않은 채 관리자 PowerShell에서 아래 명령을 실행한다. `여기에_발급받은_일회용_키` 부분을 본인 PC용 키로 바꾼다.

```powershell
& 'C:\Program Files\Tailscale\tailscale.exe' up --auth-key='여기에_발급받은_일회용_키'
& 'C:\Program Files\Tailscale\tailscale.exe' ip -4
```

키 자체에 태그를 지정했으므로 명령에 별도 태그 옵션은 필요 없다. 신규 설치 PC용 안내다. 기존에 다른 Tailscale 네트워크에 가입한 PC는 기존 연결을 확인한 뒤 진행한다.

이후 소유자의 Machines 목록에 해당 PC가 등록된다. 장치 이름과 VPN 주소를 확인하고 아래 2~4단계의 모델 설치와 AI 서버 실행을 진행한다. 이 방식에서는 장치 공유 링크를 만들거나 수락하는 단계가 필요 없다.

**일회용 등록 키는 등록에 한 번 쓰이는 키다. 등록 키가 만료되거나 폐기되어도 이미 등록된 PC의 연결이 즉시 끊기지는 않는다.** 발표가 끝나면 소유자의 Machines 목록에서 팀원 PC를 삭제하고, 팀원 PC에서도 Tailscale 연결을 해제한다. 태그 장치의 장치 키 만료는 기본적으로 꺼져 있으므로 종료 후 정리를 별도로 해야 한다.

공식 안내: https://tailscale.com/docs/features/access-control/auth-keys

## 1-B. 각자 계정으로 Tailscale 설치 및 장치 공유

1. 팀원은 https://tailscale.com/download/windows 에서 설치하고 본인 계정으로 로그인한다.
2. 팀원은 https://login.tailscale.com/admin/machines 에서 시험에 사용할 학교 PC를 찾는다.
3. 해당 PC의 `…` → `Share` → `Copy invite link`를 선택한다. 재사용 옵션은 끈 채 일회용 링크를 만든다.
4. 링크를 메인 서버 소유자에게 개인적으로 전달한다. 링크를 공개 게시하지 않는다.
5. 메인 서버 소유자는 기존 학교 PC·노트북을 등록한 Tailscale 계정으로 링크를 열고 공유를 수락한다.
6. 소유자 화면에서 보이는 장치 이름과 100.x.x.x 주소를 기록한다. 주소 충돌 시 공유받은 쪽 주소가 달라질 수 있으므로 양쪽 화면을 확인한다.

공유 방향은 **팀원 PC → 메인 서버 소유자의 계정**이다. 이 방식은 소유자가 팀원 PC로 요청을 보내고 응답을 받는 구조에 맞는다. 팀원 개인 계정의 다른 장치를 한꺼번에 초대할 필요는 없다. 공유는 양쪽 Tailscale 접근 정책과 Windows 방화벽에 따른다.

공식 안내: https://tailscale.com/docs/features/sharing

## 2. Ollama와 모델 설치

팀원 PC에 https://ollama.com/download/windows 의 공식 Windows 설치 프로그램으로 Ollama를 설치한다. 설치 후 새 PowerShell을 열고 다음을 실행한다.

```powershell
ollama --version
ollama pull gemma4:e2b-it-qat
```

완료 후 Windows 트레이의 Ollama 아이콘에서 종료한다. 기존 Ollama 서버가 실행 중이면 새 서버가 같은 포트를 사용할 수 없거나 새 설정이 적용되지 않는다. 다른 사람이 사용 중인 서버가 있다면 그 작업을 마친 뒤 실행한다.

이 단계에서는 Eye-Catch 프로젝트 전체나 사진 모델을 복사할 필요가 없다. **생성형 AI 전용** 서버다. 사진 처리도 분산하려면 별도로 프로젝트·Python 환경·사진 모델과 API를 설치하고 검증해야 한다. 생성형 AI 서버만 늘려서는 사진 처리 슬롯이 늘어나지 않는다.

## 3. 관리자 PowerShell에서 VPN 전용 AI 서버 실행

아래 학교 메인 서버 주소는 2026-10-14 확인값 `100.105.157.88`이다. 나중에 장치 재등록 등으로 주소가 바뀌면 먼저 확인한다.

```powershell
$ErrorActionPreference = 'Stop'
$teamTailscaleExe = 'C:\Program Files\Tailscale\tailscale.exe'
if (-not (Test-Path -LiteralPath $teamTailscaleExe)) {
    throw 'Tailscale을 먼저 설치하고 로그인해 주세요.'
}
$teamWorkerIp = (& $teamTailscaleExe ip -4 | Select-Object -First 1)
if ($LASTEXITCODE -ne 0 -or -not $teamWorkerIp) {
    throw 'Tailscale 연결 상태를 확인해 주세요.'
}
$teamWorkerIp = $teamWorkerIp.Trim()
if ($teamWorkerIp -notmatch '^100\.\d{1,3}\.\d{1,3}\.\d{1,3}$') {
    throw 'Tailscale IPv4 주소를 확인할 수 없습니다.'
}
$teamOllamaExe = (Get-Command ollama -CommandType Application -ErrorAction Stop).Source

New-NetFirewallRule -DisplayName 'EyeCatch-team-Gemma' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 11434 -LocalAddress $teamWorkerIp -RemoteAddress '100.105.157.88' -Profile Any | Out-Null

$env:OLLAMA_HOST = "${teamWorkerIp}:11434"
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_NUM_PARALLEL = '2'
Write-Host "이 PC의 AI 주소: http://${teamWorkerIp}:11434"
& $teamOllamaExe serve
```

마지막 명령은 실행 중인 상태로 두고 해당 PC의 전원·인터넷·Tailscale을 유지한다. GPU를 쓰는 게임이나 다른 AI 작업은 시험 중 종료한다. 절전 설정도 확인한다.

`OLLAMA_HOST`는 VPN 주소에만 서버를 바인딩한다. 위 방화벽 규칙은 학교 메인 서버의 VPN 주소에서 들어오는 11434/TCP 요청만 허용한다. 공유기 포트포워딩이나 Ollama의 공개 인터넷 노출은 필요 없다. 기존에 설치된 더 넓은 허용 규칙이 있다면 실제 접근 범위는 별도 확인해야 한다.

초기 병렬 수는 2다. 앞선 두 PC 시험에서 무조건 4로 올리는 것이 더 빠르거나 안정적이지 않았다. 각 PC의 실제 GPU 적재와 속도를 확인한 뒤 2/4를 비교한다. 변경하려면 실행 창에서 Ctrl+C 후 환경값을 바꾸고 `ollama serve`를 다시 실행해야 한다. 이는 생성 요청 수이며 방문자 정원이 아니다.

Ollama 공식 설정 안내: https://docs.ollama.com/faq

## 4. 메인 서버에서 확인하고 등록할 정보

공유를 수락한 메인 서버 소유자에게 다음을 알려준다.

- 공유받은 화면에서 보이는 장치 이름·Tailscale IPv4 주소
- GPU 모델과 VRAM 용량
- Ollama 실행 로그의 Listening 주소와 오류 유무

메인 서버에서는 지정한 장치에만 `/api/version`, `/api/tags`, 합성 입력 생성 요청을 보내 모델이 실제로 GPU에 올라가고 응답하는지 확인한다. 학교 네트워크가 직접 연결을 막으면 Tailscale 중계 경로가 사용될 수 있어 지연도 확인한다.

그 다음 메인 서버의 `.env` 파일에 각 장치의 주소를 분산 처리 대상(`OLLAMA_URLS`, 사진 서버도 함께 띄운 경우 `PHOTO_WORKER_URLS`)으로 등록하고, 6대 또는 7대 부하 시험을 한다.

```ini
# 메인 서버 + 팀원 PC Ollama 주소 목록 (쉼표 구분, /api/generate 생략 가능)
OLLAMA_URLS=http://127.0.0.1:11434,http://100.x.x.1:11434,http://100.x.x.2:11434

# 선택: 원격 사진 분석 API(8003 포트)도 함께 띄운 팀원 PC가 있는 경우
PHOTO_WORKER_URLS=http://100.x.x.1:8003,http://100.x.x.2:8003

# 워커 수에 맞춰 동시 입장 정원 조정 (부하 시험 후 확정)
MAX_ACTIVE_VISITORS=6
```

등록된 워커들은 진행 중인 요청 수가 가장 적은 워커(Least-In-Flight) 및 라운드로빈 순서로 자동 분배되며, 특정 PC의 응답이 실패하면 쿨다운(기본 15초) 동안 제외하고 즉시 다음 정상 워커로 자동 폴백(Failover)된다. 60명의 처리 성공률·응답 시간·과부하 후 회복을 측정한 뒤 실제 입장 정원을 정한다.

관람객은 기존 사이트 주소로 접속한다. 이 설계에서 관람객의 휴대전화에는 Tailscale이나 Ollama를 설치할 필요가 없다.

## 종료 및 정리

팀원 PC의 실행 창에서 Ctrl+C로 시험 Ollama를 종료한다. 필요하면 기존 트레이 앱을 다시 실행한다. 시험용 방화벽 규칙은 관리자 PowerShell에서 다음 명령으로 제거할 수 있다.

```powershell
Get-NetFirewallRule -DisplayName 'EyeCatch-team-Gemma' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
```

팀원은 Tailscale 장치의 Share 화면에서 해당 공유를 취소할 수 있다. 창에서만 설정한 Ollama 환경변수는 새 터미널이나 기존 트레이 앱에 영구 적용한 설정이 아니다.
