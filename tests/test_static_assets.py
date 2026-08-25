"""빌드된 Tailwind CSS와 마크업의 동기화 검사.

왜 필요한가:
    static/tailwind.css는 빌드 산출물인데 저장소에 커밋돼 있고, node_modules는 없다.
    Tailwind는 JIT라 빌드 시점에 쓰이지 않은 유틸리티는 번들에 들어가지 않는데,
    없는 클래스를 써도 브라우저는 **에러 없이 조용히 무시**한다.
    → 마크업만 고치고 CSS를 다시 빌드하지 않으면 스타일이 소리 없이 사라진다.
    (실제로 mt-5·mt-0.5·leading-none을 쓴 코드가 그렇게 죽은 적이 있음)

무엇을 검사하나:
    index.html과 app-*.js에서 클래스 토큰을 뽑아, Tailwind 유틸리티처럼 생긴 것이
    tailwind.css(빌드본) 또는 style.css(수제 CSS)에 실제로 존재하는지 확인한다.
    커스텀 클래스(glass-card 등)는 style.css에서 잡히고, 어느 쪽에도 없으면 실패한다.

실패하면:
    npm run build:css   (node_modules 없으면 npm install 먼저)
    또는 이미 빌드본에 있는 다른 클래스로 교체.
"""
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

# Tailwind 유틸리티로 간주할 접두사/키워드.
# 여기에 안 걸리는 토큰(tab-report, ai-loading 등)은 커스텀 클래스나 클래스가 아닌
# 문자열이므로 검사 대상에서 제외한다 — 오탐을 줄이는 것이 목적.
TW_PREFIXES = (
    "bg-", "text-", "border", "rounded", "shadow", "opacity-", "ring-",
    "p-", "px-", "py-", "pt-", "pb-", "pl-", "pr-",
    "m-", "mx-", "my-", "mt-", "mb-", "ml-", "mr-",
    "w-", "h-", "min-w-", "min-h-", "max-w-", "max-h-",
    "gap-", "space-", "grid-", "col-", "row-",
    "font-", "leading-", "tracking-", "italic", "underline", "uppercase",
    "flex", "grid", "block", "inline", "hidden", "table",
    "items-", "justify-", "self-", "place-",
    "absolute", "relative", "fixed", "sticky", "static",
    "top-", "bottom-", "left-", "right-", "inset-", "z-",
    "overflow-", "object-", "cursor-", "select-", "pointer-events-",
    "backdrop-", "blur", "filter", "transition", "duration-", "ease-",
    "animate-", "transform", "scale-", "rotate-", "translate-",
    "divide-", "outline", "resize", "whitespace-", "break-", "truncate",
    "aspect-", "order-", "basis-", "grow", "shrink", "float-", "clear-",
)
# 변형 접두사(md:, hover: 등)는 떼고 본체로 판정
VARIANT_RE = re.compile(r"^(?:[a-z-]+:)+")


def _looks_tailwind(cls: str) -> bool:
    """접두사 매칭은 단어 경계를 지켜야 한다.
    'border'로 단순 startswith를 하면 판정 코드 문자열 'borderline'까지 클래스로 오인한다.
    → 접두사가 하이픈으로 끝나면 그대로, 아니면 '완전 일치' 또는 '접두사-'만 인정한다."""
    base = VARIANT_RE.sub("", cls)
    for p in TW_PREFIXES:
        if p.endswith("-"):
            if base.startswith(p):
                return True
        elif base == p or base.startswith(p + "-"):
            return True
    return False


def _selector_present(css: str, cls: str) -> bool:
    """빌드된 CSS에 이 클래스의 선택자가 있는지. Tailwind는 특수문자를 백슬래시로
    이스케이프하므로(text-[11px] -> .text-\\[11px\\], p-3.5 -> .p-3\\.5) 두 형태를 다 본다."""
    escaped = "".join(("\\" + c if not (c.isalnum() or c in "-_") else c) for c in cls)
    for sel in {"." + escaped, "." + cls}:
        # 뒤에 단어문자/하이픈이 오면 다른 클래스임 (.mt-4가 .mt-40에 걸리는 것 방지)
        if re.search(re.escape(sel) + r"(?![-\w])", css):
            return True
    return False


