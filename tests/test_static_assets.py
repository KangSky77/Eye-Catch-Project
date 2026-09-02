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


def test_촬영_안내가_플래시를_켜라고_하지_않는다():
    """측정 근거: 정상으로 잘 판정되던 눈 사진 60장에 플래시 반사를 합성하니
    캐치라이트 10장(17%), 베일글레어 16장(27%)이 '위험'으로 뒤집혔다.
    반면 사진 전체 밝기만 올린 대조군은 60장 중 1장만 바뀌었다 —
    모델이 밝기가 아니라 '눈동자 위 국소 백색 패턴'에 반응한다는 뜻이고,
    그게 바로 플래시 캐치라이트의 모습이다.
    앱이 스스로 오탐을 유도하는 안내를 하지 않도록 고정한다."""
    data = (STATIC / "data.js").read_text(encoding="utf-8")

    금지 = [
        "플래시를 켜주세요", "Turn on the flash", "Encienda el flash",
        "Activez le flash", "フラッシュをオンに", "请打开闪光灯",
    ]
    for phrase in 금지:
        assert phrase not in data, f"플래시를 켜라는 안내가 되살아났습니다: {phrase!r}"

    # 6개 언어 모두에 '끄라'는 안내가 있어야 한다
    권장 = ["플래시는 꺼주세요", "Turn the flash off", "Apague el flash",
            "Désactivez le flash", "フラッシュはオフに", "请关闭闪光灯"]
    for phrase in 권장:
        assert phrase in data, f"플래시 끄기 안내가 없습니다: {phrase!r}"


def test_반사_판독보류를_프론트가_처리한다():
    """서버가 result_code='hold'를 주면 의료 판정 대신 재촬영을 안내해야 한다.
    처리가 없으면 확률 0.0%가 '정상'으로 표시돼 정반대 결과가 나간다."""
    vision = (STATIC / "app-vision.js").read_text(encoding="utf-8")
    # 재촬영 코드는 retake 맵으로 한꺼번에 처리한다(2026-09-02) — hold 항목과 문구 키가 있어야 한다
    assert "hold:" in vision and "ai_hold" in vision
    # hold 처리는 정상 결과 표시보다 먼저 와야 한다
    assert vision.index("hold:") < vision.index("ai-result-display")

    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert data.count("ai_hold:") == 6, "6개 언어 모두에 반사 안내 문구가 있어야 한다"


def test_학습스크립트가_저장소_어디서_실행돼도_동작한다():
    """scripts/ 로 옮기면서 두 가지가 깨질 수 있었다:
      1) python scripts/x.py 로 실행하면 sys.path[0]이 scripts/라 app 패키지를 못 찾는다
      2) dataset/ 같은 상대경로가 실행 위치에 따라 달라진다
    각 스크립트 상단의 REPO_ROOT 부트스트랩이 둘 다 막는다."""
    scripts = ROOT / "scripts"
    assert scripts.is_dir(), "scripts/ 폴더가 있어야 한다"

    필수 = ["train_ai_v3.py", "train_ai_v4.py", "dedup_dataset.py",
            "validate_real_photos.py", "smoke_eye_detect.py", "build_eye_centroid.py"]
    for name in 필수:
        src = (scripts / name).read_text(encoding="utf-8")
        assert "REPO_ROOT = Path(__file__).resolve().parent.parent" in src, f"{name}: 루트 부트스트랩 없음"
        assert "sys.path.insert(0, str(REPO_ROOT))" in src, f"{name}: sys.path 보정 없음"
        assert "os.chdir(REPO_ROOT)" in src, f"{name}: 작업 디렉터리 보정 없음"


