// ==========================================
// app-core.js — 공통 기반 (다른 app-*.js 파일들이 의존하는 것들)
// 반드시 다른 app-*.js보다 먼저 로드되어야 함 (index.html의 <script> 순서 참고)
// ==========================================

// ------------------------------------------
// 1. 상태 관리 (State Management)
// 전역 변수들을 하나의 객체로 묶어서 관리합니다.
// ------------------------------------------
const state = {
    lang: 'ko',              // 현재 언어
    stepIdx: 0,              // 고정 질문 인덱스
    aiResultData: null,      // 백내장 분석 원자료 {code, probability, twoEyes, eyes} — 언어 중립
    aiResultCode: "",        // 백내장 판독 코드 'risk'/'normal' (RAG 검색용)
    amslerResult: {},        // 암슬러 응답 {left: bool, right: bool} — 언어 중립
    opinionLang: "",         // AI 참고 정보를 생성한 언어 (언어를 바꾸면 재생성 안내)
    eyeBreakdown: [],        // 눈별 결과 [{side, probability, code}]
    asymmetric: false,       // 편측(한쪽 눈만) 위험 여부
    hasAmsler: false,        // 황반변성 이상 여부
    chatSymptoms: [],        // 수집된 증상들 (리포트용)
    symptomCodes: [],        // 증상 언어 중립 코드 (RAG 검색용)
    dynamicCount: 0,         // 젬마가 질문한 횟수
    maxDynamic: 1,           // 젬마 질문 최대 횟수
    chatHistory: [],         // 젬마에게 넘길 전체 대화 기록
    chatBusy: false,         // 문진 답변 처리 중 잠금 (중복 클릭 방지)
    step: 'step-intro'       // 검사 흐름의 현재 단계 (진행 표시용)
};

// ------------------------------------------
// 1-b. 리포트 표시 문자열 — 언어 중립 상태에서 '그릴 때' 만든다
//
// 왜 함수인가:
//   예전에는 분석이 끝난 시점의 언어로 완성된 문장을 state에 저장하고 리포트가 그걸
//   그대로 그렸다. 그래서 언어를 바꾸면 라벨만 번역되고 값은 이전 언어로 남아
//   영어 리포트 안에 "백내장 위험 단계 (정밀 검사 권장)", "오른쪽 눈 이상"이 섞였다.
//   원자료만 저장하고 표시 문자열은 매번 현재 언어로 만든다.
//
// 왜 '%'를 쓰지 않는가:
//   모델 출력은 보정(calibration)되지 않은 softmax 값이라 확률이 아니다
//   (data.js의 score_label 주석 참고). 결과 카드는 '%' 없이 'AI 위험 점수'로
//   표기하는데 리포트만 "(100%)"로 찍혀, 같은 값이 두 가지 의미로 읽혔다.
// ------------------------------------------

/** 백내장 결과를 현재 언어 문자열로. 원자료가 없으면 "-". */
function formatCataractResult() {
    const r = state.aiResultData;
    if (!r) return "-";
    const t = translations[state.lang];
    const text = t['ai_' + r.code] || r.code;
    const score = t.score_label || 'AI 특징 점수';   // 확률이 아니므로 x/100 특징 점수로 표기 (외부 리뷰)
    if (r.twoEyes) {
        const by = {};
        (r.eyes || []).forEach(e => { by[e.side] = e; });
        const lp = by.left ? by.left.probability : '-';
        const rp = by.right ? by.right.probability : '-';
        return `${text} · ${score} ${t.eye_left} ${lp}/100 / ${t.eye_right} ${rp}/100`;
    }
    return `${text} · ${score} ${r.probability}/100`;
}

/** 암슬러 결과(좌/우)를 현재 언어 문자열로. 아직 안 했으면 "-". */
function formatAmslerResult() {
    const r = state.amslerResult;
    if (!r || !Object.keys(r).length) return "-";
    const t = translations[state.lang];
    const L = !!r.left, R = !!r.right;
    return (L && R) ? (t.ams_result_bad || '양쪽 이상')
         : L ? (t.ams_result_left || '왼쪽 눈 이상')
         : R ? (t.ams_result_right || '오른쪽 눈 이상')
             : (t.ams_result_both || '양쪽 정상');
}