def _tokens_from_markup() -> dict[str, set[str]]:
    """{클래스: 출처파일들}. class= 속성, className 대입, classList 호출에서 수집."""
    found: dict[str, set[str]] = {}
    files = [STATIC / "index.html"] + sorted(STATIC.glob("app-*.js"))
    patterns = [
        re.compile(r'class="([^"]*)"'),                      # HTML 속성 + JS 템플릿 내부
        re.compile(r"className\s*=\s*'([^']*)'"),
        re.compile(r'className\s*=\s*"([^"]*)"'),
        re.compile(r"className\s*=\s*`([^`]*)`"),
        re.compile(r"classList\.(?:add|remove|toggle)\(([^)]*)\)"),
        re.compile(r"'((?:[a-z][\w./%\[\]:-]*\s+)*[a-z][\w./%\[\]:-]*)'"),  # 색상 맵 등 클래스 문자열
    ]
    # el.style.boxSizing = 'border-box' 같은 CSS "값"은 클래스가 아니다 —
    # border- 접두사에 걸려 오탐이 나므로 스캔 전에 걷어낸다.
    style_assign = re.compile(r"\.style(?:\.\w+|\[[^\]]+\])\s*=\s*(['\"`])[^'\"`]*\1")
    for f in files:
        text = style_assign.sub(" ", f.read_text(encoding="utf-8"))
        for pat in patterns:
            for m in pat.finditer(text):
                chunk = m.group(1)
                chunk = re.sub(r"\$\{[^}]*\}", " ", chunk)   # 보간부 제거
                chunk = chunk.replace("'", " ").replace('"', " ").replace(",", " ")
                for tok in chunk.split():
                    if _looks_tailwind(tok):
                        found.setdefault(tok, set()).add(f.name)
    return found


def test_마크업의_tailwind_클래스가_빌드본에_존재():
    tailwind_css = (STATIC / "tailwind.css").read_text(encoding="utf-8")
    style_css = (STATIC / "style.css").read_text(encoding="utf-8")
    if len(tailwind_css) < 1000:
        pytest.skip("tailwind.css가 비어 있음 — 빌드되지 않은 환경")

    missing = {
        cls: sorted(src)
        for cls, src in sorted(_tokens_from_markup().items())
        if not _selector_present(tailwind_css, cls) and not _selector_present(style_css, cls)
    }
    assert not missing, (
        "빌드된 static/tailwind.css에 없는 Tailwind 클래스를 쓰고 있습니다.\n"
        "브라우저는 이걸 에러 없이 무시하므로 스타일이 조용히 사라집니다.\n"
        "해결: `npm run build:css`로 재빌드하거나, 이미 빌드본에 있는 클래스로 교체하세요.\n"
        + "\n".join(f"  {c:24s} ← {', '.join(s)}" for c, s in missing.items())
    )


def test_html이_참조하는_정적파일이_실제로_존재():
    """?v= 버전만 올리고 파일명을 잘못 적으면 404 — 서버 없이 여기서 잡는다."""
    missing = {}
    for html_file in sorted(STATIC.glob("*.html")):
        refs = re.findall(r'(?:src|href)="/static/([^"?]+)', html_file.read_text(encoding="utf-8"))
        bad = [r for r in sorted(set(refs)) if not (STATIC / r).exists()]
        if bad:
            missing[html_file.name] = bad
    assert not missing, f"참조하는 정적 파일이 없습니다: {missing}"


def test_index_html에_외부_CDN_의존이_없다():
    """발표장 인터넷이 끊겨도 화면·PDF가 나와야 한다.

    핵심 자원(글꼴·html2pdf·Leaflet)은 static/vendor로 번들했다.
    누군가 다시 CDN 링크를 넣으면 여기서 잡는다.
    (지도 '타일'은 성격상 번들 불가 — app-map.js가 오프라인이면 안내로 대체한다)
    """
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    external = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    assert not external, f"index.html이 외부 자원을 참조합니다: {external}"


def test_로컬_번들_자원이_실제로_존재한다():
    required = [
        "vendor/html2pdf.bundle.min.js",
        "vendor/leaflet/leaflet.js",
        "vendor/leaflet/leaflet.css",
        "vendor/leaflet/images/marker-icon.png",
        "vendor/leaflet/images/marker-shadow.png",
        "vendor/pretendard/pretendard.css",
        "vendor/pretendard/PretendardVariable.woff2",
    ]
    missing = [r for r in required if not (STATIC / r).exists()]
    assert not missing, f"로컬 번들 자원 누락: {missing}"


def test_로컬_pretendard_css가_번들된_폰트를_가리킨다():
    css = (STATIC / "vendor" / "pretendard" / "pretendard.css").read_text(encoding="utf-8")
    urls = re.findall(r"url\('([^']+)'\)", css)
    assert urls, "폰트 url이 없습니다"
    for u in urls:
        assert not u.startswith("http"), f"외부 폰트를 가리킵니다: {u}"
        assert (STATIC / "vendor" / "pretendard" / u.lstrip("./")).exists(), f"폰트 파일 없음: {u}"