def test_파이프라인_산출물_경로가_data폴더를_가리킨다():
    """dataset_group_map.json 등을 data/로 옮겼으므로 읽고 쓰는 쪽도 같이 가야 한다.
    한쪽만 바뀌면 학습이 '그룹 맵 없음'으로 조용히 다른 분할을 쓰게 된다."""
    dedup = (ROOT / "scripts" / "dedup_dataset.py").read_text(encoding="utf-8")
    assert 'Path("data/dataset_group_map.json")' in dedup

    v3 = (ROOT / "scripts" / "train_ai_v3.py").read_text(encoding="utf-8")
    assert '"data/dataset_group_map.json"' in v3
    assert '"data/label_conflicts.json"' in v3

    for f in ["dataset_group_map.json", "label_conflicts.json", "brightiris_attributions.csv"]:
        assert (ROOT / "data" / f).exists(), f"data/{f} 가 없습니다"


def test_모델_메타데이터는_가중치_옆에_남아있다():
    """tests/test_model_consistency.py가 settings.model_path의 .pth를
    _metadata.json으로 바꿔 찾는다. 메타데이터만 옮기면 이 짝이 깨진다."""
    metas = list(ROOT.glob("cataract_*_metadata.json"))
    assert metas, "모델 메타데이터가 루트에 있어야 한다(.pth와 같은 위치)"


def test_소견서_실패시_검사전체를_다시_하지_않고_재시도할_수_있다():
    """소견서 생성은 개발 중 --reload 재시작, ngrok 끊김, Ollama 콜드스타트로
    흔히 끊긴다. 예전에는 finish() 안에 통째로 들어 있어서 실패하면
    문진부터 다시 해야 했다."""
    report = (STATIC / "app-report.js").read_text(encoding="utf-8")

    # 재시도 가능한 별도 함수로 분리돼 있어야 한다
    assert "async function runAiOpinion()" in report
    # 요청 본문을 보관해야 같은 입력으로 다시 시도할 수 있다
    assert "state.opinionRequest" in report
    # 중복 클릭 방지
    assert "_opinionBusy" in report
    # 성공/실패 어느 쪽이든 잠금이 풀려야 한다
    tail = report[report.index("async function runAiOpinion()"):]
    assert "finally {" in tail and "_opinionBusy = false;" in tail

    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert 'id="opinion-retry"' in html
    assert "runAiOpinion()" in html

    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert data.count("opinion_retry:") == 6, "6개 언어 모두에 재시도 버튼 문구가 있어야 한다"
    assert data.count("opinion_retry_hint:") == 6


def test_MTCNN_미설치를_조용히_넘기지_않는다():
    """facenet-pytorch는 --no-deps 선택 설치라 환경에서 쉽게 사라진다.
    없으면 얼굴 사진도 전체 이미지로 분석되고 눈별 판정이 사라지는데,
    예전에는 로그에 아무 표시가 없어 몇 주간 모르고 쓸 수 있었다."""
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    idx = main.index("eye_detector.is_available()")
    tail = main[idx:idx + 1200]
    assert "else:" in tail
    assert "logger.warning" in tail
    assert "facenet-pytorch" in tail


def test_지도가_sticky_헤더를_가리지_않는다():
    """Leaflet은 내부 pane에 z-index 400~700, 컨트롤에 1000을 쓴다.
    지도 컨테이너가 z-index:auto면 그 값이 문서 전체 기준으로 쌓여
    sticky 헤더(z-50) 위로 올라와 로고·메뉴를 가린다(실측 확인됨)."""
    css = (STATIC / "style.css").read_text(encoding="utf-8")
    embed = css[css.index(".map-embed {"):]
    embed = embed[: embed.index("}")]
    assert "z-index: 0" in embed, "지도 컨테이너에 쌓임 맥락이 필요하다"
    assert "isolation: isolate" in embed

    header = css[css.index(".site-header {"):]
    header = header[: header.index("}")]
    assert "z-index:" in header, "헤더도 명시적으로 올려둬야 한다"


