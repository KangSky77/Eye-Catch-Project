// ==========================================
// app-visiontest.js — 시력 · 대비감도 자가검사
// app-core.js, calibration.js가 먼저 로드되어야 함
//
// 왜 이 기능인가:
//   사진 모델은 '겉으로 보이는' 백내장만 잡는다. 기능검사로 좌우 차이를 함께 보면
//   사진만으로는 안 보이는 신호를 참고로 얻을 수 있다.
//
// ⚠️ 현재 위치: 검증 전 '참고용 측정'이다. 임상 시력값이 아니다.
//   같은 기기·거리에서 재므로 좌우 비교가 절대값보다 안정적인 것은 맞지만,
//   화면 축소 오차·검사 순서·피로/학습·눈 가림 실패·화면 밝기와 감마·주변 조명·
//   굴절 이상 같은 교란을 아직 통제하지 못했다.
//   그래서 이 결과는 리포트에 참고 정보로만 표시하고, 방문 권고(computeTriage)
//   계산에는 넣지 않는다. 기기별 반복 검증을 통과한 뒤에 다시 논의할 것.
//
// 왜 Tumbling E인가:
//   문자 시표는 언어·문해력에 의존한다. E의 방향(상하좌우)을 고르는 4지 선다는
//   6개국어 어디서나 동일하게 동작하고, 찍어서 맞출 확률(25%)도 계산에 넣기 쉽다.
//
// 왜 canvas인가:
//   DOM 텍스트(CSS px)로 그리면 시력 1.0 시표가 2~6px밖에 안 돼 형태가 무너진다.
//   canvas 백킹스토어를 devicePixelRatio배로 잡고 '물리 픽셀'에 직접 그려야 한다.
//   (프로토타입 calibration-demo.html에서 측정으로 확인한 제약)
// ==========================================

const VT = {
    // 표준 logMAR 진행(0.1 log 단위)에 대응하는 소수시력 사다리
    ACUITY_LEVELS: [0.1, 0.125, 0.16, 0.2, 0.25, 0.32, 0.4, 0.5, 0.63, 0.8, 1.0, 1.25, 1.6],
    // Pelli-Robson과 같은 0.15 log 단위 대비 사다리
    CONTRAST_LEVELS: [0.15, 0.30, 0.45, 0.60, 0.75, 0.90, 1.05, 1.20, 1.35, 1.50, 1.65, 1.80],
    TRIALS_PER_LEVEL: 3,       // 한 단계에 E 3개
    PASS_REQUIRED: 2,          // 3개 중 2개 이상 맞아야 통과 (우연 정답률 25% 대비 충분)
    CONTRAST_LETTER_ACUITY: 0.2,  // 대비검사용 글자 크기(크게 고정) — 크기가 아닌 명암만 변수로
};

const vtState = {
    phase: 'idle',      // idle | acuity | contrast | done
    eye: 'left',        // left | right (가리지 않은 = 검사 중인 눈)
    levelIdx: 0,
    trial: 0,
    correct: 0,
    current: null,      // 현재 제시된 방향
    results: { left: {}, right: {} },
};

const DIRECTIONS = ['up', 'right', 'down', 'left'];
const VT_COMPARE_EPSILON = 1e-9; // 1.20 - 0.90이 0.299999...가 되는 부동소수점 경계 보정

/** 이 기기·거리에서 실제로 표시 가능한 시력 단계만. vtStart에서 계산해 둔다. */
function vtAcuityLevels() {
    return vtState.acuityLevels && vtState.acuityLevels.length
        ? vtState.acuityLevels : VT.ACUITY_LEVELS;
}

// ------------------------------------------------------------------
// Tumbling E 그리기 (물리 픽셀 기준)
// ------------------------------------------------------------------

/**
 * 표준 시표 E: 5x5 단위 격자에 획 굵기 1단위, 획 사이 간격 1단위.
 * size = 시표 전체 높이(물리 px). 방향에 따라 회전.
 */
function drawTumblingE(ctx, cx, cy, size, direction, grayLevel) {
    const u = size / 5;                       // 1단위
    const rot = { right: 0, down: 90, left: 180, up: 270 }[direction] * Math.PI / 180;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(rot);
    ctx.fillStyle = `rgb(${grayLevel},${grayLevel},${grayLevel})`;
    // 기본 방향(right = 획이 오른쪽을 향함): 세로 등뼈 + 가로 획 3개
    ctx.fillRect(-2.5 * u, -2.5 * u, u, 5 * u);          // 등뼈
    for (const row of [-2.5, -0.5, 1.5]) {
        ctx.fillRect(-2.5 * u, row * u, 5 * u, u);        // 가로 획
    }
    ctx.restore();
}

