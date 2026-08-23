// ==========================================
// app-disease.js — 질환 소개 카드 + 상세 모달 (Disease Cards & Modal)
// app-core.js가 먼저 로드되어야 함 (state 사용)
// ==========================================

// 질환별 색상 테마 (인덱스 순서: 백내장 / 황반변성 / 녹내장 / 당뇨망막병증)
// 언어와 무관하게 질환 순서가 동일하므로 인덱스로 매핑합니다.
const DISEASE_THEME = [
    { accent: "#3b82f6", soft: "#eff6ff", grad: "#155eef" }, // 백내장
    { accent: "#d97706", soft: "#fffbeb", grad: "#b86508" }, // 황반변성
    { accent: "#7c3aed", soft: "#f5f3ff", grad: "#6840ba" }, // 녹내장
    { accent: "#dc354f", soft: "#fef2f2", grad: "#c83349" }  // 당뇨망막병증
];
function getDiseaseTheme(idx) { return DISEASE_THEME[idx] || DISEASE_THEME[0]; }

// 고정 SVG 아이콘 — 운영 UI에서 기기마다 다르게 보이는 이모지를 사용하지 않습니다.
const DISEASE_ICONS = [
    `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M2.8 12s3.5-5.2 9.2-5.2 9.2 5.2 9.2 5.2-3.5 5.2-9.2 5.2S2.8 12 2.8 12Z"/><circle cx="12" cy="12" r="3.4"/><path d="M10.2 10.2l3.6 3.6" opacity=".45"/></svg>`,
    `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><path d="m15 9 4-4M16.5 5H19v2.5"/></svg>`,
    `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="5.5"/><circle cx="12" cy="12" r="2.2"/></svg>`,
    `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3.5c2.7 3.2 6 6.6 6 10.3a6 6 0 0 1-12 0c0-3.7 3.3-7.1 6-10.3Z"/><path d="M12 8v8M12 11l-3-2M12 13l3-2M12 15l-2 2"/></svg>`
];
function getDiseaseIcon(idx) { return DISEASE_ICONS[idx] || DISEASE_ICONS[0]; }

function renderDiseases(lang) {
    const l = document.getElementById('disease-list');
    // 데이터는 data.js의 diseaseData에서 관리합니다
    const moreLabel = translations[lang].dis_more || "자세히 보기 →";
    const aiBadge = translations[lang].dis_ai_badge || "AI 분석 지원";
    l.innerHTML = diseaseData[lang].map((item, idx) => {
        const th = getDiseaseTheme(idx);
        // 백내장(idx 0)만 실제 이미지 AI 분석 대상이라 배지를 표시합니다.
        const badge = idx === 0
            ? `<span class="dc-badge">${aiBadge}</span>` : '';
        // role="button" + tabindex — <button>으로 감싸면 안의 <h3>/<p>가 버튼의 허용 자식이
        // 아니라 마크업이 깨진다. 대신 키보드(Enter/Space)를 아래 keydown에서 직접 처리한다.
        return `<div class="disease-card" role="button" tabindex="0" aria-haspopup="dialog"
                     onclick="openDisease(${idx})" style="--accent:${th.accent};--soft:${th.soft}">
            <div class="dc-head">
                <span class="dc-ico" aria-hidden="true">${getDiseaseIcon(idx)}</span>
                <div class="dc-head-text">
                    <h3>${item.t}</h3>
                    ${badge}
                </div>
            </div>
            <p>${item.d}</p>
            <p class="dc-more" aria-hidden="true">${moreLabel}</p>
        </div>`;
    }).join('');
}

// 카드가 매 언어 전환마다 새로 그려지므로, 리스트 컨테이너에 한 번만 위임 등록한다.
window.addEventListener('DOMContentLoaded', () => {
    const list = document.getElementById('disease-list');
    if (!list) return;
    list.addEventListener('keydown', e => {
        const card = e.target.closest('.disease-card');
        if (!card) return;
        if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
            e.preventDefault();     // Space로 페이지가 스크롤되는 것 방지
            card.click();
        }
    });
});