def test_질환별_시야_체험이_4종_모두_다르게_동작한다():
    """안저사진은 '의사가 보는 그림'이라 일반 사용자에게 와닿지 않는다.
    시야 재현은 증상과 직접 연결되므로 질환마다 다른 효과여야 의미가 있다."""
    disease = (STATIC / "app-disease.js").read_text(encoding="utf-8")
    assert "VISION_SIMS" in disease
    for key in ["'cataract'", "'amd'", "'glaucoma'", "'dr'"]:
        assert key in disease, f"{key} 시야 효과가 없습니다"
    # 외부 이미지·라이브러리 없이 동작해야 한다(발표장 오프라인 대비) — 장면 사진은 로컬 CC0 실사진
    assert "/static/assets/vision-scene.jpg" in disease
    assert (STATIC / "assets" / "vision-scene.jpg").exists()
    assert (STATIC / "assets" / "ATTRIBUTION-vision-scene.md").exists()
    assert "VISION_SCENE_CREDIT" in disease and "sim-credit" in disease, "화면에 사진 출처가 있어야 한다"

    data = (STATIC / "data.js").read_text(encoding="utf-8")
    for key in ["sim_title:", "sim_desc:", "sim_normal:", "sim_strength:", "sim_disclaimer:"]:
        assert data.count(key) == 6, f"{key} 가 6개 언어에 모두 있어야 한다"


def test_시야_체험은_진단도구가_아님을_밝힌다():
    """증상을 재현해 보여주는 기능이라, 사용자가 '내 눈이 이렇구나'로
    받아들이지 않도록 교육용이라는 고지가 반드시 붙어야 한다."""
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert "진단 도구가 아닙니다" in data
    assert "Not a diagnostic tool" in data


def test_흔들림_보류를_프론트가_처리한다():
    vision = (STATIC / "app-vision.js").read_text(encoding="utf-8")
    assert "blurry:" in vision and "ai_blurry" in vision
    assert vision.index("blurry:") < vision.index("ai-result-display")
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert data.count("ai_blurry:") == 6


def test_시력검사에_안보여요가_있고_오답으로_처리된다():
    """4지선다 강제선택이라 안 보여도 찍으면 25%로 맞는다.
    '건너뛰기'로 만들면 그 단계가 끝나지 않아 검사가 멈추고,
    '통과'로 치면 시력이 부풀려진다. 그래서 오답으로 집계해야 한다."""
    vt = (STATIC / "app-visiontest.js").read_text(encoding="utf-8")
    assert "function vtCantSee()" in vt
    # 실제 방향과 다른 값을 넘겨 오답 처리
    assert "DIRECTIONS.find(d => d !== vtState.current)" in vt
    assert "vtAnswer(wrong)" in vt

    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert "vtCantSee()" in html
    assert 'data-i18n="vt_guess_hint"' in html, "찍어도 된다는 안내가 있어야 한다"

    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert data.count("vt_cant_see:") == 6
    assert data.count("vt_guess_hint:") == 6


def test_시력검사_UI가_복구되어_있다():
    """조원 논의 후 재투입(2abec18 revert). 스크립트 2개와 탭이 함께 살아나야 한다."""
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert 'id="tab-vision"' in html
    assert "app-visiontest.js" in html and "calibration.js" in html
    assert html.count('data-i18n="nav_vision"') == 2, "상단·하단 네비 모두 필요"


def test_촬영_예시_갤러리가_있고_사진과_출처가_존재한다():
    """팀 요청(2026-09-02): 찍기 전에 잘 찍은 얼굴 사진/흔들린 얼굴 사진을 보여준다.
    예시 사진은 CC0 원본 한 장을 가공한 것이므로 출처 파일도 같이 있어야 한다."""
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    guide = html[html.index('id="step-guide"'):html.index('id="step-photo"')]
    for name in ["face-good", "face-blurry"]:
        assert f"/static/assets/examples/{name}.jpg" in guide, f"{name} 예시가 촬영 안내 단계에 없습니다"
        assert (STATIC / "assets" / "examples" / f"{name}.jpg").exists()
    assert (STATIC / "assets" / "examples" / "ATTRIBUTION.md").exists()

    data = (STATIC / "data.js").read_text(encoding="utf-8")
    for key in ["ex_title:", "ex_good:", "ex_bad_blur:", "ex_hint:"]:
        assert data.count(key) == 6, f"{key} 가 6개 언어에 모두 있어야 한다"


