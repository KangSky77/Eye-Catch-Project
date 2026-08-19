// ==========================================
// app-visiontest.js — 시력 · 대비감도 자가검사
// app-core.js, calibration.js가 먼저 로드되어야 함
//
// 왜 이 기능인가:
//   사진 모델은 '겉으로 보이는' 백내장만 잡는다. 초기 핵경화는 외안부 사진에 안 나타난다.
//   반면 대비감도는 백내장 초기에 시력보다 먼저 떨어지므로, 사진이 놓치는 구간을 메운다.
//   또 좌우 차이는 같은 기기·같은 거리에서 재므로 캘리브레이션 오차가 상쇄된다 →
//   사진 모델의 편측(asymmetric) 판정과 교차검증할 수 있다.
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

/** 캔버스를 물리 픽셀 해상도로 준비하고 컨텍스트를 반환. */
function prepareCanvas(canvas, cssW, cssH) {
    const dpr = window.devicePixelRatio || 1;
    canvas.style.width = cssW + 'px';
    canvas.style.height = cssH + 'px';
    canvas.width = Math.round(cssW * dpr);
    canvas.height = Math.round(cssH * dpr);
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;        // 시표 가장자리를 뭉개지 않는다
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    return ctx;
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
    const cssW = Math.min(canvas.parentElement.clientWidth, 420);
    const cssH = 240;
    const ctx = prepareCanvas(canvas, cssW, cssH);

    vtState.current = DIRECTIONS[Math.floor(Math.random() * 4)];

    let sizeMm, gray;
    if (vtState.phase === 'acuity') {
        sizeMm = window.ECCalib.acuityToLetterMm(VT.ACUITY_LEVELS[vtState.levelIdx], dist);
        gray = 0;                                            // 최대 대비(검정)
    } else {
        sizeMm = window.ECCalib.acuityToLetterMm(VT.CONTRAST_LETTER_ACUITY, dist);
        const logCS = VT.CONTRAST_LEVELS[vtState.levelIdx];
        gray = window.ECCalib.contrastToGray(window.ECCalib.logCSToContrast(logCS));
    }
    // CSS px/mm * dpr = 물리 px/mm
    const sizePhys = sizeMm * cal.pxPerMm * dpr;
    drawTumblingE(ctx, canvas.width / 2, canvas.height / 2, sizePhys, vtState.current, gray);

    const t = translations[state.lang];
    document.getElementById('vt-progress').textContent =
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
    const levels = vtState.phase === 'acuity' ? VT.ACUITY_LEVELS : VT.CONTRAST_LEVELS;

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

/** 눈/검사 순서: 좌안 시력 → 좌안 대비 → 우안 시력 → 우안 대비 → 결과 */
function vtAdvanceStage() {
    if (vtState.phase === 'acuity') {
        vtState.phase = 'contrast';
    } else if (vtState.eye === 'left') {
        vtState.eye = 'right';
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

function vtBeginStage() {
    document.getElementById('vt-eye-prompt').classList.add('hidden');
    document.getElementById('vt-test-area').classList.remove('hidden');
    vtRenderStimulus();
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

    const th = document.getElementById('vt-touch-hint');
    if (th) th.innerHTML = translations[state.lang].vt_touch_hint || '';

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
    vtLockViewport(true);
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
    const dist = parseFloat(document.getElementById('vt-dist').value);
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
        if (d && existing.distanceMm) d.value = String(existing.distanceMm);
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
    vtState.phase = 'acuity';
    vtState.eye = 'left';
    vtState.levelIdx = 0;
    vtState.trial = 0;
    vtState.correct = 0;
    vtState.results = { left: {}, right: {} };
    document.getElementById('vt-intro').classList.add('hidden');
    document.getElementById('vt-result').classList.add('hidden');
    vtShowEyePrompt();
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
    // 좌우 차이 — 캘리브레이션 오차가 상쇄되므로 절대값보다 신뢰도가 높다
    const dCS = (r.left.contrast != null && r.right.contrast != null)
        ? Math.abs(r.left.contrast - r.right.contrast) : null;
    const dAc = (r.left.acuity != null && r.right.acuity != null)
        ? Math.abs(window.ECCalib.decimalToLogMAR(r.left.acuity) - window.ECCalib.decimalToLogMAR(r.right.acuity))
        : null;
    // 0.3 logCS(=2배) 이상 차이면 편측 의심 — 임상에서 유의미하게 보는 폭
    state.visionTest.asymmetric = (dCS != null && dCS >= 0.3) || (dAc != null && dAc >= 0.2);
    state.visionTest.deltaLogCS = dCS;
    state.visionTest.deltaLogMAR = dAc;

    vtRenderResult();
    document.getElementById('vt-result').classList.remove('hidden');
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
    if (r.asymmetric) {
        const w = document.createElement('p');
        w.className = 'vt-warn';
        w.textContent = t.vt_asym || '⚠️ 좌우 차이가 큽니다 — 한쪽 눈만 진행된 변화일 수 있어 안과 확인을 권합니다.';
        box.appendChild(w);
    }
    // 사진 모델의 편측 판정과 교차검증
    if (state.asymmetric && r.asymmetric) {
        const c = document.createElement('p');
        c.className = 'vt-cross';
        c.textContent = t.vt_cross_match || '📌 사진 분석의 편측 소견과 기능검사 결과가 일치합니다.';
        box.appendChild(c);
    }
}
