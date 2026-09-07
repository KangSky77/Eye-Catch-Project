# -*- coding: utf-8 -*-
"""2026-09-07 코덱스 변경분에서 나온 회귀 4건의 재발 방지.

네 건 모두 의도는 타당했는데, state.sessionGeneration 하나를 세 가지 용도
(사진 분석 취소 · 문진 세대 · 히스토리 회차)로 겸용하면서 서로 간섭했다.
지금은 히스토리만 navEpoch로 분리해 각자 자기 일만 한다.

업로드 왕복 자체는 문자열 검사로 잡을 수 없어(호출 '순서' 문제였다)
tests/upload_lifecycle.test.cjs에서 실제로 함수를 돌려 확인한다.
"""
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return io.open(ROOT / rel, encoding="utf-8").read()


def test_요청번호를_리셋_뒤에_딴다():
    """resetScreeningState()는 내부에서 cancelEyeAnalysis()로 _analysisRequestId를 올린다.
    그보다 먼저 번호를 따 두면 방금 시작한 분석이 스스로 취소돼, 서버가 200으로 응답해도
    화면이 로딩에서 3분(ANALYSIS_TIMEOUT_MS) 멈춘다. 실측으로 앱 전체가 막혔다."""
    vis = read("static/app-vision.js")
    body = vis[vis.index("async function runAIAnalysis("):]
    body = body[:body.index("\n}\n")]
    assert body.index("resetScreeningState()") < body.index("const requestId ="), \
        "requestId를 resetScreeningState()보다 먼저 따고 있다 — 업로드가 스스로 취소된다"
    # 맨 앞의 '이전 업로드 무효화'는 남아 있어야 한다(늦게 온 응답이 새 결과를 덮지 않게)
    assert body.index("cancelEyeAnalysis()") < body.index("resetScreeningState()")


def test_히스토리는_sessionGeneration을_쓰지_않는다():
    """sessionGeneration은 사진을 올릴 때마다 올라간다. 그걸 히스토리 항목에 쓰면
    step-photo(올리기 전)와 step-ai-result(올린 뒤)의 번호가 달라져, 뒤로가기 한 번에
    step-photo를 건너뛰고 첫 화면으로 튄다. 실측으로 재현했다."""
    core = read("static/app-core.js")
    assert "navEpoch" in core
    assert "ecNav: state.navEpoch" in core
    assert "ecSession" not in core
    # navEpoch를 올리는 곳은 goHome() 하나뿐이어야 한다
    assert core.count("state.navEpoch++") == 1, "navEpoch를 올리는 곳이 goHome() 말고 또 있다"
    home = core[core.index("function goHome()"):]
    home = home[:home.index("\n}\n")]
    assert "state.navEpoch++" in home
    # 리셋이 navEpoch를 건드리면 업로드마다 히스토리가 무효화된다
    reset = core[core.index("function resetScreeningState()"):]
    reset = reset[:reset.index("\n}\n")]
    assert "navEpoch" not in reset


def test_질문_전환_중에는_언어_갱신을_미룬다():
    """handleAnswer는 riskIdx를 먼저 올리고 500ms 뒤에 질문을 그린다. 그 틈에 언어를
    바꾸면 refreshChatLanguage가 '다음 질문'을 '이전 질문 버블'에 덮어써서
    사용자 답변 기록이 사라지고, 타이머가 같은 질문을 또 추가해 두 번 나온다."""
    chat = read("static/app-chat.js")
    body = chat[chat.index("function refreshChatLanguage()"):]
    body = body[:body.index("\n}\n")]
    assert "if (state.chatBusy) return;" in body


def test_여러얼굴_문구가_다른_안내와_같은_자리에_있다():
    """형제 키(ai_blurry/ai_hold/ai_eyes_hidden/ai_invalid)는 data.js에 6개 언어로 있는데
    ai_multiple_faces만 app-vision.js 안에 인라인으로 하드코딩돼 있었다.
    그러면 check_i18n_limits.js가 못 지켜주고, 번역을 고치러 data.js를 연 사람은 못 찾는다."""
    data = read("static/data.js")
    for key in ("ai_blurry", "ai_hold", "ai_eyes_hidden", "ai_invalid", "ai_multiple_faces"):
        assert data.count(key + ":") == 6, f"{key}가 6개 언어에 없다"
    vis = read("static/app-vision.js")
    # 인라인 언어 사전이 되살아나면 안 된다
    assert "복数" not in vis and "複数の顔が検出" not in vis, "app-vision.js에 인라인 번역이 다시 생겼다"
