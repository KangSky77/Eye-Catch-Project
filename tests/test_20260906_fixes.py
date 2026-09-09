# -*- coding: utf-8 -*-
"""2026-09-06 실사용 점검(데스크톱 + S25 Ultra 실기기)에서 나온 수정의 회귀 방지.

각 테스트는 '무엇이 잘못됐었는지'를 먼저 적는다 — 나중에 이 줄을 지우려는 사람이
그게 왜 있는지 알 수 있어야 한다.
"""
import io
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return io.open(ROOT / rel, encoding="utf-8").read()


# ── 리포트 ─────────────────────────────────────────────────────────────

def test_새_검사는_이전_추가질문_답변을_지운다():
    """리셋이 #followup-response를 안 지워서, 새 리포트 밑에 이전 사람이 받은
    AI 답변이 그대로 남아 있었다(같은 기기를 돌려 쓰면 남의 질문까지 노출)."""
    core = read("static/app-core.js")
    body = core[core.index("function resetScreeningState()"):]
    body = body[:body.index("\n}\n")]
    assert "invalidateScreeningReport()" in body
    body = core[core.index("function invalidateScreeningReport()"):]
    body = body[:body.index("\n}\n")]
    assert "followup-response" in body
    assert "user-followup-input" in body


def test_추가질문_답변에_세대_가드가_있다():
    """스트리밍 도중 새 검사가 시작되면 늦게 도착한 답변이 새 리포트에 박혔다."""
    rep = read("static/app-report.js")
    body = rep[rep.index("async function askGemmaMore()"):]
    body = body[:body.index("\n}\n")]
    assert "state.sessionGeneration" in body
    assert body.count("isCurrent()") >= 3


# ── 응급 신호와 AI 요약의 긴급도 일치 ────────────────────────────────────

def test_응급신호가_소견서_요청에_실린다():
    """화면은 '지금 바로 진료를 받으세요'라고 띄우는데 바로 밑 AI 요약은
    '안압 측정을 받으실 수 있습니다'처럼 예약을 잡는 말투로 나왔다.
    서버 프롬프트가 이 회차가 응급인지 몰랐기 때문이다."""
    assert "red_flags" in read("static/app-report.js")
    assert "red_flags" in read("app/schemas/ai.py")
    assert "red_flags=req.red_flags" in read("app/api/routes.py")


def test_응급_프롬프트가_한가한_표현을_금지한다():
    llm = read("app/services/llm.py")
    assert "_URGENT_BLOCK_KO" in llm and "_URGENT_BLOCK_EN" in llm
    assert "urgent=bool(red_flags)" in llm
    for banned in ("정기 검진", "예약을 잡"):
        assert banned in llm, f"금지 표현 목록에 {banned}가 없다"
    # 지시문을 그대로 베껴 쓰는 사고가 있었다("지금 바로 간다."가 1줄째로 나옴)
    assert "그대로 옮겨 적지 마세요" in llm


def test_응급_회차에는_고정_안내문이_AI조언_위에_온다():
    html = read("static/index.html")
    assert 'id="opinion-urgent-note"' in html
    assert html.index('id="opinion-urgent-note"') < html.index('id="gemma-opinion-text"')
    assert "opinion_urgent_note" in read("static/app-report.js")


def test_언어_불일치_안내가_가리키는_본문보다_위에_있다():
    """문구가 6개 언어 모두 '아래 AI 참고 정보'라고 말하는데 정작 본문 아래에 있었다."""
    html = read("static/index.html")
    assert html.index('id="opinion-stale"') < html.index('id="gemma-opinion-text"')


# ── 암슬러 ─────────────────────────────────────────────────────────────

def test_암슬러_눈_안내문이_언어변경을_따라간다():
    """JS가 직접 써넣는 유일한 안내문이라 data-i18n이 없으면 언어를 바꿔도
    '어느 쪽 눈을 가리라'는 이 한 줄만 이전 언어로 남았다."""
    assert "setAttribute('data-i18n', 'ams_which_'" in read("static/app-vision.js")


def test_암슬러_눈_전환시_안내문으로_스크롤한다():
    """모바일에서 답변 버튼은 항상 접힌 부분 아래에 있어 사용자는 스크롤을 내린 채
    답한다. 그 위치에서 눈 안내문은 화면 밖(-225px)이라, 스크롤을 되돌리지 않으면
    검사하는 눈이 바뀐 것을 볼 방법이 없다 → 같은 눈으로 두 번 답하게 된다."""
    vis = read("static/app-vision.js")
    assert "scrollAmslerPromptIntoView" in vis
    body = vis[vis.index("function recordAmsler("):]
    body = body[:body.index("\n}\n")]
    assert "scrollAmslerPromptIntoView()" in body


def test_스크롤_목적지에_헤더_회피_여백이_있다():
    """scrollIntoView({block:'start'})는 요소를 뷰포트 맨 위에 붙이는데
    sticky 헤더(59~74px)가 그 자리를 덮고 있어 목적지가 통째로 가려졌다."""
    css = read("static/style.css")
    assert "scroll-margin-top" in css
    for sel in ("#amsler-eye-instruction", "#vt-test-area", "#vt-calib"):
        assert sel in css, f"{sel}에 scroll-margin이 없다"