def test_촬영_안내가_후면카메라_대신_흔들림_방지를_말한다():
    """팀 결정(2026-09-02): 1번 팁은 '후면 카메라 권장'을 빼고 '흔들리지 않게'로."""
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    for phrase in ["후면 카메라", "rear camera", "cámara trasera", "caméra arrière", "背面カメラ", "后置摄像头"]:
        assert phrase not in data, f"후면 카메라 권장 문구가 남아 있습니다: {phrase!r}"
    for phrase in ["흔들리지 않게", "Hold the phone steady", "Mantenga el teléfono firme",
                   "Tenez le téléphone bien stable", "手ブレしないように", "拍摄时请保持稳定"]:
        assert phrase in data, f"흔들림 방지 안내가 없습니다: {phrase!r}"


def test_글자_크기_조절이_있고_저장값을_먼저_적용한다():
    """모바일 가독성: A−/A+ 로 3단계, 선택은 localStorage에 저장돼 첫 화면부터 적용된다."""
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'id="fs-dec"' in html and 'id="fs-inc"' in html
    assert html.index("localStorage.getItem('ec_font')") < html.index("<body"), "저장값 복원은 <head>에서 먼저"
    core = (STATIC / "app-core.js").read_text(encoding="utf-8")
    assert "function applyFontSize" in core and "applyFontSize(loadFontLevel())" in core
    css = (STATIC / "style.css").read_text(encoding="utf-8")
    assert 'html[data-font="1"]' in css and 'html[data-font="2"]' in css
    # px 임의값 텍스트 클래스는 root를 따라가지 않으므로 rem 재정의가 있어야 실제로 커진다
    assert r".text-\[11px\] { font-size: .6875rem; }" in css
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert data.count("font_size:") == 6


def test_리포트_AI_요약_라벨이_3줄_요약을_말한다():
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert data.count("rep_info_title:") == 6
    for phrase in ["AI 3줄 요약", "AI 3-line summary", "3 líneas", "3 lignes", "AI 3行要約", "AI 三行摘要"]:
        assert phrase in data, f"3줄 요약 라벨이 없습니다: {phrase!r}"


def test_소견_완료후_부가동작_실패가_연결끊김으로_보이지_않는다():
    """S25 Ultra 실기기 재현(2026-09-02): 안드로이드 크롬은 페이지 컨텍스트의 new Notification()이
    예외를 던진다. 그 예외가 스트림 try/catch로 흘러 완성된 소견을 '연결 끊김'으로 덮어썼다."""
    report = (STATIC / "app-report.js").read_text(encoding="utf-8")
    assert "function notifyOpinionDone()" in report
    body = report[report.index("function notifyOpinionDone()"):]
    body = body[: body.index("\n}")]
    assert "try {" in body and "new Notification" in body, "알림 생성은 반드시 try 안에서"
    # runAiOpinion 본문 안에는 new Notification이 직접 등장하면 안 된다
    run = report[report.index("async function runAiOpinion()"):report.index("function notifyOpinionDone()")]
    assert "new Notification(translations" not in run   # 주석의 언급은 제외, 실제 호출만
    assert "notifyOpinionDone();" in run


def test_모바일_카메라로_바로_찍기_버튼이_있다():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'id="cataract-camera"' in html and " capture " in html, "capture 속성이 있어야 카메라가 바로 열린다"
    assert 'for="cataract-camera"' in html
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert data.count("camera_btn:") == 6
    css = (STATIC / "style.css").read_text(encoding="utf-8")
    assert ".touch-device .camera-btn { display: block; }" in css
    # (hover: none) 미디어쿼리로 판별하면 S펜 갤럭시(Ultra)에서 숨겨진다 — JS 터치 판별을 써야 한다
    assert "(hover: none)" not in css.split(".camera-btn")[0][-400:]
    vision = (STATIC / "app-vision.js").read_text(encoding="utf-8")
    assert "navigator.maxTouchPoints" in vision and "classList.add('touch-device')" in vision