/** 문진 소견을 현재 언어 문자열 배열로. state.chatSymptoms에는 i18n 키가 들어 있다. */
function formatSymptoms() {
    const t = translations[state.lang];
    return (state.chatSymptoms || []).map(k => t[k] || k);
}

// 백엔드(llm.py)가 AI 오류를 정상 토큰과 구분하기 위해 붙이는 마커 — 프론트는 감지 시 에러 처리
const ERROR_MARKER = "⛔__ECERR__";

// 스트리밍 중 마커가 두 청크 경계에 걸쳐 쪼개지면(예: "⛔__E" | "CERR__") 완전한 마커가
// 아직 도착하지 않은 순간 부분 마커가 화면에 잠깐 노출될 수 있다. 마커 길이-1만큼
// 텍스트 끝을 보류해, 그 부분이 마커의 일부일 가능성이 없을 때만 화면에 반영한다.
function safeStreamDisplay(text, marker) {
    const maxOverlap = Math.min(marker.length - 1, text.length);
    for (let len = maxOverlap; len > 0; len--) {
        if (text.endsWith(marker.slice(0, len))) {
            return text.slice(0, text.length - len).split(marker).join('');
        }
    }
    return text.split(marker).join('');
}

// AI 스트리밍 응답(fetch Response)을 끝까지 읽는 공용 리더.
// app-report.js의 소견서/추가질문 두 곳에서 같은 루프가 중복되던 것을 추출.
// - 하트비트(제로폭 공백 U+200B)는 제거 → 실제 토큰이 올 때까지 로더 유지 가능
// - onUpdate(displayText): 실제 토큰이 도착할 때마다 화면 표시용 텍스트 전달
//   (마커가 청크 경계에 걸쳐 쪼개져도 safeStreamDisplay로 안전하게 가림)
// 반환: { text: 마커 제거된 최종 텍스트, hasError: ERROR_MARKER 감지 여부 }
async function readAiStream(response, onUpdate) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let fullText = '';
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const piece = decoder.decode(value, { stream: true }).replace(/\u200B/g, '');
        if (!piece) continue;
        fullText += piece;
        onUpdate(safeStreamDisplay(fullText, ERROR_MARKER));
    }
    return {
        text: fullText.split(ERROR_MARKER).join(''),   // 보류됐던 마지막 일부까지 포함해 최종 확정
        hasError: fullText.includes(ERROR_MARKER)
    };
}

// ------------------------------------------
// 2. 초기화 및 UI 제어 (UI & Navigation)
// ------------------------------------------
window.addEventListener('DOMContentLoaded', () => {
    // 1순위: 사용자가 이전에 직접 고른 언어(localStorage) → 기기/브라우저 언어와 무관하게 유지
    // 2순위: 브라우저 언어  3순위: 영어
    const saved = localStorage.getItem('ec_lang');
    const browser = (navigator.language || navigator.userLanguage || 'en').substring(0, 2);
    const lang = (saved && translations[saved]) ? saved
               : (translations[browser] ? browser : 'en');
    updateUI(lang);
    applyFontSize(loadFontLevel());   // 저장된 글자 크기 복원 + 버튼 활성 상태 동기화
    showTab('tab-test', false); // 네비 활성 상태 초기화 (포커스는 문서 맨 앞에 그대로 둔다)
});

function changeLanguage(lang) {
    updateUI(lang);
}

// ------------------------------------------
// 글자 크기 조절 (모바일 가독성) — html[data-font]에 단계(0~2)를 기록하고
// style.css가 단계별 root font-size를 정한다(Tailwind 텍스트 클래스가 rem 기반이라 전체가 함께 커짐).
// index.html <head>의 인라인 스크립트가 저장값을 먼저 적용해 첫 화면 깜빡임을 막는다.
// ------------------------------------------
const FONT_LEVEL_MAX = 2;

function loadFontLevel() {
    let v = 0;
    try { v = parseInt(localStorage.getItem('ec_font'), 10); } catch (e) { /* 저장소 차단(시크릿 모드 등) */ }
    return Number.isInteger(v) ? Math.min(Math.max(v, 0), FONT_LEVEL_MAX) : 0;
}