def test_보정_전에는_시야각을_단정하지_않는다():
    """CSS 기준 96dpi(3.78 px/mm)를 가정하는데 요즘 폰은 4.5~5.5다.
    S25 Ultra(5.23)에서 격자는 54.7mm인데 75.7mm로 착각해 21cm를 안내했고,
    그 거리에서는 20°가 아니라 14.8°만 덮었다."""
    vis = read("static/app-vision.js")
    assert "ams_dist_note_uncal" in vis
    head = vis[:vis.index("ams_dist_note_uncal")]
    assert "calibrated" in head[-500:], "보정 여부로 갈라 쓰고 있지 않다"
    assert read("static/data.js").count("ams_dist_note_uncal:") == 6


@pytest.mark.parametrize("key", ["ams_glasses_note"])
def test_안경_착용_안내가_6개_언어에_있다(key):
    """암슬러는 16~21cm에서 보라고 한다. 노안이면 맨눈으로 초점이 안 맞아
    흐린 것을 '휘어 보임'으로 답하기 쉽고, 없는 황반 이상이 만들어진다."""
    assert read("static/data.js").count(key + ":") == 6, f"{key}가 6개 언어에 없다"
    assert 'data-i18n="' + key + '"' in read("static/index.html")


# ── 업로드 ─────────────────────────────────────────────────────────────

def test_업로드_전에_사진을_줄인다():
    """서버 상한은 24MP/10MB인데 갤럭시 고해상도 모드는 50MP·200MP다.
    S25 Ultra 실측: 50MP -> 413 해상도 초과, 200MP -> 413 용량 초과.
    '더 작은 사진을 올려주세요'라고 해도 사용자가 할 수 있는 일이 없다."""
    vis = read("static/app-vision.js")
    assert "shrinkForUpload" in vis and "UPLOAD_MAX_EDGE" in vis
    # 용량 검사보다 먼저 줄여야 한다 — 200MP는 축소 전에 이미 10MB를 넘는다
    assert vis.index("file = await shrinkForUpload(file)") < vis.index("if (file.size > MAX_UPLOAD_MB")


def test_업로드_오류가_언어중립_코드로_나간다():
    """서버가 한국어 문자열만 보내서, 앱을 영어·일본어로 쓰는 사용자에게도
    '이미지 해상도가 너무 큽니다'가 한국어로 떴다(6개 언어 중 5개에서 재현)."""
    vision = read("app/services/vision.py")
    assert "_upload_error(" in vision
    raw = [l for l in vision.splitlines()
           if "HTTPException(" in l and "_upload_error" not in l and "import" not in l]
    assert len(raw) == 1, f"코드화되지 않은 예외가 남아 있다: {raw}"

    js = read("static/app-vision.js")
    assert "uploadErrorMessage" in js and "UPLOAD_ERROR_KEYS" in js
    data = read("static/data.js")
    for key in ("err_img_resolution", "err_img_invalid", "err_ai_not_ready", "err_validator_busy"):
        assert data.count(key + ":") == 6, f"{key}가 6개 언어에 없다"


# ── 문진 ───────────────────────────────────────────────────────────────

def test_대기중에는_이전_질문_버튼을_치운다():
    """맞춤 질문 생성은 평균 19초(6회 측정 14.6~25.0초) 걸린다. 그동안 방금 답한
    질문의 네/아니오가 스피너 아래에 살아 있어, 눌러도 아무 일이 없었다."""
    chat = read("static/app-chat.js")
    body = chat[chat.index("function addLoadingMsg("):]
    body = body[:body.index("\n}\n")]
    assert "chat-controls" in body and "innerHTML = ''" in body


def test_기타증상_문구가_한_번만_들어간다():
    """맞춤 질문을 1개에서 2개로 늘린 뒤 리포트에 '기타 의심 증상 추가 발견'이
    두 번 찍혔다 — 맞춤 질문마다 같은 코드를 넣고 있었다."""
    assert "!state.chatSymptoms.includes('symptom_extra')" in read("static/app-chat.js")


def test_맞춤질문_중복_필터가_있다():
    """되묻기 금지를 프롬프트에 넣어도 젬마가 어긴다. 실제로 나온 쌍:
    '최근 몇 달 동안 시력이 ... 나빠졌나요?' / '최근 몇 달 사이 시력이 ... 나빠진 적이 있나요?'
    (글자 2-gram 자카드 0.54, 서로 다른 질문들은 0.03~0.05)"""
    chat = read("static/app-chat.js")
    assert "isDuplicateQuestion" in chat and "DUP_QUESTION_THRESHOLD" in chat
    assert "isDuplicateQuestion(result.question)" in chat


