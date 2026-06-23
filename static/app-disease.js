// ==========================================
// app-disease.js — 질환 소개 카드 + 상세 모달 (Disease Cards & Modal)
// app-core.js가 먼저 로드되어야 함 (state 사용)
// ==========================================

// 질환별 색상 테마 (인덱스 순서: 백내장 / 황반변성 / 녹내장 / 당뇨망막병증)
// 언어와 무관하게 질환 순서가 동일하므로 인덱스로 매핑합니다.
const DISEASE_THEME = [
    { accent: "#3b82f6", soft: "#eff6ff", grad: "linear-gradient(150deg, #6E86FF, #3D55D9)" }, // 백내장
    { accent: "#f59e0b", soft: "#fffbeb", grad: "linear-gradient(150deg, #FBBF24, #D97706)" }, // 황반변성
    { accent: "#8b5cf6", soft: "#f5f3ff", grad: "linear-gradient(150deg, #A78BFA, #7C3AED)" }, // 녹내장
    { accent: "#ef4444", soft: "#fef2f2", grad: "linear-gradient(150deg, #FB7185, #E11D48)" }  // 당뇨망막병증
];
function getDiseaseTheme(idx) { return DISEASE_THEME[idx] || DISEASE_THEME[0]; }

function renderDiseases(lang) {
    const l = document.getElementById('disease-list');
    // 데이터는 data.js의 diseaseData에서 관리합니다
    const moreLabel = translations[lang].dis_more || "자세히 보기 →";
    const aiBadge = translations[lang].dis_ai_badge || "AI 분석 지원";
    l.innerHTML = diseaseData[lang].map((item, idx) => {
        const th = getDiseaseTheme(idx);
        // 백내장(idx 0)만 실제 이미지 AI 분석 대상이라 배지를 표시합니다.
        const badge = idx === 0
            ? `<span class="dc-badge">✨ ${aiBadge}</span>` : '';
        return `<div class="disease-card" onclick="openDisease(${idx})" style="--accent:${th.accent};--soft:${th.soft}">
            <div class="dc-head">
                <span class="dc-ico">${item.i}</span>
                <div class="dc-head-text">
                    <h3>${item.t}</h3>
                    ${badge}
                </div>
            </div>
            <p>${item.d}</p>
            <p class="dc-more">${moreLabel}</p>
        </div>`;
    }).join('');
}

function openDisease(idx) {
    const lang = state.lang;
    const item = diseaseData[lang][idx];
    if (!item) return;

    document.getElementById('dm-icon').textContent = item.i;
    document.getElementById('dm-title').textContent = item.t;

    // 질환 색상 테마를 모달 헤더에 적용
    const th = getDiseaseTheme(idx);
    const head = document.querySelector('#dm-card .dm-head');
    if (head) head.style.background = th.grad;
    const card = document.getElementById('dm-card');
    card.style.setProperty('--accent', th.accent);
    card.style.setProperty('--soft', th.soft);

    const note = translations[lang].dis_modal_note || "이런 증상이 의심되면 안과 검진을 받아보세요.";
    const detailText = item.detail || item.d;

    const detail = document.getElementById('dm-detail');
    detail.innerHTML = '';
    const p = document.createElement('p');
    p.textContent = detailText;             // XSS 방지: textContent 사용
    const noteDiv = document.createElement('div');
    noteDiv.className = 'dm-note';
    noteDiv.textContent = '💡 ' + note;
    detail.appendChild(p);
    detail.appendChild(noteDiv);

    document.getElementById('disease-modal').classList.add('show');
}

function closeDisease(e) {
    // 오버레이 배경 클릭 또는 닫기 버튼(인자 없음)일 때만 닫기
    if (e && e.target && e.target.id !== 'disease-modal') return;
    document.getElementById('disease-modal').classList.remove('show');
}