def test_큰_글자_단계에서도_브랜드명을_숨기지_않는다():
    """실기기 피드백: A+ 최대에서 Eye-Catch 이름이 사라지면 앱이 바뀐 것처럼 보인다."""
    css = (STATIC / "style.css").read_text(encoding="utf-8")
    assert '.brand-name { display: none; }' not in css
    assert "#gemma-opinion-text { font-size: .9rem" in css, "3줄 요약 본문도 root 크기를 따라 커져야 한다"


def test_시야_체험은_모달_밖_패널에_있고_버튼으로_연다():
    """팀 요청(2026-09-02): 질환 상세 모달 안에 있던 시야 체험을 질환 탭 맨 아래 버튼 → 패널로."""
    disease = (STATIC / "app-disease.js").read_text(encoding="utf-8")
    open_body = disease[disease.index("function openDisease("):disease.index("function openDiseaseModal")]
    assert "buildVisionSim(" not in open_body, "시야 체험이 다시 모달 안으로 들어갔습니다"
    assert "function toggleVisionSim(" in disease and "function renderVisionSimPanel(" in disease
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    disease_tab = html[html.index('id="tab-disease"'):html.index('id="tab-report"')]
    assert 'id="sim-open-btn"' in disease_tab and 'id="vision-sim-panel"' in disease_tab
    assert disease_tab.index('id="disease-list"') < disease_tab.index('id="sim-open-btn"'), "버튼은 카드 목록 아래(맨 밑)에"
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    for key in ["sim_open_btn:", "sim_close_btn:", "sim_pick:"]:
        assert data.count(key) == 6, f"{key} 가 6개 언어에 모두 있어야 한다"


def test_외부리뷰_반영_모달_zindex_배너_개인정보_예시위치():
    """2026-09-02 외부 리뷰: 모달이 헤더에 가림 / 오류 토스트 놓침 / 사진 개인정보 안내 없음 / 기본 지도가 '내 주변'처럼 보임."""
    css = (STATIC / "style.css").read_text(encoding="utf-8")
    overlay = css[css.index(".dm-overlay {"):]; overlay = overlay[: overlay.index("}")]
    z = int(overlay.split("z-index:")[1].split(";")[0])
    header = css[css.index(".site-header {"):]; header = header[: header.index("}")]
    hz = int(header.split("z-index:")[1].split(";")[0])
    assert z > hz, "질환 모달은 고정 헤더보다 위에 있어야 한다"
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    photo = html[html.index('id="step-photo"'):html.index('id="step-ai-loading"')]
    assert 'id="upload-error"' in photo and photo.index('id="upload-error"') < photo.index('id="upload-guide"'), "오류 배너는 카드 상단에"
    assert 'data-i18n="upload_privacy"' in photo and photo.index('data-i18n="upload_privacy"') < photo.index('id="cataract-camera"'), "개인정보 안내는 업로드 버튼 위에"
    vision = (STATIC / "app-vision.js").read_text(encoding="utf-8")
    assert "function showUploadError" in vision and "clearUploadError();" in vision
    for code in ["blurry", "hold", "eyes_hidden", "invalid"]:
        assert f"{code}:" in vision, f"{code} 재촬영 안내가 배너로 나가야 한다"
    mapjs = (STATIC / "app-map.js").read_text(encoding="utf-8")
    assert "map-example-badge" in mapjs and "clearMapExample();" in mapjs
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    for key in ["ai_eyes_hidden:", "upload_privacy:", "upload_privacy_title:", "upload_privacy_more:", "map_example_badge:"]:
        assert data.count(key) == 6, f"{key} 가 6개 언어에 모두 있어야 한다"