/**
 * 캔버스를 물리 픽셀 해상도로 준비하고 { ctx, cssW } 를 반환.
 *
 * ⚠️ 여기서 반환하는 cssW는 '요청한 폭'이 아니라 **실제로 렌더된 폭**이다.
 *    이유: style.width를 지정해도 CSS(max-width, flex, padding 등)가 다시 줄일 수 있다.
 *    실제로 .vt-canvas의 max-width:100% + 부모 padding 때문에 캔버스가 11.3% 축소됐고,
 *    그 상태로 물리 크기를 계산하니 시표가 계산값보다 작게 그려졌다.
 *    → 폭을 정한 뒤 반드시 다시 '측정'해서, 그 값을 기준으로 시표 크기를 계산한다.
 *      이렇게 하면 CSS가 무엇을 하든 화면에 찍히는 크기가 계산과 일치한다.
 */
function prepareCanvas(canvas, requestedCssW, cssH) {
    const dpr = window.devicePixelRatio || 1;
    canvas.style.width = requestedCssW + 'px';
    canvas.style.height = cssH + 'px';

    // 레이아웃을 강제로 확정시킨 뒤 실제 폭을 읽는다
    const actualCssW = canvas.getBoundingClientRect().width || requestedCssW;
    if (Math.abs(actualCssW - requestedCssW) > 0.5) {
        // CSS가 개입했다 — 실제 폭에 맞춰 다시 지정해 계산과 표시를 일치시킨다
        canvas.style.width = actualCssW + 'px';
    }

    canvas.width = Math.round(actualCssW * dpr);
    canvas.height = Math.round(cssH * dpr);
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;        // 시표 가장자리를 뭉개지 않는다
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    return { ctx, cssW: actualCssW };
}

/** 부모의 '콘텐츠 폭'(패딩 제외). clientWidth는 패딩을 포함하므로 그대로 쓰면 넘친다. */
function contentWidthOf(el) {
    const cs = getComputedStyle(el);
    return el.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
}

// ------------------------------------------------------------------
// 검사 진행
// ------------------------------------------------------------------

function vtCalibration() {
    return window.ECCalib ? window.ECCalib.loadCalibration() : null;
}

/** 현재 단계의 시표를 그린다. */
function vtRenderStimulus() {
    const cal = vtCalibration();
    const canvas = document.getElementById('vt-canvas');
    if (!cal || !canvas) return;

    const dpr = window.devicePixelRatio || 1;
    const dist = cal.distanceMm || 600;
    // 부모의 '콘텐츠 폭'을 써야 한다 — clientWidth는 패딩을 포함해서 그대로 쓰면
    // max-width:100%에 걸려 캔버스가 다시 줄어든다(실제로 11.3% 축소됐던 버그)
    const cssH = 240;
    const { ctx, cssW } = prepareCanvas(canvas, Math.min(contentWidthOf(canvas.parentElement), 420), cssH);

    vtState.current = DIRECTIONS[Math.floor(Math.random() * 4)];

    let sizeMm, gray;
    if (vtState.phase === 'acuity') {
        sizeMm = window.ECCalib.acuityToLetterMm(vtAcuityLevels()[vtState.levelIdx], dist);
        gray = 0;                                            // 최대 대비(검정)
    } else {
        sizeMm = window.ECCalib.acuityToLetterMm(VT.CONTRAST_LETTER_ACUITY, dist);
        const logCS = VT.CONTRAST_LEVELS[vtState.levelIdx];
        gray = window.ECCalib.contrastToGray(window.ECCalib.logCSToContrast(logCS));
    }
    // CSS px/mm * dpr = 물리 px/mm
    const sizePhys = sizeMm * cal.pxPerMm * dpr;

    // 안전장치: 시표가 캔버스를 넘치거나 픽셀이 너무 적으면 측정값이 무의미해진다.
    // 조용히 잘못된 값을 내느니 콘솔에 남긴다.
    if (sizePhys > canvas.height || sizePhys > canvas.width) {
        console.warn('[vt] 시표가 캔버스보다 큽니다 — 거리를 늘리거나 캔버스를 키워야 합니다', { sizePhys, canvas: canvas.width + 'x' + canvas.height });
    }
    drawTumblingE(ctx, canvas.width / 2, canvas.height / 2, sizePhys, vtState.current, gray);

    vtUpdateProgress();
}

/** 현재 시표를 바꾸지 않고 진행 문구만 다시 그린다(언어 전환용). */
function vtUpdateProgress() {
    if (vtState.phase !== 'acuity' && vtState.phase !== 'contrast') return;
    const progress = document.getElementById('vt-progress');
    if (!progress) return;
    const t = translations[state.lang];
    progress.textContent =
        `${vtState.phase === 'acuity' ? (t.vt_acuity || '시력') : (t.vt_contrast || '대비감도')} · ` +
        `${(t['vt_eye_' + vtState.eye] || vtState.eye)} · ` +
        `${vtState.trial + 1}/${VT.TRIALS_PER_LEVEL}`;
}