function applyFontSize(level) {
    document.documentElement.setAttribute('data-font', String(level));
    try { localStorage.setItem('ec_font', String(level)); } catch (e) { /* 저장 못 해도 이번 세션엔 적용 */ }
    const dec = document.getElementById('fs-dec'), inc = document.getElementById('fs-inc');
    if (dec) dec.disabled = level <= 0;
    if (inc) inc.disabled = level >= FONT_LEVEL_MAX;
    // 지도·시력검사 카드는 컨테이너 크기에 맞춰 그리므로 다시 계산시킨다
    if (typeof _map !== 'undefined' && _map) setTimeout(() => _map.invalidateSize(), 250);
    if (typeof vtRefreshCalibrationUI === 'function' && document.getElementById('vt-cardbox')) {
        setTimeout(vtRefreshCalibrationUI, 250);
    }
}

function changeFontSize(delta) {
    applyFontSize(Math.min(Math.max(loadFontLevel() + delta, 0), FONT_LEVEL_MAX));
}

function updateUI(lang) {
    state.lang = lang;
    localStorage.setItem('ec_lang', lang);   // 선택 언어 저장 → 새로고침/재방문 시 복원
    // 문서 언어도 함께 바꾼다 — 스크린리더 발음, 브라우저 번역 제안, CJK 폰트 선택이
    // 모두 이 속성을 본다. index.html에 lang="ko"로 박혀 있으면 6개국어가 전부 한국어로 읽힌다.
    document.documentElement.lang = lang;
    document.getElementById('lang-selector').value = lang;
    // 스크린리더·번역기·검색엔진이 실제 표시 언어를 알 수 있도록 <html lang>도 함께 바꾼다
    document.documentElement.setAttribute('lang', lang);

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) el.innerHTML = translations[lang][key];
    });

    // placeholder 등 속성 번역 (data-i18n-ph="키")
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
        const key = el.getAttribute('data-i18n-ph');
        if (translations[lang][key]) el.placeholder = translations[lang][key];
    });

    // 화면에 글자가 없는 요소(아이콘 버튼 등)의 스크린리더 라벨 번역 (data-i18n-aria="키").
    // 하드코딩된 aria-label은 6개 국어 앱에서 한 언어로 고정돼버린다.
    document.querySelectorAll('[data-i18n-aria]').forEach(el => {
        const key = el.getAttribute('data-i18n-aria');
        if (translations[lang][key]) el.setAttribute('aria-label', translations[lang][key]);
    });

    // 마우스 툴팁(title)도 번역 (data-i18n-title="키") — 글자 크기 버튼 묶음 등
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (translations[lang][key]) el.title = translations[lang][key];
    });

    renderStepProgress();   // "5단계 중 2단계" 라벨도 선택 언어로

    // 리포트 페이지 하단 지도 버튼 라벨만 현지화 (스타일은 디자인 유지)
    const mapBtn = document.getElementById('dynamic-map-btn');
    const mapBtnLabel = mapBtn?.querySelector('[data-i18n="map_btn"]');
    if (mapBtnLabel && translations[lang].map_btn) mapBtnLabel.textContent = translations[lang].map_btn;

    renderDiseases(lang);

    // data-i18n으로 덮이지 않는 '동적 생성' 문구들도 다시 그린다.
    // (리포트 게이트·해석·시력검사 안내는 JS가 textContent로 넣으므로
    //  언어만 바꾸면 이전 언어 문장이 그대로 남는다)
    if (typeof updateReportGate === 'function') updateReportGate();
    // 리포트의 '값'(백내장·암슬러·문진 소견)은 data-i18n으로 덮이지 않는다 —
    // 언어 중립 상태에서 현재 언어로 다시 만든다.
    if (typeof refreshReportResults === 'function') refreshReportResults();
    if (typeof refreshAiResultDisplay === 'function') refreshAiResultDisplay();
    // 암슬러 격자 안내(거리·보정)도 현재 언어로
    if (typeof renderAmslerGrid === 'function' && document.getElementById('amsler-box')) {
        renderAmslerGrid();
    }
    // 결과 화면의 사진 캡션
    const rpc = document.getElementById('result-photo-caption');
    if (rpc && translations[lang].result_photo_label) rpc.textContent = translations[lang].result_photo_label;
    const rpi = document.getElementById('result-photo');
    if (rpi && translations[lang].result_photo_label) rpi.alt = translations[lang].result_photo_label;
    if (typeof vtRefreshCalibrationUI === 'function' && document.getElementById('vt-cardbox')) {
        vtRefreshCalibrationUI();
    }
    if (typeof vtRefreshDynamicUI === 'function') vtRefreshDynamicUI();
    const findBox = document.getElementById('findings-box');
    if (findBox && findBox.children.length && typeof renderFindings === 'function') {
        renderFindings(findBox);
    }
    const triBox = document.getElementById('triage-box');
    if (triBox && triBox.children.length && state.triage && typeof renderTriage === 'function') {
        renderTriage(triBox, computeTriage({
            cataractCode: state.aiResultCode, amslerAbnormal: state.hasAmsler,
            symptomCodes: state.symptomCodes, symptomScore: state.symptomScore,
            redFlags: state.redFlags,
        }), computeRiskScore(state.riskAnswers || {}).factors);
    }
}