def test_진행표시가_맞춤질문까지_센다():
    """마지막 고정 질문에서 '15 / 15'가 떠 다 끝난 줄 알았는데
    번호 없는 질문이 두 개 더 나왔다."""
    chat = read("static/app-chat.js")
    survey = chat[chat.index("function surveyProgress()"):]
    survey = survey[:survey.index("\n}\n")]
    assert "state.maxDynamic" in survey
    assert "function dynamicProgress()" in chat
    assert "addMsg('bot', q, dynamicProgress())" in chat


# ── 기능검사 / 질환 카드 / 레이아웃 ──────────────────────────────────────

def test_측정불가_문구가_항목별로_나온다():
    """'양쪽 눈 모두 유효한 측정값을 계산할 수 없었습니다'가 바로 두 줄 위의
    logCS 1.80을 스스로 부정했다 — 시력만 실패하고 대비는 측정된 경우."""
    assert "vt_unmeasurable_kinds" in read("static/app-visiontest.js")
    assert read("static/data.js").count("vt_unmeasurable_kinds:") == 6


def test_질환_카드를_키보드로_열_수_있다():
    """role='button' + tabindex='0'인 div라 포커스는 가는데 Enter로 열리지 않았다.
    모달 쪽은 Escape·포커스 트랩까지 갖춰져 있는데 들어가는 문만 막혀 있었다."""
    dis = read("static/app-disease.js")
    assert "'Enter'" in dis and "disease-card" in dis
    assert "card.click()" in dis


def test_로딩_화면_자식이_하나로_묶여_있다():
    """데스크톱(>=1024px)에서 '#tab-test .step-content.active > * { width:100% }'가
    직계 자식을 전부 늘린다. 다른 단계는 자식이 카드 하나뿐인데 이 단계만 여러 개라,
    원형 미리보기(w-32)가 992x128 알약으로, 스피너가 화면을 가로지르는 타원으로 늘어났다."""
    html = read("static/index.html")
    block = html[html.index('id="step-ai-loading"'):]
    block = block[:block.index('id="step-ai-result"')]
    assert block.index("max-w-md mx-auto w-full") < block.index('id="preview-image"')


def test_작은_글씨_대비가_상향됐다():
    """10~11px + slate-400은 흰 배경에서 2.45:1 — WCAG AA(4.5:1) 미달이었다.
    그중 하나가 'AI 특징 점수는 확률이 아니다'라는 오해 방지 문장이었다."""
    for rel in ("static/index.html", "static/app-vision.js",
                "static/app-findings.js", "static/app-assess.js"):
        bad = re.findall(r"text-\[1[01]px\][^\"']*?text-slate-400", read(rel))
        assert not bad, f"{rel}에 대비 미달 조합이 남아 있다: {bad}"


def test_뒤로가기가_검사를_날리지_않는다():
    """리포트까지 끝낸 상태에서 안드로이드 뒤로가기 한 번에 탭이 닫히고 홈으로 나갔다.
    실측(S25 Ultra) — 수정 후 뒤로 1회: step-ai-result -> step-photo(결과 유지),
                                2회: step-photo -> step-intro(결과 유지)."""
    core = read("static/app-core.js")
    assert "history.pushState({" in core
    # 히스토리 유효성 기준은 navEpoch다. sessionGeneration을 쓰면 사진을 올릴 때마다
    # 번호가 올라가 같은 검사 안에서도 앞뒤 항목이 어긋난다(아래 테스트 참고).
    assert "ecNav: state.navEpoch" in core
    assert "addEventListener('popstate'" in core
    assert "function nextStep(sid, viaHistory = false)" in core
    # popstate에서 다시 push하면 무한 루프가 된다
    assert "nextStep(sid, true)" in core


def test_새_회차가_분석결과를_무효화한다():
    """홈 이동/새 회차 뒤 늦은 사진 응답이 남으면 안 된다."""
    core = read("static/app-core.js")
    vision = read("static/app-vision.js")
    assert "cancelEyeAnalysis()" in core
    assert "visionTest" not in core
    assert "_analysisRequestId++" in vision


def test_문진_재시작이_이전_회차의_맞춤질문을_끊는다():
    """startChat()은 반드시 세대를 올려야 한다.

    올리지 않으면 이전 회차의 맞춤 질문 요청(15~25초)이 fetchNextQuestion의 가드를
    통과해, 1번 질문부터 다시 시작한 새 문진에 '19 / 20 이전 회차 질문'으로 끼어든다
    (뒤로가기 → 암슬러 재답변 경로에서 2026-09-07 재현).

    한때 이걸 뺀 적이 있는데, 이유는 히스토리 항목이 sessionGeneration을 회차 식별자로
    쓰고 있어서였다. 지금은 히스토리가 navEpoch를 따로 쓰므로 둘이 충돌하지 않는다."""
    chat = read("static/app-chat.js")
    start = chat[chat.index("function startChat()"):chat.index("function askRiskQuestion")]
    assert "state.sessionGeneration++" in start
    assert "if (state.sessionGeneration !== generation) return;" in chat
    # 히스토리는 sessionGeneration을 쓰면 안 된다 — 그래야 위 증가가 안전하다
    core = read("static/app-core.js")
    assert "ecSession" not in core, "히스토리가 다시 sessionGeneration에 묶였다"
