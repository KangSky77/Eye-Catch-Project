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
    if (typeof hasSurgery === 'function' && hasSurgery()) {
        out.push(t.post_limit);
        // 문항 문장을 그대로 나열하면("가장 최근에 어떤 눈 수술을 받으셨나요?: 백내장")
        // 소견서가 아니라 답안지처럼 읽히고, 아래 '문진에서 확인된 항목'과 톤도 어긋난다.
        // 짧은 라벨로 한 줄에 모은다.
        const label = code => {
            const q = surgeryRiskQuestions.find(x => x.code === code);
            const opt = q && q.options.find(o => o.v === state.riskAnswers[code]);
            return opt ? t[opt.key] : '';
        };
        const parts = [
            t['surgery_' + state.riskAnswers.surgery],
            label('surgery_type'),
            label('surgery_eye') && t.post_eye_operated + ' ' + label('surgery_eye'),
            label('surgery_sym_eye') && t.post_eye_affected + ' ' + label('surgery_sym_eye'),
        ].filter(Boolean);
        if (parts.length) out.push((t.find_post_context || '{items}').replace('{items}', parts.join(' · ')));
    }
    if (state.riskAnswers?.surgery === 'past' && typeof remoteSurgeryLabels === 'function') {
        const parts = remoteSurgeryLabels();
        if (parts.length) out.push((t.find_remote_context || '{items}').replace('{items}', parts.join(' · ')));
    }

    // --- 백내장 사진 판독 ---
    // 수술 4주 이내면 건너뛴다. 위에서 post_limit로 '사진만으로는 판정할 수 없다'고
    // 이미 말했는데, 바로 아래에 '백내장 위험' 소견을 붙이면 그 말을 스스로 뒤집는다.
    const postop = typeof photoAssessmentExcluded === 'function' ? photoAssessmentExcluded() : (typeof hasSurgery === 'function' && hasSurgery());
    if (postop && !hasSurgery()) out.push(t.photo_history_limit);
    // 사진을 한 장도 받지 않은 회차는 '판독 제외'가 아니라 '판독 없음'이다.
    // 아무 줄도 남기지 않으면 사진 항목만 조용히 사라져 무엇이 빠졌는지 알 수 없다.
    //
    // 다만 위 hasSurgery() 블록이 이미 post_limit('사진이나 이 문진만으로는 판정할 수
    // 없습니다')을 내보냈다면 겹쳐 쓰지 않는다 — '사진 없이 증상 확인하기'로 들어와
    // 문진에서 '오늘 수술했습니다'를 고르면 같은 뜻의 두 줄이 나란히 찍혔다.
    // 우선순위는 formatCataractResult()와 같게 둔다(술후 문구 > 사진 없음).
    if (!hasSurgery() && ['postop', 'skipped'].includes(state.aiResultCode)) {
        out.push(state.aiResultCode === 'postop' ? t.post_limit : t.photo_skipped);
    }
    if (!postop) {
        // 반대쪽 눈만 판독한 경우, 아래 백내장 소견이 어느 눈에 대한 것인지 먼저 밝힌다.
        if (typeof fellowEyeAssessable === 'function' && fellowEyeAssessable()) out.push(t.find_cat_fellow);
        if (state.aiResultCode === 'risk') out.push(t.find_cat_risk);
        else if (state.aiResultCode === 'borderline') out.push(t.find_cat_borderline);
        else if (state.aiResultCode === 'uncertain') out.push(t.find_cat_uncertain);
        else if (state.aiResultCode === 'normal') out.push(t.find_cat_normal);
        if (state.asymmetric) out.push(t.find_cat_asym);
    }

    // --- 암슬러(황반 자가검사) — 반드시 '황반만 본다'는 범위를 함께 말한다 ---
    if (Object.values(state.amslerResult || {}).includes('unable')) out.push(t.ams_unable_note);
    if (state.hasAmsler) {
        const eye = formatAmslerResult();
        out.push((t.find_ams_abnormal || '').replace('{eye}', eye));
    } else if (typeof amslerComplete === 'function' && amslerComplete()) {
        // '좌우 모두 이상 없음'은 양쪽 눈을 다 본 뒤에만 할 수 있는 말이다.
        // 한쪽만 답한 상태에서 이 문장을 쓰면 검사하지 않은 눈까지 정상이라고 말하게 된다.
        out.push(t.find_ams_normal);
    }

    // --- 문진 ---
    if (state.chatSymptoms && state.chatSymptoms.length) {
        out.push((t.find_sym || '').replace('{items}', formatSymptoms().join(', ')));
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
    head.className = 'text-[10px] font-black text-slate-500 mb-2';
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
    note.className = 'text-[10px] text-slate-500 mt-3 leading-relaxed';
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