// moveFocus: 사용자가 탭을 눌러 이동한 경우에만 true.
// 첫 로드에서 포커스를 본문으로 옮겨버리면 첫 Tab이 '본문으로 건너뛰기'와 상단 네비를
// 통째로 건너뛴다 — 키보드 사용자가 네비에 닿을 수 없게 된다.
function showTab(tid, moveFocus = true) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    const target = document.getElementById(tid);
    if (target) target.classList.add('active');
    window.scrollTo(0, 0);

    // 상단/하단 네비 활성 상태 동기화 (data-tab 기준)
    document.querySelectorAll('[data-tab]').forEach(item => {
        item.classList.toggle('active', item.getAttribute('data-tab') === tid);
        // 시각적 하이라이트만으로는 스크린리더가 현재 위치를 알 수 없어 aria-current도 같이 준다
        if (item.getAttribute('data-tab') === tid) item.setAttribute('aria-current', 'page');
        else item.removeAttribute('aria-current');
    });

    // 본문 건너뛰기는 숨겨진 고정 탭이 아니라 현재 보이는 탭으로 이동해야 한다.
    const skipLink = document.querySelector('.skip-link');
    if (skipLink && target) skipLink.setAttribute('href', `#${tid}`);

    // 탭이 바뀌면 포커스도 새 화면으로 옮긴다(키보드/스크린리더 사용자가 길을 잃지 않도록).
    // tabindex="-1"이라 마우스 사용자에게 보이는 링은 생기지 않는다(:focus-visible만 표시).
    if (target && moveFocus) target.focus({ preventScroll: true });

    // 지도 탭이 보일 때 Leaflet 크기 재계산 (숨겨진 동안 0px로 깨지는 것 방지)
    if (tid === 'tab-map' && typeof ensureMap === 'function') ensureMap();

    // 검사 전에는 빈 리포트·PDF를 쓰지 못하게 게이팅
    // (app-polish의 토스트 안내 대신 이 인페이지 게이트를 쓴다 — 같은 말을 두 번 하지 않는다)
    if (tid === 'tab-report' && typeof updateReportGate === 'function') updateReportGate();

    // 시력검사 탭도 지도와 같은 이유 — 숨겨진 동안에는 부모 폭이 0이라 카드 크기를 계산할 수 없다.
    // 이 호출이 없으면 카드가 폭 0으로 그려져 '파란 박스가 안 보이는' 상태가 된다.
    if (tid === 'tab-vision' && typeof vtRefreshCalibrationUI === 'function') vtRefreshCalibrationUI();
    // 다른 탭으로 나가면 확대 잠금을 반드시 되돌린다 — 저시력 사용자에게 확대는 필수 기능이다
    else if (typeof vtLockViewport === 'function') vtLockViewport(false);
}

// 검사 흐름의 사용자 관점 단계 (인트로/로딩은 자체 단계가 아님)
const STEP_FLOW = ['step-guide', 'step-photo', 'step-ai-result', 'step-amsler', 'step-chat'];
// 분석 중에는 '사진 업로드' 단계에 머무는 것으로 표시
const STEP_ALIAS = { 'step-ai-loading': 'step-photo' };