def test_외부리뷰_문구_진단_아닌_리포트_점수는_100점만점_범위_명시():
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert "진단 리포트" not in data and "Diagnostic Report" not in data, "'진단'은 서비스 안내와 충돌한다 → 눈 건강 리포트"
    assert data.count("AI 특징 점수") >= 1 and "AI 위험 점수" not in data
    assert "특이 소견 없음 (정상)" not in data, "모델은 백내장만 본다 → '백내장 의심 소견 없음'"
    vision = (STATIC / "app-vision.js").read_text(encoding="utf-8")
    assert "/100" in vision and "${d.probability}%" not in vision, "리포트의 % 표기는 질병 확률로 읽힌다"
    assert "진행성 수정체 혼탁 특징만 확인합니다" in data, "첫 화면에서 사진 AI의 범위(보이는 진행성 혼탁만)를 밝혀야 한다"
    assert "검사는 모두 마쳤지만" in data, "시력검사 실패 문구는 '완료됐지만 계산 불가'로"
    disease = (STATIC / "app-disease.js").read_text(encoding="utf-8")
    assert "_simLevel" in disease, "언어 전환 시 시야 체험 강도가 초기화되면 안 된다"


def test_눈게이트_파일과_얼굴모드_검증():
    assert (ROOT / "app" / "models" / "eye_gate.npz").exists(), "scripts/build_eye_gate.py 산출물이 있어야 한다"
    src = (ROOT / "app" / "services" / "vision.py").read_text(encoding="utf-8")
    body = src[src.index("def predict_cataract("):]
    assert 'if mode == "face":' in body and '"eyes_hidden"' in body


def test_낮은_점수_구간과_클로즈업_권유가_프론트에_있다():
    """외부 테스트(AI 생성 얼굴 5장, 2026-09-02): 옅은 초기 혼탁이 0~4.9점 → '정상'. 낮은 점수는 '판단 어려움'으로
    분리하고, 얼굴 사진은 편의 기능이며 눈 클로즈업을 우선하도록 안내한다."""
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    for key in ["ai_uncertain:", "closeup_hint:", "closeup_btn:", "find_cat_uncertain:"]:
        assert data.count(key) == 6, f"{key} 가 6개 언어에 모두 있어야 한다"
    assert "백내장 판별 결과" not in data and "백내장 위험 단계" not in data, "판별/위험 단계 → 혼탁 특징 표현으로"
    assert "눈을 한쪽씩 가까이 찍어주세요" in data
    vision = (STATIC / "app-vision.js").read_text(encoding="utf-8")
    assert "d.closeup_suggested" in vision and "uncertain:" in vision
    findings = (STATIC / "app-findings.js").read_text(encoding="utf-8")
    assert "find_cat_uncertain" in findings


# ==========================================================================
# 2026-08-29 실사용 리뷰 대응 회귀 테스트
# ==========================================================================

def test_리포트_값이_언어전환에_따라_다시_그려진다():
    """회귀: 분석 시점 언어로 완성한 문자열을 state에 굳혀 놓아서, 언어를 바꾸면
    라벨만 번역되고 값은 이전 언어로 남았다(영어 리포트에 한국어가 섞임)."""
    core = (STATIC / "app-core.js").read_text(encoding="utf-8")
    vision = (STATIC / "app-vision.js").read_text(encoding="utf-8")
    report = (STATIC / "app-report.js").read_text(encoding="utf-8")
    findings = (STATIC / "app-findings.js").read_text(encoding="utf-8")

    # 언어 중립 원자료만 저장하고, 표시 문자열은 포매터가 만든다
    assert "function formatCataractResult()" in core
    assert "function formatAmslerResult()" in core
    assert "function formatSymptoms()" in core
    assert "state.aiResultData = {" in vision

    # 굳은 문자열을 다시 만들지 않는다
    assert "state.aiResult =" not in vision
    assert "state.amslerLabel" not in vision
    assert "state.amslerLabel" not in findings

    # 언어를 바꾸면 리포트 값도 다시 그린다
    assert "function refreshReportResults()" in report
    assert "refreshReportResults()" in core


