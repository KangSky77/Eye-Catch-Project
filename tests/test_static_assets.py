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
    assert "d.result_code === 'hold'" in vision
    assert "ai_hold" in vision
    # hold 처리는 정상 결과 표시보다 먼저 와야 한다
    assert vision.index("d.result_code === 'hold'") < vision.index("ai-result-display")

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
    # 외부 이미지·라이브러리 없이 동작해야 한다(발표장 오프라인 대비)
    assert "/static/assets/vision-scene.svg" in disease
    assert (STATIC / "assets" / "vision-scene.svg").exists()

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
    assert "d.result_code === 'blurry'" in vision
    assert vision.index("d.result_code === 'blurry'") < vision.index("ai-result-display")
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
