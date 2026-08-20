// ==========================================
// app-findings.js — 검사 결과의 '해석'을 코드가 결정론적으로 생성
// app-core.js가 먼저 로드되어야 함
//
// 왜 이 파일이 있는가:
//   해석을 LLM에게 맡겼더니 실제로 이런 문장이 나왔다(외부 리뷰에서 재현).
//     "암슬러 격자가 정상이므로 녹내장과 관련된 심각한 황반부 문제 가능성이 낮다"
//   암슬러는 황반 검사인데 녹내장 결론을 냈고, 선별검사로 질환을 배제했고,
//   질환 둘을 한 문장에 섞었다. RAG나 프롬프트 지시로는 이런 오류를 못 막는다.
//
//   그래서 의학적 해석은 전부 여기서 '고정 문장'으로 만든다. 조합만 달라질 뿐
//   문장 자체는 사람이 검수한 것이므로 새로운 오류가 생길 여지가 없다.
//   LLM은 생활 관리 조언만 담당한다(app/services/llm.py 참고).
//
// 문장을 고칠 때 지켜야 할 규칙:
//   - 검사가 실제로 본 것만 말한다 (암슬러 → 황반, 사진 → 수정체 겉모습)
//   - '가능성이 낮다', '안심하셔도 된다'로 질환을 배제하지 않는다
//   - 한 문장에서 서로 다른 질환을 연결짓지 않는다
//   - 점수를 확률처럼 말하지 않는다
// ==========================================

/** 현재 state로부터 안전한 해석 문장 목록을 만든다. */
function buildFindings() {
    const t = translations[state.lang];
    const out = [];

    // --- 백내장 사진 판독 ---
    if (state.aiResultCode === 'risk') out.push(t.find_cat_risk);
    else if (state.aiResultCode === 'borderline') out.push(t.find_cat_borderline);
    else if (state.aiResultCode === 'normal') out.push(t.find_cat_normal);
    if (state.asymmetric) out.push(t.find_cat_asym);

    // --- 암슬러(황반 자가검사) — 반드시 '황반만 본다'는 범위를 함께 말한다 ---
    if (state.hasAmsler) {
        const eye = state.amslerLabel || '';
        out.push((t.find_ams_abnormal || '').replace('{eye}', eye));
    } else if (state.amslerResult && Object.keys(state.amslerResult).length) {
        out.push(t.find_ams_normal);
    }

    // --- 기능검사(시력·대비감도) ---
    if (state.visionTest) {
        // 한쪽 눈이 아예 측정되지 않은 경우는 '차이 있음'과도 다른 상황이라 따로 안내한다
        if (state.visionTest.oneSideUnmeasurable) out.push(t.find_vt_unmeasurable);
        else out.push(state.visionTest.asymmetric ? t.find_vt_asym : t.find_vt_ok);
    }

    // --- 문진 ---
    if (state.chatSymptoms && state.chatSymptoms.length) {
        out.push((t.find_sym || '').replace('{items}', state.chatSymptoms.join(', ')));
    } else {
        out.push(t.find_nosym);
    }

    return out.filter(Boolean);
}

/** 해석 블록을 리포트에 그린다. */
function renderFindings(container) {
    const t = translations[state.lang];
    container.innerHTML = '';

    const head = document.createElement('p');
    head.className = 'text-[10px] font-black text-slate-400 mb-2';
    head.textContent = t.find_title || '검사 요약 해석';
    container.appendChild(head);

    const ul = document.createElement('ul');
    ul.className = 'space-y-2';
    buildFindings().forEach(text => {
        const li = document.createElement('li');
        li.className = 'text-[12px] text-slate-600 leading-relaxed flex gap-2';
        const dot = document.createElement('span');
        dot.className = 'text-slate-300';
        dot.textContent = '·';
        const body = document.createElement('span');
        body.textContent = text;          // 고정 문장이지만 textContent로 일관되게 삽입
        li.appendChild(dot);
        li.appendChild(body);
        ul.appendChild(li);
    });
    container.appendChild(ul);

    const note = document.createElement('p');
    note.className = 'text-[10px] text-slate-400 mt-3 leading-relaxed';
    note.textContent = t.find_disclaimer || '';
    container.appendChild(note);
}

// ------------------------------------------------------------------
// 검사 완료 여부 게이팅
// 검사하지 않은 사용자가 빈 PDF를 만들거나 맥락 없이 의료 질문을 보내는 것을 막는다.
// ------------------------------------------------------------------

/** 사진 분석과 문진을 모두 마쳤는가. */
function hasCompletedScreening() {
    return !!(state.aiResultCode && state.triage);
}

/** 리포트 탭 진입 시 호출 — 미완료면 안내 화면만 보여준다. */
function updateReportGate() {
    const done = hasCompletedScreening();
    const gate = document.getElementById('report-gate');
    const content = document.getElementById('report-content');
    const actions = document.getElementById('report-actions');
    if (!gate) return;

    gate.classList.toggle('hidden', done);
    if (content) content.classList.toggle('hidden', !done);
    if (actions) actions.classList.toggle('hidden', !done);

    const t = translations[state.lang];
    const title = document.getElementById('report-gate-title');
    const desc = document.getElementById('report-gate-desc');
    const btn = document.getElementById('report-gate-btn');
    if (title) title.textContent = t.gate_title || '';
    if (desc) desc.textContent = t.gate_desc || '';
    if (btn) btn.textContent = t.gate_go || '';
}