function openDisease(idx) {
    const lang = state.lang;
    const item = diseaseData[lang][idx];
    if (!item) return;

    document.getElementById('dm-icon').innerHTML = getDiseaseIcon(idx);
    document.getElementById('dm-title').textContent = item.t;

    // 질환 색상 테마를 모달 헤더에 적용
    const th = getDiseaseTheme(idx);
    const head = document.querySelector('#dm-card .dm-head');
    if (head) head.style.background = th.grad;
    const card = document.getElementById('dm-card');
    card.style.setProperty('--accent', th.accent);
    card.style.setProperty('--soft', th.soft);

    const labels = translations[lang];
    const note = labels.dis_modal_note || "이런 증상이 의심되면 안과 검진을 받아보세요.";
    const media = diseaseMedia[idx];
    const detail = document.getElementById('dm-detail');
    detail.innerHTML = '';

    if (media) {
        const figure = document.createElement('figure');
        figure.className = 'dm-figure';

        // 촬영 방식을 구분해 표시한다. 백내장·급성 폐쇄각 녹내장은 겉에서 보이지만,
        // 황반변성·당뇨망막병증은 눈 안쪽 망막 병변이라 안저촬영(병원 장비)이 있어야 보인다.
        // 라벨이 넷 다 '임상 참고 이미지'로 같으면 폰 사진으로 넷 다 판별된다고 읽힌다.
        const imageLabel = document.createElement('span');
        imageLabel.className = 'dm-image-label dm-image-label-' + (media.kind || 'external');
        imageLabel.textContent = (media.kind === 'fundus'
            ? labels.dis_modal_image_fundus
            : labels.dis_modal_image_external) || labels.dis_modal_image || 'Clinical reference image';

        const img = document.createElement('img');
        img.className = 'dm-clinical-image';
        img.src = media.src;
        img.alt = item.caption;
        img.loading = 'eager';
        img.decoding = 'async';

        const figcaption = document.createElement('figcaption');
        const caption = document.createElement('p');
        caption.textContent = item.caption;

        const imageNote = document.createElement('p');
        imageNote.className = 'dm-image-note';
        imageNote.textContent = labels.dis_modal_image_note || 'For education only. A photo alone cannot diagnose a condition.';

        const sourceLink = document.createElement('a');
        sourceLink.href = media.page;
        sourceLink.target = '_blank';
        sourceLink.rel = 'noopener';
        sourceLink.textContent = `${labels.dis_modal_image_source || 'Image source'}: ${media.credit} ↗`;

        const licenseLink = document.createElement('a');
        licenseLink.href = media.licenseUrl;
        licenseLink.target = '_blank';
        licenseLink.rel = 'noopener license';
        licenseLink.textContent = `${labels.dis_modal_license || 'License'}: ${media.license} ↗`;

        const licenseLinks = document.createElement('div');
        licenseLinks.className = 'dm-license-links';
        licenseLinks.append(sourceLink, licenseLink);

        figcaption.append(caption, imageNote);
        // 안저사진이면 '왜 겉으로는 안 보이는지'까지 덧붙인다 —
        // 이 앱의 사진 분석이 백내장만 다루는 이유와 직결된다.
        if (media.kind === 'fundus' && labels.dis_modal_image_fundus_note) {
            const why = document.createElement('p');
            why.className = 'dm-image-note';
            why.textContent = labels.dis_modal_image_fundus_note;
            figcaption.appendChild(why);
        }
        if (media.change === 'reencoded' && labels.dis_modal_image_change_reencoded) {
            const changeNote = document.createElement('p');
            changeNote.className = 'dm-image-note';
            changeNote.textContent = labels.dis_modal_image_change_reencoded;
            figcaption.appendChild(changeNote);
        }
        figcaption.appendChild(licenseLinks);

        figure.append(imageLabel, img, figcaption);
        detail.appendChild(figure);
    }

    const intro = document.createElement('p');
    intro.className = 'dm-intro';
    intro.textContent = item.detail || item.d;
    detail.appendChild(intro);

    const infoGrid = document.createElement('div');
    infoGrid.className = 'dm-info-grid';

    const symptomSection = document.createElement('section');
    symptomSection.className = 'dm-section';
    const symptomTitle = document.createElement('h3');
    symptomTitle.textContent = labels.dis_modal_symptoms || 'Common symptoms';
    const symptomList = document.createElement('ul');
    (item.symptoms || []).forEach(symptom => {
        const li = document.createElement('li');
        li.textContent = symptom;
        symptomList.appendChild(li);
    });
    symptomSection.append(symptomTitle, symptomList);

    const riskSection = document.createElement('section');
    riskSection.className = 'dm-section';
    const riskTitle = document.createElement('h3');
    riskTitle.textContent = labels.dis_modal_risk || 'Risk factors';
    const riskText = document.createElement('p');
    riskText.textContent = item.risk;
    riskSection.append(riskTitle, riskText);
    infoGrid.append(symptomSection, riskSection);
    detail.appendChild(infoGrid);

    const careSection = document.createElement('section');
    careSection.className = 'dm-section dm-care';
    const careTitle = document.createElement('h3');
    careTitle.textContent = labels.dis_modal_care || 'Exams and treatment';
    const careText = document.createElement('p');
    careText.textContent = item.care;
    careSection.append(careTitle, careText);
    detail.appendChild(careSection);

    if (item.urgent) {
        const urgentSection = document.createElement('section');
        urgentSection.className = 'dm-urgent';
        const urgentTitle = document.createElement('h3');
        urgentTitle.textContent = labels.dis_modal_urgent || 'When to seek prompt care';
        const urgentText = document.createElement('p');
        urgentText.textContent = item.urgent;
        urgentSection.append(urgentTitle, urgentText);
        detail.appendChild(urgentSection);
    }

    const noteDiv = document.createElement('div');
    noteDiv.className = 'dm-note';
    noteDiv.textContent = note;
    detail.appendChild(noteDiv);

    if (item.source) {
        const sourceLink = document.createElement('a');
        sourceLink.className = 'dm-source-link';
        sourceLink.href = item.source;
        sourceLink.target = '_blank';
        sourceLink.rel = 'noopener';
        sourceLink.textContent = `${labels.dis_modal_source || 'Official condition guide'} · National Eye Institute ↗`;
        detail.appendChild(sourceLink);
    }

    openDiseaseModal();
}