/** 사용자가 방향을 골랐을 때. */
function vtAnswer(direction) {
    if (vtState.phase !== 'acuity' && vtState.phase !== 'contrast') return;
    if (direction === vtState.current) vtState.correct++;
    vtState.trial++;

    if (vtState.trial < VT.TRIALS_PER_LEVEL) { vtRenderStimulus(); return; }

    // 한 단계 종료 — 통과하면 더 어려운 단계로, 실패하면 이 눈의 이 검사 종료
    const passed = vtState.correct >= VT.PASS_REQUIRED;
    const levels = vtState.phase === 'acuity' ? vtAcuityLevels() : VT.CONTRAST_LEVELS;

    if (passed && vtState.levelIdx < levels.length - 1) {
        vtState.levelIdx++;
        vtState.trial = 0;
        vtState.correct = 0;
        vtRenderStimulus();
        return;
    }

    // 마지막으로 통과한 단계를 결과로 (한 단계도 통과 못 하면 사다리 아래로 표기)
    const achievedIdx = passed ? vtState.levelIdx : vtState.levelIdx - 1;
    const value = achievedIdx >= 0 ? levels[achievedIdx] : null;
    vtState.results[vtState.eye][vtState.phase] = value;
    vtAdvanceStage();
}

/** '안 보여요' — 오답으로 처리한다(건너뛰기가 아니다).
 *
 *  왜 오답인가: 이 검사는 4지선다 강제선택 계단식이라, 안 보여도 찍으면 25% 확률로
 *  맞는다. 3문항 중 2개 통과 규칙이라 순전히 운으로 한 단계를 통과할 확률이 15.6%다
 *  (C(3,2)*0.25^2*0.75 + 0.25^3). 이걸 '건너뛰기'로 만들어 시행에서 빼버리면
 *  단계가 끝나지 않아 검사가 멈추고, '통과'로 치면 시력이 부풀려진다.
 *
 *  오답 처리는 시력을 살짝 낮게 볼 수 있지만, 스크리닝에서는 그쪽이 안전한 오차다
 *  — 낮게 보면 안과에 가보라고 안내할 뿐이고, 높게 보면 잘못 안심시킨다.
 */
function vtCantSee() {
    if (vtState.phase !== 'acuity' && vtState.phase !== 'contrast') return;
    // 처음 눌렀을 때 한 번만: 왜 같은 버튼을 또 눌러야 하는지 설명한다.
    // (설계상 단계는 끝까지 진행하는데, 라벨만 보면 '검사가 끝난다'고 읽힌다)
    const hint = document.getElementById('vt-cant-see-hint');
    if (hint && hint.classList.contains('hidden')) {
        hint.textContent = translations[state.lang].vt_cant_see_hint || '';
        hint.classList.remove('hidden');
    }
    // 실제 방향과 다른 값을 넘겨 오답으로 집계시킨다
    const wrong = DIRECTIONS.find(d => d !== vtState.current) || 'up';
    vtAnswer(wrong);
}

/** 눈/검사 순서: 무작위로 고른 첫 눈의 시력·대비 → 반대쪽 눈의 시력·대비 → 결과 */
function vtAdvanceStage() {
    if (vtState.phase === 'acuity') {
        vtState.phase = 'contrast';
    } else if (vtState.eye === vtState.firstEye) {
        // 먼저 한 눈이 끝났으면 반대쪽으로 (시작 눈이 무작위이므로 고정 비교를 쓰면 안 된다)
        vtState.eye = vtState.eye === 'left' ? 'right' : 'left';
        vtState.phase = 'acuity';
    } else {
        vtFinish();
        return;
    }
    vtState.levelIdx = 0;
    vtState.trial = 0;
    vtState.correct = 0;
    vtShowEyePrompt();
}

/** 눈 가리기 안내 화면. */
function vtShowEyePrompt() {
    const t = translations[state.lang];
    document.getElementById('vt-test-area').classList.add('hidden');
    const prompt = document.getElementById('vt-eye-prompt');
    prompt.classList.remove('hidden');
    const which = t['vt_cover_' + (vtState.eye === 'left' ? 'right' : 'left')]
        || (vtState.eye === 'left' ? '오른쪽 눈을 가려주세요' : '왼쪽 눈을 가려주세요');
    document.getElementById('vt-eye-instruction').textContent = which;
    document.getElementById('vt-eye-sub').textContent =
        (vtState.phase === 'acuity' ? (t.vt_acuity_desc || '') : (t.vt_contrast_desc || ''));
}