def test_방문권고가_검증되지_않은_지표를_쓰지_않는다():
    """triage(언제 병원에 갈지)는 근거가 있는 입력만 써야 한다.

    외부 리뷰 지적: 검증되지 않은 기능검사 좌우차와 임의 배점 위험점수가
    의료 행동 시점을 바꾸고 있었다. 둘 다 리포트 '참고 정보'로만 남기고
    computeTriage의 판정 분기에서는 제외했다. 되살아나면 여기서 잡는다.
    """
    src = (STATIC / "app-assess.js").read_text(encoding="utf-8")
    body = src[src.index("function computeTriage"):src.index("function renderTriage")]
    # 판정 분기(let level = ... 이후 if 체인)에 쓰이면 안 되는 입력
    decision = body[body.index("let level;"):]
    for banned in ("visionAsymmetric", "highRisk", "riskScore >="):
        assert banned not in decision, (
            f"computeTriage 판정 분기가 '{banned}'를 다시 쓰고 있습니다. "
            "검증 전 지표로 진료 시점을 정하면 안 됩니다."
        )


def test_기능검사_문구가_단정적이지_않다():
    """'영향을 받지 않는다', '일치합니다' 같은 단정은 검증 전에는 쓸 수 없다."""
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    banned = [
        "영향을 받지 않아", "결과가 일치합니다", "신뢰도가 높은 신호",
        "한쪽 눈만 진행된 변화", "one-sided change", "可能为单眼病变",
    ]
    found = [b for b in banned if b in data]
    assert not found, f"과도한 단정 표현이 남아 있습니다: {found}"


def _classify_vision_results(payload: dict) -> dict:
    """브라우저와 같은 JS 판정 함수를 Node에서 직접 실행한다."""
    source_path = json.dumps(str(STATIC / "app-visiontest.js"))
    payload_json = json.dumps(payload)
    script = f"""
const fs = require('fs');
global.window = {{
  addEventListener() {{}},
  ECCalib: {{ decimalToLogMAR(a) {{ return -Math.log10(a); }} }}
}};
const source = fs.readFileSync({source_path}, 'utf8');
(0, eval)(source + '\\n;process.stdout.write(JSON.stringify(vtClassifyResults({payload_json})));');
"""
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return json.loads(completed.stdout)


def test_기능검사_측정불가_상태를_좌우차이없음으로_처리하지_않는다():
    """양안 실패, 한쪽 실패, 정상 비교를 서로 다른 상태로 보존한다."""
    both_failed = _classify_vision_results({
        "left": {"acuity": None, "contrast": None},
        "right": {"acuity": None, "contrast": None},
    })
    assert both_failed["bothEyesUnmeasurable"] is True
    assert both_failed["oneSideUnmeasurable"] is False
    assert both_failed["asymmetric"] is False

    one_failed = _classify_vision_results({
        "left": {"acuity": None, "contrast": None},
        "right": {"acuity": 0.63, "contrast": 1.2},
    })
    assert one_failed["bothEyesUnmeasurable"] is False
    assert one_failed["oneSideUnmeasurable"] is True
    assert one_failed["asymmetric"] is True

    comparable = _classify_vision_results({
        "left": {"acuity": 0.8, "contrast": 1.2},
        "right": {"acuity": 0.8, "contrast": 1.2},
    })
    assert comparable["bothEyesUnmeasurable"] is False
    assert comparable["oneSideUnmeasurable"] is False
    assert comparable["asymmetric"] is False

    threshold = _classify_vision_results({
        "left": {"acuity": 0.8, "contrast": 0.9},
        "right": {"acuity": 0.8, "contrast": 1.2},
    })
    assert threshold["asymmetric"] is True, "0.30 logCS 경계값이 부동소수점 오차로 빠지면 안 됩니다"


def test_기능검사_동적문구와_결과가_재렌더된다():
    """언어 전환 시 보정 패널만 갱신해 진행 문구가 남는 회귀를 막는다."""
    core = (STATIC / "app-core.js").read_text(encoding="utf-8")
    vision = (STATIC / "app-visiontest.js").read_text(encoding="utf-8")
    findings = (STATIC / "app-findings.js").read_text(encoding="utf-8")
    assert "vtRefreshDynamicUI()" in core
    assert "result.scrollIntoView" in vision
    assert "function vtRecalibrate" in vision
    assert "bothEyesUnmeasurable" in findings


