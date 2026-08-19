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
    const ratio = C.CARD_WIDTH_MM / C.CARD_HEIGHT_MM;
    const avail = box.parentElement.clientWidth;
    // 짧은 변 모드에서는 카드 전체 폭이 폰 화면을 넘으므로 잘라 표시한다
    let w = vtEdge === 'long' ? vtCardPx : vtCardPx * ratio;
    const h = vtEdge === 'long' ? vtCardPx / ratio : vtCardPx;
    if (w > avail) w = avail;
    box.style.width = w + 'px';
    box.style.height = h + 'px';
    document.getElementById('vt-slider').max =
        Math.max(80, Math.round(vtEdge === 'long' ? avail : window.innerHeight * 0.4));
    document.getElementById('vt-pxmm').textContent =
        (vtCardPx / C.EDGE_MM[vtEdge]).toFixed(2);

    for (const e of ['long', 'short']) {
        const b = document.getElementById('vt-edge-' + e);
        if (b) b.className = 'flex-1 py-2 rounded-xl text-[11px] font-bold ' +
            (e === vtEdge ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600');
    }
}

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
