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
    aiResult: "",            // 백내장 분석 결과
    aiResultCode: "",        // 백내장 판독 코드 'risk'/'normal' (RAG 검색용)
    eyeBreakdown: [],        // 눈별 결과 [{side, probability, code}]
    asymmetric: false,       // 편측(한쪽 눈만) 위험 여부
    hasAmsler: false,        // 황반변성 이상 여부
    chatSymptoms: [],        // 수집된 증상들 (리포트용)
    symptomCodes: [],        // 증상 언어 중립 코드 (RAG 검색용)
    dynamicCount: 0,         // 젬마가 질문한 횟수
    maxDynamic: 1,           // 젬마 질문 최대 횟수
    chatHistory: [],         // 젬마에게 넘길 전체 대화 기록
    chatBusy: false          // 문진 답변 처리 중 잠금 (중복 클릭 방지)
};

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
    showTab('tab-test'); // 네비 활성 상태 초기화
});

function changeLanguage(lang) {
    updateUI(lang);
}

function updateUI(lang) {
    state.lang = lang;
    localStorage.setItem('ec_lang', lang);   // 선택 언어 저장 → 새로고침/재방문 시 복원
    document.getElementById('lang-selector').value = lang;

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) el.innerHTML = translations[lang][key];
    });

    // placeholder 등 속성 번역 (data-i18n-ph="키")
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
        const key = el.getAttribute('data-i18n-ph');
        if (translations[lang][key]) el.placeholder = translations[lang][key];
    });

    // 리포트 페이지 하단 지도 버튼 라벨만 현지화 (스타일은 디자인 유지)
    const mapBtn = document.getElementById('dynamic-map-btn');
    if (mapBtn && translations[lang].map_btn) mapBtn.innerText = translations[lang].map_btn;

    renderDiseases(lang);
}

function showTab(tid) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    const target = document.getElementById(tid);
    if (target) target.classList.add('active');
    window.scrollTo(0, 0);

    // 상단/하단 네비 활성 상태 동기화 (data-tab 기준)
    document.querySelectorAll('[data-tab]').forEach(item => {
        item.classList.toggle('active', item.getAttribute('data-tab') === tid);
    });

    // 지도 탭이 보일 때 Leaflet 크기 재계산 (숨겨진 동안 0px로 깨지는 것 방지)
    if (tid === 'tab-map' && typeof ensureMap === 'function') ensureMap();
}

function nextStep(sid) {
    document.querySelectorAll('.step-content').forEach(s => s.classList.remove('active'));
    document.getElementById(sid).classList.add('active');
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