// ------------------------------------------
// 모달 접근성 — 열기 전 포커스 기억, 뒤 배경 스크롤 잠금, ESC 닫기, 포커스 가두기
// ------------------------------------------
let _lastFocused = null;

function openDiseaseModal() {
    _lastFocused = document.activeElement;
    document.getElementById('disease-modal').classList.add('show');
    // display:none 상태에서는 scrollTop 초기화가 무시될 수 있으므로 표시한 뒤 맨 위로 이동한다.
    const modalBody = document.querySelector('#dm-card .dm-body');
    if (modalBody) modalBody.scrollTop = 0;
    // 모달이 열린 동안 뒤 페이지가 스크롤되면 어디를 보고 있었는지 잃어버린다
    document.body.classList.add('modal-open');
    const closeBtn = document.querySelector('#dm-card .dm-close');
    if (closeBtn) closeBtn.focus();
}

function closeDisease(e) {
    // 오버레이 배경 클릭 또는 닫기 버튼(인자 없음)일 때만 닫기
    if (e && e.target && e.target.id !== 'disease-modal') return;
    document.getElementById('disease-modal').classList.remove('show');
    document.body.classList.remove('modal-open');
    // 모달을 연 카드로 포커스를 돌려준다 (키보드 사용자가 목록 맨 위로 튕기지 않도록)
    if (_lastFocused && document.contains(_lastFocused)) _lastFocused.focus();
    _lastFocused = null;
}

function isDiseaseModalOpen() {
    const m = document.getElementById('disease-modal');
    return !!m && m.classList.contains('show');
}

document.addEventListener('keydown', e => {
    if (!isDiseaseModalOpen()) return;

    if (e.key === 'Escape') { closeDisease(); return; }

    // Tab이 모달 밖(뒤에 가려진 페이지)으로 새어나가지 않게 순환시킨다
    if (e.key !== 'Tab') return;
    const focusables = document.querySelectorAll('#dm-card button, #dm-card a[href], #dm-card [tabindex]:not([tabindex="-1"])');
    if (!focusables.length) return;
    const first = focusables[0], last = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
});