def test_리포트가_위험점수를_확률로_표기하지_않는다():
    """모델 출력은 보정되지 않은 softmax라 확률이 아니다.
    결과 카드는 '%' 없이 쓰는데 리포트만 '(100%)'로 찍혀 두 가지로 읽혔다."""
    vision = (STATIC / "app-vision.js").read_text(encoding="utf-8")
    core = (STATIC / "app-core.js").read_text(encoding="utf-8")

    assert "${d.probability}%" not in vision
    assert "${e.probability}%" not in vision, "눈별 배지도 '%'를 붙이면 안 된다"
    assert "score_label" in core, "리포트도 결과 카드와 같은 '위험 점수' 표기를 쓴다"


def test_암슬러_격자가_화면_캘리브레이션을_사용한다():
    """회귀: 240 CSS px 고정 + 24px 칸(10x10)이라 30cm에서 약 12°만 덮었다.
    임상 규격은 10cm / 5mm 칸(20x20) = 중심 20°."""
    vision = (STATIC / "app-vision.js").read_text(encoding="utf-8")
    css = (STATIC / "style.css").read_text(encoding="utf-8")
    data = (STATIC / "data.js").read_text(encoding="utf-8")

    assert "function renderAmslerGrid()" in vision
    assert "loadCalibration" in vision, "시력검사의 px/mm 보정을 재사용해야 한다"
    assert "AMSLER_CELLS = 20" in vision
    assert "AMSLER_FIELD_DEG = 20" in vision
    # JS가 못 돈 순간의 대비책도 칸 수는 20x20이어야 한다 (240 / 12)
    assert "background-size: 12px 12px;" in css

    # 크기까지 애니메이션되면, 방금 설정한 폭을 되읽을 때 중간값이 나온다 —
    # 실제로 그 때문에 칸이 20개가 아니라 23개로 그려졌다.
    # (설명 주석에도 같은 문자열이 나오므로 주석을 지우고 선언만 본다)
    body = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rule = body[body.index(".amsler-grid"):]
    rule = rule[:rule.index("}")]
    assert "transition:" in rule and "all" not in rule.split("transition:")[1].split(";")[0], (
        f"격자 크기가 애니메이션되면 칸 계산이 어긋난다: {rule.split('transition:')[1].split(';')[0]!r}")

    # 숨겨진 상태(폭 0)에서 재면 크기가 틀어진다 — 보일 때까지 미룬다
    assert "requestAnimationFrame(renderAmslerGrid)" in vision

    # 계산된 거리를 안내하므로 안내문에 30cm를 박아두면 안 된다
    assert data.count("ams_dist_note:") == 6
    assert "30cm 거리에서 가운데 점" not in data


def test_결과화면에_분석한_사진이_보인다():
    """회귀: 미리보기가 로딩 화면에만 있어, 사진을 잘못 골라도 결과에서 알 수 없었다."""
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    vision = (STATIC / "app-vision.js").read_text(encoding="utf-8")
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert 'id="result-photo"' in html
    assert "function showAnalyzedPhoto()" in vision
    assert "showAnalyzedPhoto();" in vision
    assert data.count("result_photo_label:") == 6


def test_문진_답변버튼의_시각무게가_같다():
    """'네'만 파란 primary면 의학 문진에서 묵종 편향을 만든다."""
    chat = (STATIC / "app-chat.js").read_text(encoding="utf-8")
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")

    assert "if (o.value === false) b.className" not in chat, "선택지별로 스타일을 달리하지 않는다"
    # 말풍선(addMsg) 스타일과 섞이지 않도록 renderChatOptions 본문만 본다
    body = chat[chat.index("function renderChatOptions"):]
    body = body[:body.index(chr(10) + "}" + chr(10))]
    assert body.count("b.className =") == 1, "선택지마다 다른 스타일을 주면 편향이 생긴다"
    assert "bg-blue-600 text-white" not in body, "답변 버튼에 primary 스타일을 쓰지 않는다"

    yes = re.search(r'id="chat-yes-btn"[^>]*class="([^"]*)"', html).group(1)
    no = re.search(r'id="chat-no-btn"[^>]*class="([^"]*)"', html).group(1)
    assert yes == no, f"네/아니오 버튼 스타일이 달라 편향을 만든다: {yes!r} vs {no!r}"


