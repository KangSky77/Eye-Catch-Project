// ==========================================
// calibration.js — 화면 물리 크기 캘리브레이션 + 시각 자극 크기 계산
//
// 왜 필요한가:
//   시력·대비감도는 자극의 "시야각"(= 실제 크기 ÷ 보는 거리)으로 결정된다.
//   그런데 브라우저는 화면의 물리적 mm를 모른다 — CSS px는 기기마다 실제 크기가 다르다.
//   그래서 폰마다 결과가 달라지는 문제가 생긴다(팀 내에서 제기된 우려).
//
// 어떻게 푸는가:
//   1) 화면 px/mm  → 신용카드로 캘리브레이션.
//      신용카드는 ISO/IEC 7810 ID-1 규격으로 85.60 x 53.98 mm 고정이라
//      전 세계 어느 카드든 동일한 기준자가 된다. 화면에 사각형을 띄우고
//      실물 카드와 크기를 맞추게 하면 그 기기의 px/mm가 정확히 나온다.
//   2) 보는 거리 → 사용자가 고정 거리를 지키게 안내(+ 향후 전면카메라 IPD 추정).
//
//   두 값이 있으면 임의의 시력/대비 자극을 "물리적으로 정확한 크기"로 그릴 수 있다.
//
// 이 파일은 순수 계산 + 저장만 담당한다(DOM 조작 없음) — 테스트·재사용이 쉽도록.
// ==========================================

// ISO/IEC 7810 ID-1 — 신용/체크카드, 주민등록증, 운전면허증이 모두 이 규격
const CARD_WIDTH_MM = 85.60;
const CARD_HEIGHT_MM = 53.98;

const STORE_KEY = 'ec_calibration';

// ------------------------------------------------------------------
// 캘리브레이션 값 저장/복원
// ------------------------------------------------------------------

/** 저장된 캘리브레이션을 반환. 없으면 null. */
function loadCalibration() {
    try {
        const raw = localStorage.getItem(STORE_KEY);
        if (!raw) return null;
        const c = JSON.parse(raw);
        // pxPerMm가 상식 범위를 벗어나면(구버전/손상) 무시
        if (!(c.pxPerMm > 1 && c.pxPerMm < 30)) return null;
        return c;
    } catch (e) {
        return null;
    }
}

/**
 * 카드의 어느 변을 기준으로 맞출지.
 * 폰 세로 모드는 화면 폭이 보통 68~72mm라 카드 긴 변(85.6mm)이 물리적으로 안 들어간다.
 * 그래서 좁은 화면에서는 짧은 변(53.98mm)을 기준으로 맞추게 한다.
 */
const EDGE_MM = { long: CARD_WIDTH_MM, short: CARD_HEIGHT_MM };

/** 화면 폭에 카드 긴 변이 들어갈 만한지 대략 판단 — 기준 변 자동 선택용. */
function suggestEdge(viewportPx, assumedPxPerMm = 6.5) {
    // 여백까지 고려해 긴 변이 화면 폭의 80% 안에 들어와야 편하게 맞출 수 있다
    return (CARD_WIDTH_MM * assumedPxPerMm) < viewportPx * 0.8 ? 'long' : 'short';
}

/** 카드 맞추기 결과(화면상 해당 변의 px)로부터 캘리브레이션을 저장. */
function saveCalibration(matchedPx, distanceMm, edge = 'long') {
    const refMm = EDGE_MM[edge] || CARD_WIDTH_MM;
    const c = {
        pxPerMm: matchedPx / refMm,
        edge: edge,
        matchedPx: matchedPx,
        cardWidthPx: (matchedPx / refMm) * CARD_WIDTH_MM,   // 긴 변 환산(하위 호환)
        distanceMm: distanceMm,
        // devicePixelRatio를 같이 남겨둔다 — 기기가 바뀌면 재캘리브레이션이 필요함을 감지
        dpr: window.devicePixelRatio || 1,
        screen: `${window.screen.width}x${window.screen.height}`,
        savedAt: new Date().toISOString(),
    };
    // 저장 실패(사이트 데이터 차단·용량 초과)해도 이번 세션의 보정값은 그대로 쓴다 —
    // 여기서 예외가 나가면 시력검사 카드 맞추기가 통째로 중단된다(app-visiontest.js).
    // 읽기(loadCalibration)는 이미 try/catch로 감싸져 있었는데 쓰기만 빠져 있었다.
    try { localStorage.setItem(STORE_KEY, JSON.stringify(c)); } catch (e) { /* 이번 세션에만 적용 */ }
    return c;
}