/** 언어를 바꿔도 진행 중인 시표·판정 상태는 바꾸지 않고 동적 문구만 갱신한다. */
function vtRefreshDynamicUI() {
    const prompt = document.getElementById('vt-eye-prompt');
    const testArea = document.getElementById('vt-test-area');
    if ((vtState.phase === 'acuity' || vtState.phase === 'contrast') && prompt && !prompt.classList.contains('hidden')) {
        vtShowEyePrompt();
    }
    if ((vtState.phase === 'acuity' || vtState.phase === 'contrast') && testArea && !testArea.classList.contains('hidden')) {
        vtUpdateProgress();
    }
    if (vtState.phase === 'done' && state.visionTest) vtRenderResult();
    // 이미 띄워둔 '안 보여요' 설명도 현재 언어로
    const hint = document.getElementById('vt-cant-see-hint');
    if (hint && !hint.classList.contains('hidden')) {
        hint.textContent = translations[state.lang].vt_cant_see_hint || '';
    }
}

function vtBeginStage() {
    document.getElementById('vt-eye-prompt').classList.add('hidden');
    document.getElementById('vt-test-area').classList.remove('hidden');
    vtRenderStimulus();
    vtScrollToTest();
}

// ------------------------------------------------------------------
// 화면 캘리브레이션 UI (앱 내장)
// ------------------------------------------------------------------

let vtEdge = 'long';
let vtCardPx = 300;

function vtSetEdge(edge) {
    // 기준 변을 바꿔도 px/mm는 보존되도록 환산
    const prev = window.ECCalib.EDGE_MM[vtEdge];
    const ppm = vtCardPx / prev;
    vtEdge = edge;
    vtCardPx = ppm * window.ECCalib.EDGE_MM[edge];
    vtPaintCard();
}