def test_이미_답이_정해진_문진문항은_묻지_않는다():
    """안저 검사(1년 내)를 받았다면 '2년 내 안과 검진'은 논리적으로 참이다.
    두 번 물으면 사용자가 모순된 답을 남길 수 있다."""
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    chat = (STATIC / "app-chat.js").read_text(encoding="utf-8")

    assert "skipIf: { code: 'dr_fundus', answer: true }" in data
    assert "q.skipIf" in chat and "state.symptomAnswers[q.skipIf.code]" in chat
    assert "state.symptomAnswers[q.code] = yes" in chat

    # skipIf 대상은 판단 근거 문항보다 뒤에 있어야 symIdx가 밀리지 않는다
    assert data.index("code: 'dr_fundus'") < data.index("code: 'chk_recent'")


def test_문진_진행률이_처음부터_끝까지_이어진다():
    """회귀: 위험요인 5문항엔 진행률이 없고 증상 문항부터 1/13이 시작돼
    사용자가 전체 길이를 끝까지 알 수 없었다."""
    chat = (STATIC / "app-chat.js").read_text(encoding="utf-8")
    assert "function surveyProgress()" in chat
    assert chat.count("surveyProgress()") >= 3, "위험요인·증상 양쪽에서 써야 한다"
    assert "riskQuestions.length + symCount" in chat


def test_촬영안내가_두_화면에서_같은_말을_한다():
    """회귀: 팁 화면은 후면카메라/플래시끄기/30cm, 업로드 화면은 정면촬영/빛반사주의로
    서로 다른 말을 했다."""
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert "정면에서 촬영하세요." not in data
    # 9/2 팀 결정: '후면 카메라 권장'은 빼고 흔들림 방지·플래시 끄기·눈 클로즈업 — 업로드 화면 목록도 같은 세 가지
    guide_ko = data[data.index('guide_list: "'):]; guide_ko = guide_ko[: guide_ko.index('",')]
    for phrase in ["흔들리지 않게", "플래시는 꺼주세요", "가까이"]:
        assert phrase in guide_ko, f"업로드 화면 안내에 '{phrase}'가 없다 — 팁 화면과 같은 말을 해야 한다"
    assert "후면 카메라" not in data
    assert data.count("guide_list:") == 6


def test_안보여요를_왜_또_눌러야_하는지_설명한다():
    """오답 집계는 의도된 설계다(psychometrics). 다만 라벨만 보면 검사가 끝난다고
    읽히므로, 처음 한 번은 이유를 설명해야 한다."""
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    vt = (STATIC / "app-visiontest.js").read_text(encoding="utf-8")
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert 'id="vt-cant-see-hint"' in html
    assert "vt_cant_see_hint" in vt
    assert data.count("vt_cant_see_hint:") == 6


def test_소견서_언어불일치를_사용자에게_알린다():
    """LLM 소견서는 생성 시점 언어로 고정된다. 자동 번역하지 않는 대신
    다시 생성할 수 있다는 사실을 알려야 한다."""
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    report = (STATIC / "app-report.js").read_text(encoding="utf-8")
    data = (STATIC / "data.js").read_text(encoding="utf-8")
    assert 'id="opinion-stale"' in html
    assert "function regenerateOpinion()" in report
    assert "state.opinionLang" in report
    assert data.count("opinion_stale:") == 6 and data.count("opinion_regen:") == 6


def test_데스크톱에서_검사카드가_세로로_치우치지_않는다():
    """모바일 우선 레이아웃이라 큰 화면에서 아래 절반이 통째로 비어 보였다."""
    css = (STATIC / "style.css").read_text(encoding="utf-8")
    assert "@media (min-width: 1024px)" in css
    assert "#tab-test .step-content.active" in css