function nextStep(sid) {
    document.querySelectorAll('.step-content').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(sid);
    if (!target) return;
    target.classList.add('active');
    state.step = sid;
    renderStepProgress();
    // 카드가 통째로 바뀌므로 스크롤을 위로 올려 새 내용의 시작점을 보여준다
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 상단 단계 표시(점 5개) 갱신. 인트로에서는 숨긴다.
function renderStepProgress() {
    const bar = document.getElementById('step-progress');
    if (!bar) return;
    const current = STEP_ALIAS[state.step] || state.step;
    const idx = STEP_FLOW.indexOf(current);
    if (idx < 0) { bar.classList.remove('show'); bar.innerHTML = ''; bar.setAttribute('aria-label', ''); return; }

    bar.classList.add('show');
    bar.innerHTML = '';
    for (let i = 0; i < STEP_FLOW.length; i++) {
        const dot = document.createElement('span');
        dot.className = 'sp-dot' + (i < idx ? ' done' : i === idx ? ' current' : '');
        bar.appendChild(dot);
    }
    const tmpl = translations[state.lang].step_progress || "Step {n} of {total}";
    bar.setAttribute('aria-label', tmpl.replace('{n}', idx + 1).replace('{total}', STEP_FLOW.length));
}

// 로고 클릭 — 새로고침(입력한 내용이 전부 날아감) 대신 첫 화면으로 돌아간다
function goHome() {
    resetScreeningState();
    nextStep('step-intro');
    showTab('tab-test');
}

/** Start a new screening session without carrying results or generated opinion over. */
function resetScreeningState() {
    state.aiResultData = null; state.aiResultCode = ''; state.eyeBreakdown = [];
    state.asymmetric = false; state.amslerResult = {}; state.hasAmsler = false;
    state.opinionRequest = null; state.opinionLang = ''; state.triage = null;
    const opinion = document.getElementById('gemma-opinion-text');
    if (opinion) { opinion.textContent = ''; opinion.classList.add('hidden'); }
    const stale = document.getElementById('opinion-stale'); if (stale) stale.classList.add('hidden');
    const consent = document.getElementById('consent-box'); if (consent) consent.classList.add('hidden');
    const findings = document.getElementById('findings-box'); if (findings) findings.innerHTML = '';
    const triage = document.getElementById('triage-box'); if (triage) triage.innerHTML = '';
}

function openMap() {
    if (state.lang === 'ko') window.open('https://map.kakao.com/?q=안과', '_blank');
    else window.open('https://www.google.com/maps/search/eye+clinic+near+me', '_blank');
}

// ------------------------------------------
// AI 로딩 인디케이터 (타이핑 점 3개 + 실시간 경과 시간)
// 사용: const loader = createAiLoader("소견서 작성 중"); el에 loader.el 삽입;
//       응답 도착 시 loader.stop() (타이머 정지 + DOM 제거)
// app-chat.js, app-report.js에서 공용으로 사용
// ------------------------------------------
function createAiLoader(label) {
    const wrap = document.createElement('div');
    wrap.className = 'ai-loading';

    const dots = document.createElement('span');
    dots.className = 'ai-dots';
    for (let i = 0; i < 3; i++) dots.appendChild(document.createElement('span'));

    const labelEl = document.createElement('span');
    labelEl.className = 'al-label';
    labelEl.textContent = (label || '').replace(/\n/g, ' ').trim();

    const elapsedEl = document.createElement('span');
    elapsedEl.className = 'al-elapsed';
    const tmpl = translations[state.lang].loading_elapsed || "{s}초 경과";
    elapsedEl.textContent = tmpl.replace('{s}', '0.0');

    wrap.appendChild(dots);
    wrap.appendChild(labelEl);
    wrap.appendChild(elapsedEl);

    const t0 = performance.now();
    const timer = setInterval(() => {
        const sec = ((performance.now() - t0) / 1000).toFixed(1);
        elapsedEl.textContent = tmpl.replace('{s}', sec);
    }, 100);

    return {
        el: wrap,
        stop() {
            clearInterval(timer);
            wrap.remove();
        }
    };
}

// HTML 이스케이프 — app-report.js(PDF 본문), app-map.js(병원 목록)에서 공용으로 사용
function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ------------------------------------------
// 인앱 토스트 알림 (alert() 대체)
// alert()은 모바일에서 화면 전체를 막고 디자인과 따로 놀며, 페이지 전환과 겹치면
// 사용자가 두 번 탭해야 넘어간다. 같은 자리에 뜨는 카드로 바꿔 흐름을 끊지 않는다.
// 아이콘은 기기마다 모양이 달라지는 이모지 대신 선형 SVG (앱 전체 아이콘 규칙과 동일).
// type: 'info' | 'error' | 'success'
// ------------------------------------------
const TOAST_MAX = 3;
const TOAST_ICONS = {
    error:   '<svg viewBox="0 0 24 24" fill="none"><path d="M12 8.5v4.2M12 16.2h.01"/><path d="M10.3 3.9 2.7 17.1A2 2 0 0 0 4.4 20h15.2a2 2 0 0 0 1.7-2.9L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>',
    success: '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9"/><path d="m8 12.3 2.7 2.7L16 9.7"/></svg>',
    info:    '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.8h.01"/></svg>'
};

function showToast(message, type = 'info', duration = 4500) {
    const host = document.getElementById('toast-host');
    if (!host) { console.warn(message); return; }

    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    const icon = document.createElement('span');
    icon.className = 'toast-ico';
    icon.setAttribute('aria-hidden', 'true');
    icon.innerHTML = TOAST_ICONS[type] || TOAST_ICONS.info;   // 고정 상수라 주입 위험 없음
    const text = document.createElement('span');
    text.className = 'toast-msg';
    text.textContent = message;                               // 서버/사용자 문자열은 항상 textContent
    el.appendChild(icon);
    el.appendChild(text);

    let timer = null;
    const dismiss = () => {
        if (timer) { clearTimeout(timer); timer = null; }
        el.classList.add('leaving');
        // 퇴장 애니메이션이 끝나면 제거 (애니메이션이 꺼져 있어도 fallback 타이머로 정리)
        el.addEventListener('animationend', () => el.remove(), { once: true });
        setTimeout(() => el.remove(), 400);
    };
    el.addEventListener('click', dismiss);

    host.appendChild(el);
    // 오래된 토스트가 쌓이면 화면을 가리므로 최신 것만 남긴다
    while (host.children.length > TOAST_MAX) host.firstElementChild.remove();
    timer = setTimeout(dismiss, duration);
    return dismiss;
}

// 버튼을 "처리 중" 상태로 잠근다(중복 클릭 방지 + 진행 중임을 알림).
// 반환된 함수를 호출하면 원래 라벨·상태로 되돌린다.
function setButtonBusy(btn, busyLabel) {
    if (!btn) return () => {};
    const prevHTML = btn.innerHTML;
    const prevDisabled = btn.disabled;
    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');
    btn.innerHTML = '';
    const spinner = document.createElement('span');
    spinner.className = 'btn-spinner';
    spinner.setAttribute('aria-hidden', 'true');
    btn.appendChild(spinner);
    if (busyLabel) btn.appendChild(document.createTextNode(busyLabel));
    return () => {
        btn.innerHTML = prevHTML;
        // 처리 중 언어가 바뀌었을 수 있으므로 저장 당시 문구가 아닌 현재 언어로 복원한다.
        const textNodes = btn.matches('[data-i18n]')
            ? [btn, ...btn.querySelectorAll('[data-i18n]')]
            : [...btn.querySelectorAll('[data-i18n]')];
        textNodes.forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (translations[state.lang][key]) el.innerHTML = translations[state.lang][key];
        });
        const ariaNodes = btn.matches('[data-i18n-aria]')
            ? [btn, ...btn.querySelectorAll('[data-i18n-aria]')]
            : [...btn.querySelectorAll('[data-i18n-aria]')];
        ariaNodes.forEach(el => {
            const key = el.getAttribute('data-i18n-aria');
            if (translations[state.lang][key]) el.setAttribute('aria-label', translations[state.lang][key]);
        });
        btn.disabled = prevDisabled;
        btn.removeAttribute('aria-busy');
    };
}