function vtPaintCard() {
    const C = window.ECCalib;
    const box = document.getElementById('vt-cardbox');
    if (!box) return;

    // 탭이 숨겨져 있으면(display:none) 부모 폭이 0이라 계산이 전부 망가진다.
    // 이 상태로 그리면 카드 폭이 0이 되어 '파란 박스가 안 보이는' 버그가 된다.
    // → 보이게 될 때(showTab) 다시 호출되므로 여기서는 조용히 건너뛴다.
    const avail = box.parentElement.clientWidth;
    if (!avail) return;

    const ratio = C.CARD_WIDTH_MM / C.CARD_HEIGHT_MM;   // 1.586

    // 방향 선택의 핵심:
    //   긴 변 모드  = 카드를 눕혀서(가로) 맞춘다. 폭이 85.6mm 필요 → 넓은 화면용.
    //   짧은 변 모드 = 카드를 세워서(세로) 맞춘다. 폭 54mm · 높이 85.6mm 라
    //                 폰 화면(보통 68~72mm)에 둘 다 들어간다. 잘라 보여줄 필요가 없다.
    const w = vtEdge === 'long' ? vtCardPx : vtCardPx;              // 슬라이더가 곧 '맞추는 변'
    const h = vtEdge === 'long' ? vtCardPx / ratio : vtCardPx * ratio;
    box.style.width = Math.round(w) + 'px';
    box.style.height = Math.round(h) + 'px';
    box.dataset.orient = vtEdge === 'long' ? 'landscape' : 'portrait';
    // 안전장치: 레이아웃이 카드를 축소/확대하면 px/mm가 어긋난다. 어긋나면 콘솔에 남긴다.
    requestAnimationFrame(() => {
        const actual = box.getBoundingClientRect().width;
        const expect = vtEdge === 'long' ? vtCardPx : vtCardPx;
        if (Math.abs(actual - expect) > 1.5) {
            console.warn('[calib] 카드 렌더 폭 불일치 — px/mm가 부정확해집니다.', { expect, actual });
        }
    });

    // 슬라이더 상한: 카드 전체가 화면 안에 들어오는 선까지.
    // 상한이 '실제로 필요한 값'보다 낮으면 사용자가 카드를 못 맞춰 캘리브레이션 자체가 불가능해진다.
    // 화면 폭이 좁은(=px/mm가 높은) 기기까지 커버하도록 넉넉히 잡는다:
    //  - 좌우로 카드 컨테이너 패딩만큼(.vt-cardwrap 음수 마진) 더 쓴다
    //  - 세로는 뷰포트의 72%까지 허용(스크롤되어도 맞추는 데 지장 없음)
    // .vt-cardwrap이 음수 마진으로 이미 패딩을 되찾았으므로 avail에 그 폭이 포함돼 있다.
    // 여기서 또 더하면 상한이 실제 가용폭을 넘어 flex가 카드를 축소시키고,
    // 그러면 '계산한 폭'과 '실제 그려진 폭'이 달라져 px/mm가 조용히 틀어진다.
    const maxByWidth = Math.min(avail, window.innerWidth - 8);
    const maxByHeight = vtEdge === 'long'
        ? window.innerHeight * 0.72 * ratio          // 가로 카드: 높이 = px/ratio
        : window.innerHeight * 0.72 / ratio;         // 세로 카드: 높이 = px*ratio
    document.getElementById('vt-slider').max =
        Math.max(80, Math.round(Math.min(maxByWidth, maxByHeight)));

    document.getElementById('vt-pxmm').textContent =
        (vtCardPx / C.EDGE_MM[vtEdge]).toFixed(2);

    const t2 = translations[state.lang];
    const th = document.getElementById('vt-touch-hint');
    if (th) th.innerHTML = t2.vt_lock_hint || '';
    const dg = document.getElementById('vt-dist-guide');
    if (dg) dg.innerHTML = t2.vt_dist_guide || '';
    const dt = document.getElementById('vt-dist-tol');
    if (dt) dt.innerHTML = t2.vt_dist_tolerance || '';
    vtUpdateLockButton();

    const hint = document.getElementById('vt-orient-hint');
    if (hint) {
        const t = translations[state.lang];
        hint.innerHTML = vtEdge === 'long'
            ? (t.vt_orient_landscape || '') : (t.vt_orient_portrait || '');
    }

    for (const e of ['long', 'short']) {
        const b = document.getElementById('vt-edge-' + e);
        if (b) b.className = 'flex-1 py-2 rounded-xl text-[11px] font-bold ' +
            (e === vtEdge ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600');
    }
}

// ------------------------------------------------------------------
// 실물 카드를 화면에 올려두면 그 접촉이 터치로 인식돼 화면이 확대·스크롤된다.
// 캘리브레이션 단계에서만 제스처를 잠그고, 벗어나면 반드시 되돌린다.
// (확대를 앱 전체에서 영구히 끄면 저시력 사용자에게 해롭다 — 이 화면에서만 끈다)
// ------------------------------------------------------------------
const VT_VIEWPORT_DEFAULT = 'width=device-width, initial-scale=1.0';
const VT_VIEWPORT_LOCKED =
    'width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=no';

function vtLockViewport(lock) {
    vtGestureLockActive = !!lock;
    const meta = document.querySelector('meta[name="viewport"]');
    if (meta) meta.setAttribute('content', lock ? VT_VIEWPORT_LOCKED : VT_VIEWPORT_DEFAULT);
    const calib = document.getElementById('vt-calib');
    // touch-action:none 이 표준 방식 — iOS는 user-scalable=no 를 무시하므로 이쪽이 실질 방어선
    if (calib) calib.classList.toggle('vt-nozoom', !!lock);
    document.body.classList.toggle('vt-noscroll', !!lock);
}

// 문서 레벨 핸들러는 한 번만 붙지만, 실제 차단은 '캘리브레이션 잠금 중'일 때만 한다.
// 무조건 막으면 앱의 다른 화면(지도 확대 등)에서도 핀치가 죽어 접근성을 해친다.
let vtGestureLockActive = false;

/** 카드가 화면에 닿아 생기는 멀티터치 제스처(핀치 확대)를 막는다. */
function vtBlockGestures(e) {
    if (!vtGestureLockActive) return;
    if (e.type === 'gesturestart' || (e.touches && e.touches.length > 1)) e.preventDefault();
}

function vtInstallGestureGuards() {
    const calib = document.getElementById('vt-calib');
    if (!calib || calib.dataset.guarded) return;
    calib.dataset.guarded = '1';
    // passive:false 여야 preventDefault가 먹는다
    calib.addEventListener('touchmove', (e) => {
        if (vtGestureLockActive) e.preventDefault();
    }, { passive: false });
    document.addEventListener('gesturestart', vtBlockGestures, { passive: false });   // iOS Safari
    document.addEventListener('touchmove', vtBlockGestures, { passive: false });
}

/** 사용자가 직접 켜고 끄는 화면 고정. 카드 놓을 자리까지 스크롤한 뒤 켜면 된다. */
function vtToggleLock() {
    vtLockViewport(!vtGestureLockActive);
    vtUpdateLockButton();
}

const VT_LOCK_ICON_ON  = '<svg viewBox="0 0 24 24" fill="none"><rect x="5" y="10.5" width="14" height="9.5" rx="2"/><path d="M8.2 10.5V7.6a3.8 3.8 0 0 1 7.6 0v2.9"/></svg>';
const VT_LOCK_ICON_OFF = '<svg viewBox="0 0 24 24" fill="none"><rect x="5" y="10.5" width="14" height="9.5" rx="2"/><path d="M8.2 10.5V7.6a3.8 3.8 0 0 1 7.3-1.3"/></svg>';

function vtUpdateLockButton() {
    const b = document.getElementById('vt-lock-btn');
    if (!b) return;
    const t = translations[state.lang];
    // 아이콘은 기기마다 모양이 달라지는 이모지 대신 선형 SVG (앱 전체 아이콘 규칙과 동일)
    b.innerHTML = '';
    const ico = document.createElement('span');
    ico.className = 'vt-lock-ico';
    ico.setAttribute('aria-hidden', 'true');
    ico.innerHTML = vtGestureLockActive ? VT_LOCK_ICON_ON : VT_LOCK_ICON_OFF;   // 고정 상수
    const label = document.createElement('span');
    label.textContent = vtGestureLockActive ? (t.vt_lock_on || '고정됨') : (t.vt_lock_off || '화면 고정하기');
    b.append(ico, label);
    b.className = 'w-full mt-3 py-3 rounded-2xl font-bold text-[13px] btn-pop ' +
        (vtGestureLockActive ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-700');
}

/** 거리 드롭다운에서 '직접 입력'을 고르면 숫자 입력칸을 연다. */
function vtOnDistChange() {
    const sel = document.getElementById('vt-dist');
    const custom = document.getElementById('vt-dist-custom');
    if (custom) custom.classList.toggle('hidden', sel.value !== 'custom');
    vtPaintCard();
}

/** 현재 선택된 보는 거리(mm). '직접 입력'이면 숫자 입력칸 값을 cm→mm로. */
function vtCurrentDistanceMm() {
    const sel = document.getElementById('vt-dist');
    if (!sel) return 600;
    if (sel.value === 'custom') {
        const cm = parseFloat(document.getElementById('vt-dist-custom').value);
        return (isFinite(cm) && cm >= 20 && cm <= 200) ? cm * 10 : 600;
    }
    return parseFloat(sel.value);
}

/** +/− 미세조정 — 카드를 화면에 댄 채로 크기를 바꿀 수 있게 한다. */
function vtNudge(delta) {
    const sl = document.getElementById('vt-slider');
    const next = Math.min(parseFloat(sl.max), Math.max(parseFloat(sl.min), vtCardPx + delta));
    vtCardPx = next;
    sl.value = next;
    vtPaintCard();
}

/** 탭이 보이게 되거나 화면이 회전하면 다시 그린다(숨김 상태에서는 폭이 0이라 계산 불가). */
function vtRefreshCalibrationUI() {
    if (!document.getElementById('vt-cardbox')) return;
    vtInstallGestureGuards();
    vtUpdateLockButton();
    // 슬라이더 값이 새 상한을 넘으면 클램프
    vtPaintCard();
    const sl = document.getElementById('vt-slider');
    if (sl && vtCardPx > parseFloat(sl.max)) {
        vtCardPx = parseFloat(sl.max);
        sl.value = vtCardPx;
        vtPaintCard();
    } else if (sl) {
        sl.value = vtCardPx;
    }
}
window.addEventListener('resize', vtRefreshCalibrationUI);
window.addEventListener('orientationchange', () => setTimeout(vtRefreshCalibrationUI, 200));

function vtSaveCalibration() {
    const dist = vtCurrentDistanceMm();
    const cal = window.ECCalib.saveCalibration(vtCardPx, dist, vtEdge);
    // 검증 막대 — 자로 재서 50mm면 보정이 맞다는 것을 사용자가 직접 확인
    document.getElementById('vt-verify').classList.remove('hidden');
    document.getElementById('vt-ruler').style.width = (50 * cal.pxPerMm) + 'px';
}

function vtInitCalibrationUI() {
    if (!window.ECCalib || !document.getElementById('vt-cardbox')) return;
    const existing = window.ECCalib.loadCalibration();
    if (existing) {
        vtEdge = existing.edge || 'long';
        vtCardPx = existing.matchedPx || existing.cardWidthPx;
        const d = document.getElementById('vt-dist');
        if (d && existing.distanceMm) {
            const opt = [...d.options].find(o => o.value === String(existing.distanceMm));
            if (opt) { d.value = opt.value; }
            else {
                d.value = 'custom';
                const c = document.getElementById('vt-dist-custom');
                if (c) { c.value = existing.distanceMm / 10; c.classList.remove('hidden'); }
            }
        }
    } else {
        vtEdge = window.ECCalib.suggestEdge(window.innerWidth);
    }
    const sl = document.getElementById('vt-slider');
    sl.value = vtCardPx;
    sl.addEventListener('input', (e) => { vtCardPx = parseFloat(e.target.value); vtPaintCard(); });
    vtPaintCard();
}
window.addEventListener('DOMContentLoaded', vtInitCalibrationUI);

// ------------------------------------------------------------------
// 시작 / 종료
// ------------------------------------------------------------------

function vtStart() {
    const cal = vtCalibration();
    const t = translations[state.lang];
    if (!cal) {
        alert(t.vt_need_calib || '먼저 화면 캘리브레이션을 완료해주세요.');
        return;
    }
    // 보정 후 화면이 바뀌었으면(회전·확대·창 크기·다른 디스플레이) 예전 px/mm는 무효다.
    // calibrationStale()이 그걸 감지하도록 만들어져 있었는데 아무도 호출하지 않고 있었다.
    if (window.ECCalib.calibrationStale(cal)) {
        alert(t.calib_stale || '화면 설정이 바뀐 것 같습니다. 다시 보정해 주세요.');
        document.getElementById('vt-calib').classList.remove('hidden');
        document.getElementById('vt-calib').scrollIntoView({ block: 'start', behavior: 'smooth' });
        return;
    }

    // 이 기기·거리에서 물리적으로 표시할 수 없는 시력 단계는 사다리에서 잘라낸다.
    // 그러지 않으면 픽셀이 부족해 형태가 무너진 E를 보여주고 '못 봤다'로 기록된다.
    const maxA = window.ECCalib.maxDisplayableAcuity(
        cal.pxPerMm * (window.devicePixelRatio || 1), cal.distanceMm || 600);
    vtState.acuityLevels = VT.ACUITY_LEVELS.filter(a => a <= maxA);
    if (!vtState.acuityLevels.length) vtState.acuityLevels = [VT.ACUITY_LEVELS[0]];
    vtState.maxDisplayableAcuity = maxA;
    vtState.phase = 'acuity';
    // 시작 눈을 무작위로 — 항상 왼쪽부터 하면 피로·학습 효과가 한쪽 눈에만 쌓여
    // 좌우 차이가 검사 순서 때문에 생길 수 있다.
    vtState.eye = Math.random() < 0.5 ? 'left' : 'right';
    vtState.firstEye = vtState.eye;
    vtState.levelIdx = 0;
    vtState.trial = 0;
    vtState.correct = 0;
    vtState.results = { left: {}, right: {} };
    document.getElementById('vt-intro').classList.add('hidden');
    document.getElementById('vt-result').classList.add('hidden');
    // 검사 중에는 캘리브레이션 패널을 숨긴다 — 그대로 두면 모바일에서 시표와
    // 방향 버튼이 한 화면에 안 들어와 매번 스크롤해야 한다(390x844에서 실측 확인).
    document.getElementById('vt-calib').classList.add('hidden');
    vtLockViewport(false);          // 검사 중에는 확대 잠금이 필요 없다
    vtShowEyePrompt();
}

/** 검사 카드가 화면 위쪽에 오도록 스크롤 — 시표와 방향 버튼을 함께 보이게 한다. */
function vtScrollToTest() {
    const el = document.getElementById('vt-test-area');
    if (el) el.scrollIntoView({ block: 'start', behavior: 'smooth' });
}

/** DOM과 무관하게 양안 결과를 분류한다. 브라우저 흐름과 회귀 테스트가 같은 규칙을 쓴다. */
function vtClassifyResults(r) {
    const left = r.left || {};
    const right = r.right || {};
    const dCS = (left.contrast != null && right.contrast != null)
        ? Math.abs(left.contrast - right.contrast) : null;
    const dAc = (left.acuity != null && right.acuity != null)
        ? Math.abs(window.ECCalib.decimalToLogMAR(left.acuity) - window.ECCalib.decimalToLogMAR(right.acuity))
        : null;

    const oneSideUnmeasurable =
        (left.acuity == null) !== (right.acuity == null) ||
        (left.contrast == null) !== (right.contrast == null);
    const bothEyesUnmeasurable =
        left.acuity == null && right.acuity == null &&
        left.contrast == null && right.contrast == null;
    const asymmetric = !bothEyesUnmeasurable && (oneSideUnmeasurable
        || (dCS != null && dCS + VT_COMPARE_EPSILON >= 0.3)
        || (dAc != null && dAc + VT_COMPARE_EPSILON >= 0.2));

    return { dCS, dAc, oneSideUnmeasurable, bothEyesUnmeasurable, asymmetric };
}

function vtFinish() {
    vtState.phase = 'done';
    document.getElementById('vt-test-area').classList.add('hidden');
    document.getElementById('vt-eye-prompt').classList.add('hidden');

    const r = vtState.results;
    state.visionTest = {
        left:  { acuity: r.left.acuity,  logCS: r.left.contrast },
        right: { acuity: r.right.acuity, logCS: r.right.contrast },
    };
    // 양안 모두 최저 단계를 통과하지 못한 경우는 '차이 없음'이 아니라
    // 비교 불가능한 검사 실패다. 한쪽만 null인 경우와도 구분한다.
    const classified = vtClassifyResults(r);
    state.visionTest.asymmetric = classified.asymmetric;
    state.visionTest.oneSideUnmeasurable = classified.oneSideUnmeasurable;
    state.visionTest.bothEyesUnmeasurable = classified.bothEyesUnmeasurable;
    state.visionTest.deltaLogCS = classified.dCS;
    state.visionTest.deltaLogMAR = classified.dAc;

    vtRenderResult();
    const result = document.getElementById('vt-result');
    result.classList.remove('hidden');
    // 보정 패널이 DOM상 앞에 있어 모바일에서 결과가 화면 밖으로 밀리므로,
    // 사용자가 검사 완료 직후 결과를 바로 보도록 한다.
    requestAnimationFrame(() => result.scrollIntoView({ block: 'center', behavior: 'smooth' }));
}

/** 결과를 유지한 채 화면 보정 단계만 다시 연다. */
function vtRecalibrate() {
    vtState.phase = 'idle';
    document.getElementById('vt-result').classList.add('hidden');
    document.getElementById('vt-intro').classList.remove('hidden');
    const calib = document.getElementById('vt-calib');
    calib.classList.remove('hidden');
    vtRefreshCalibrationUI();
    calib.scrollIntoView({ block: 'start', behavior: 'smooth' });
}

// 기능검사 결과 배지 아이콘 — 앱 전체와 같은 선형 SVG (이모지 미사용)
const VT_WARN_ICON  = '<svg viewBox="0 0 24 24" fill="none"><path d="M12 8.6v4.2M12 16.4h.01"/><path d="M10.3 3.9 2.7 17.1A2 2 0 0 0 4.4 20h15.2a2 2 0 0 0 1.7-2.9L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>';
const VT_CROSS_ICON = '<svg viewBox="0 0 24 24" fill="none"><path d="M4 12.5 9 17.5 20 6.5"/></svg>';

/** 경고·교차검증 문구를 아이콘과 함께 만든다(문자열은 항상 textContent). */
function vtMakeNote(cls, icon, text) {
    const p = document.createElement('p');
    p.className = cls;
    const i = document.createElement('span');
    i.className = 'vt-note-ico';
    i.setAttribute('aria-hidden', 'true');
    i.innerHTML = icon;                 // 고정 상수
    const t = document.createElement('span');
    t.textContent = text;
    p.append(i, t);
    return p;
}

function vtRenderResult() {
    const t = translations[state.lang];
    const r = state.visionTest;
    const box = document.getElementById('vt-result-body');
    box.innerHTML = '';

    const mk = (label, val) => {
        const row = document.createElement('div');
        row.className = 'vt-row';
        const l = document.createElement('span'); l.className = 'vt-row-l'; l.textContent = label;
        const v = document.createElement('span'); v.className = 'vt-row-v'; v.textContent = val;
        row.appendChild(l); row.appendChild(v);
        return row;
    };
    const fmtA = (a) => a == null ? '—' : `${a.toFixed(2)} (logMAR ${window.ECCalib.decimalToLogMAR(a).toFixed(2)})`;
    const fmtC = (c) => c == null ? '—' : `logCS ${c.toFixed(2)}`;

    for (const side of ['left', 'right']) {
        box.appendChild(mk(`${t['vt_eye_' + side] || side} · ${t.vt_acuity || '시력'}`, fmtA(r[side].acuity)));
        box.appendChild(mk(`${t['vt_eye_' + side] || side} · ${t.vt_contrast || '대비감도'}`, fmtC(r[side].logCS)));
    }
    if (r.bothEyesUnmeasurable) {
        box.appendChild(vtMakeNote('vt-warn', VT_WARN_ICON, t.vt_unmeasurable_both || '양쪽 눈 모두 측정이 완료되지 않았습니다. 조명·거리·눈 가림을 확인하고 다시 검사해 주세요.'));
    } else if (r.oneSideUnmeasurable) {
        box.appendChild(vtMakeNote('vt-warn', VT_WARN_ICON, t.vt_unmeasurable || '한쪽 눈의 측정이 완료되지 않았습니다. 조건을 확인해 재검사하고, 차이가 지속되면 안과에서 확인하세요.'));
    } else if (r.asymmetric) {
        box.appendChild(vtMakeNote('vt-warn', VT_WARN_ICON, t.vt_asym || '좌우 결과 차이가 관찰됐습니다. 측정 조건에 따라 달라질 수 있으므로 재검사 후에도 차이가 지속되면 안과에서 확인하세요.'));
    }
    // 사진 모델의 편측 판정과 교차검증
    if (state.asymmetric && r.asymmetric) {
        box.appendChild(vtMakeNote('vt-cross', VT_CROSS_ICON, t.vt_cross_match || '사진 분석의 편측 소견과 기능검사 결과가 일치합니다.'));
    }
}
