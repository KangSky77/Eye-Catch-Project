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
import re
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