/** 저장 당시와 다른 기기/해상도면 true — 재캘리브레이션을 권해야 한다. */
function calibrationStale(c) {
    if (!c) return true;
    return c.dpr !== (window.devicePixelRatio || 1)
        || c.screen !== `${window.screen.width}x${window.screen.height}`;
}

// ------------------------------------------------------------------
// 시야각 ↔ 물리 크기 변환
// ------------------------------------------------------------------

/**
 * 시야각(분, arcmin)에 해당하는 물리 크기(mm).
 *   size = 2 * d * tan(angle / 2)
 * 작은 각도라 근사해도 되지만, 큰 자극(대비감도용 큰 글자)도 정확하도록 tan을 그대로 쓴다.
 */
function arcminToMm(arcmin, distanceMm) {
    const rad = (arcmin / 60) * (Math.PI / 180);
    return 2 * distanceMm * Math.tan(rad / 2);
}

/** 물리 크기(mm) → 시야각(분). arcminToMm의 역함수. */
function mmToArcmin(mm, distanceMm) {
    const rad = 2 * Math.atan(mm / (2 * distanceMm));
    return (rad * 180 / Math.PI) * 60;
}

/**
 * 소수시력(decimal, 1.0 = 20/20) → 시표 전체 높이(mm).
 * 표준: 시력 1.0의 시표는 전체가 5분각(획 하나가 1분각)을 차지한다.
 * MAR(최소분리각) = 1 / 소수시력 이므로 전체 높이 = 5 * MAR 분각.
 */
function acuityToLetterMm(decimalAcuity, distanceMm) {
    const mar = 1 / decimalAcuity;          // arcmin
    return arcminToMm(5 * mar, distanceMm);
}

/** 소수시력 ↔ logMAR 변환 (logMAR 0.0 = 시력 1.0) */
const decimalToLogMAR = (d) => -Math.log10(d);
const logMARToDecimal = (l) => Math.pow(10, -l);

/** 이 기기·이 거리에서 물리적으로 표시 가능한 최소 시력(픽셀 한계). */
function maxDisplayableAcuity(pxPerMm, distanceMm, minLetterPx = 5) {
    // 시표가 minLetterPx보다 작아지면 픽셀 격자 때문에 형태가 무너진다
    const minMm = minLetterPx / pxPerMm;
    const arcmin = mmToArcmin(minMm, distanceMm);
    return 5 / arcmin;                       // 위 식의 역: acuity = 5 / (전체 분각)
}

// ------------------------------------------------------------------
// 대비 (Pelli-Robson 계열)
// ------------------------------------------------------------------

/**
 * Weber 대비 → sRGB 회색값. 배경은 흰색(255) 기준.
 *   C = (L_bg - L_target) / L_bg
 * 감마를 고려해 선형 광량에서 계산한 뒤 sRGB로 되돌린다.
 */
function contrastToGray(contrast) {
    const bgLin = 1.0;                       // 흰 배경의 선형 광량
    const targetLin = Math.max(0, bgLin * (1 - contrast));
    // sRGB 역감마 (근사식 2.2 대신 표준 sRGB 곡선)
    const s = targetLin <= 0.0031308
        ? targetLin * 12.92
        : 1.055 * Math.pow(targetLin, 1 / 2.4) - 0.055;
    return Math.round(Math.max(0, Math.min(1, s)) * 255);
}

/** 대비감도 = 1 / 대비. 로그 대비감도로 보고하는 것이 임상 관례(Pelli-Robson). */
const contrastToLogCS = (contrast) => Math.log10(1 / contrast);
const logCSToContrast = (logCS) => 1 / Math.pow(10, logCS);

// ------------------------------------------------------------------
// 정확도 안내용 — 거리 오차가 결과에 미치는 영향
// ------------------------------------------------------------------

/**
 * 거리를 err 비율만큼 잘못 알았을 때 시력 측정값의 logMAR 오차.
 * 시야각은 거리에 반비례하므로 시력도 그대로 비례해서 틀어진다.
 * (대비감도는 자극 크기를 고정하고 명암만 바꾸므로 이 오차에 훨씬 둔감하다)
 */
function distanceErrorToLogMAR(relativeError) {
    return Math.abs(Math.log10(1 + relativeError));
}

// 브라우저/노드 양쪽에서 쓸 수 있게 노출
if (typeof window !== 'undefined') {
    window.ECCalib = {
        CARD_WIDTH_MM, CARD_HEIGHT_MM, EDGE_MM, suggestEdge,
        loadCalibration, saveCalibration, calibrationStale,
        arcminToMm, mmToArcmin,
        acuityToLetterMm, decimalToLogMAR, logMARToDecimal, maxDisplayableAcuity,
        contrastToGray, contrastToLogCS, logCSToContrast,
        distanceErrorToLogMAR,
    };
}