def test_가중치_미로드를_로드완료로_기록하지_않는다():
    """발표 환경에 모델이 없는데도 성공 로그를 남기면 준비 오류를 놓친다."""
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert "weights_ready = load_trained_weights()" in main
    assert "if weights_ready:" in main
    assert "사진 분석 API는 503으로 차단" in main


def test_질환_모달은_표시한_뒤_스크롤을_초기화한다():
    """숨겨진 모달에 scrollTop을 설정해 재열기 위치가 남는 회귀를 막는다."""
    src = (STATIC / "app-disease.js").read_text(encoding="utf-8")
    body = src[src.index("function openDiseaseModal"):src.index("function closeDisease")]
    assert body.index("classList.add('show')") < body.index("scrollTop = 0")


def test_질환_모달_닫기_svg가_실제로_그려진다():
    """fill이 없는 X 아이콘에는 CSS stroke와 크기가 반드시 필요하다."""
    css = (STATIC / "style.css").read_text(encoding="utf-8")
    rule = css[css.index(".dm-close svg"):css.index(".dm-icon-lg")]
    assert "stroke: currentColor" in rule
    assert "width: 18px" in rule
    assert "height: 18px" in rule


def test_질환_사진에_원본_라이선스와_변경_고지가_노출된다():
    """CC 사진의 원본·라이선스 링크와 재인코딩 사실을 공개 UI에 남긴다."""
    disease = (STATIC / "app-disease.js").read_text(encoding="utf-8")
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert "sourceLink.href = media.page" in disease
    assert "licenseLink.href = media.licenseUrl" in disease
    assert "media.change === 'reencoded'" in disease
    assert 'licenseUrl: "https://creativecommons.org/licenses/by-sa/3.0/"' in data
    assert 'licenseUrl: "https://creativecommons.org/publicdomain/mark/1.0/"' in data
    assert data.count("dis_modal_image_change_reencoded:") == 6


def test_맞춤형질문_답변버튼은_문진핸들러가_아니라_전용핸들러에_연결된다():
    """renderChatOptions가 handleAnswer에 고정돼 있어서, 문진이 끝난 뒤
    Gemma 맞춤형 질문에 '네'를 눌러도 문진 핸들러가 호출돼 그 자리에서 멈췄다.
    (handleSymptomAnswer가 범위 밖 문항을 만나 예외로 죽고, 그 직전에 걸어둔
     chatBusy 잠금이 영영 풀리지 않아 이후 모든 클릭이 무시됐다.)"""
    chat = (STATIC / "app-chat.js").read_text(encoding="utf-8")

    # 핸들러를 인자로 받아야 한다
    assert "function renderChatOptions(opts, onPick)" in chat
    assert "b.onclick = () => pick(o.value, o.label);" in chat

    # 맞춤형 질문 구간은 handleChatAnswer로 연결돼야 한다
    assert "v => handleChatAnswer(v === true)" in chat


def test_증상핸들러는_범위밖_문항에서_잠금을_걸지_않는다():
    """잠금을 걸어놓고 예외로 죽으면 이후 입력이 전부 무시된다.
    q가 없으면 chatBusy를 건드리기 전에 빠져나가야 한다."""
    chat = (STATIC / "app-chat.js").read_text(encoding="utf-8")
    body = chat[chat.index("function handleSymptomAnswer("):]
    body = body[: body.index("\n}")]
    assert body.index("if (!q) return;") < body.index("state.chatBusy = true;")


def test_암슬러_격자가_아래버튼과_붙지_않는다():
    """style.css가 tailwind.css보다 뒤에 로드되므로, .amsler-grid에 margin
    단축 속성을 쓰면 마크업의 mb-6이 0으로 덮여 격자가 버튼에 딱 붙는다."""
    css = (STATIC / "style.css").read_text(encoding="utf-8")
    rule = css[css.index(".amsler-grid {"):]
    rule = rule[: rule.index("}")]
    assert "margin: 0 auto" not in rule, "margin 단축 속성은 mb-6을 덮어쓴다"
    assert "margin-bottom:" in rule


def test_업로드_진행률은_100퍼센트로_차지_않는다():
    """xhr.upload 진행률은 '내보냈다'는 뜻이지 '서버가 다 받았다'가 아니다.
    ngrok/모바일망에서 100%를 띄우면 '다 됐는데 왜 안 넘어가지'가 된다."""
    vision = (STATIC / "app-vision.js").read_text(encoding="utf-8")
    assert "Math.min(99, Math.round(pct))" in vision
    assert "is-indeterminate" in vision
