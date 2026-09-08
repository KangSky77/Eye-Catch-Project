from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_ai_analysis_block() -> str:
    vision = (ROOT / "static" / "app-vision.js").read_text(encoding="utf-8")
    start = vision.index("async function runAIAnalysis")
    end = vision.index("\n// 눈별(좌/우) 분석 결과 카드를", start)
    return vision[start:end]


def test_현재_분석_request_id는_화면_리셋_뒤에_발급한다():
    """resetScreeningState가 이전 요청을 무효화하므로 현재 요청 id는 그 뒤에 만들어야 한다."""
    block = _run_ai_analysis_block()
    reset_pos = block.index("resetScreeningState()")
    request_pos = block.index("const requestId = ++_analysisRequestId;")
    assert reset_pos < request_pos


def test_새_회차_초기화는_진행중인_눈_분석을_취소한다():
    """홈 이동·새 검사 시작 시 늦게 도착한 이전 분석 응답이 새 화면을 덮으면 안 된다."""
    core = (ROOT / "static" / "app-core.js").read_text(encoding="utf-8")
    start = core.index("function resetScreeningState()")
    end = core.index("\nfunction openMap()", start)
    reset_block = core[start:end]
    assert "cancelEyeAnalysis()" in reset_block


def test_reset_함수가_없는_독립_실행에서도_이전_분석을_취소한다():
    """app-vision.js를 독립적으로 시험하는 환경에서도 이전 요청 무효화가 유지돼야 한다."""
    block = _run_ai_analysis_block()
    assert "else cancelEyeAnalysis();" in block
