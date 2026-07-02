// ==========================================
// app-vision.js — AI 비전 분석 (Vision AI)
// app-core.js가 먼저 로드되어야 함 (state, nextStep 등 사용)
// ==========================================
async function runAIAnalysis() {
    const fileInput = document.getElementById('cataract-file');
    const file = fileInput.files[0];
    if (!file) return;

    const r = new FileReader();
    r.onload = e => {
        const p = document.getElementById('preview-image');
        p.src = e.target.result;
        p.classList.remove('hidden');
    };
    r.readAsDataURL(file);
    nextStep('step-ai-loading');

    const fd = new FormData();
    fd.append('file', file);

    try {
        const res = await fetch('/api/analyze-eye', { method: 'POST', body: fd });
        const d = await res.json();
        if (!res.ok) {
            alert(`⚠️ ${d.detail || "Error"}`);
            nextStep('step-photo');
            return;
        }

        // 눈 사진이 아니라고 판단되면 의료 결과 대신 재촬영 안내
        if (d.result_code === 'invalid') {
            alert(translations[state.lang].ai_invalid || "눈 사진이 아닌 것 같아요. 눈을 가까이서 촬영한 사진을 올려주세요.");
            nextStep('step-photo');
            return;
        }

        // 백내장 결과를 선택 언어로 표시 (result_code 기반)
        const t = translations[state.lang];
        const resultText = t['ai_' + d.result_code] || d.result;
        state.aiResultCode = d.result_code;   // 언어 중립 코드 저장 (RAG 검색용)
        state.eyeBreakdown = d.eyes || [];
        state.asymmetric = !!d.asymmetric;

        // 얼굴 모드(눈 2개)면 좌/우 분리 결과를, 아니면 단일 결과를 리포트/소견서 문자열에 반영
        const twoEyes = d.mode === 'face' && Array.isArray(d.eyes) && d.eyes.length === 2;
        if (twoEyes) {
            const bySide = {}; d.eyes.forEach(e => bySide[e.side] = e);
            const lp = bySide.left ? bySide.left.probability : '-';
            const rp = bySide.right ? bySide.right.probability : '-';
            // 좌/우 수치 자체가 비대칭을 드러내므로 문자열은 간결하게(스키마 길이 제한 대비)
            state.aiResult = `${resultText} (${t.eye_left} ${lp}%, ${t.eye_right} ${rp}%)`;
        } else {
            state.aiResult = `${resultText} (${d.probability}%)`;
        }

        const disp = document.getElementById('ai-result-display');
        disp.innerHTML = '';
        const pProb = document.createElement('p');
        pProb.className = 'text-xs text-blue-700 font-black mb-1';
        pProb.textContent = `${d.probability}%`;
        const pRes = document.createElement('p');
        pRes.className = 'text-xl font-bold';
        pRes.textContent = resultText;
        disp.appendChild(pProb);
        disp.appendChild(pRes);

        // 눈별 분석 카드 (얼굴 모드 + 눈 2개일 때만)
        if (twoEyes) {
            renderEyeBreakdown(disp, d.eyes);
        } else if (d.mode === 'face' && d.eyes_detected > 0) {
            const pFace = document.createElement('p');
            pFace.className = 'text-[11px] text-slate-500 font-bold mt-2';
            const tmpl = t.face_mode_note || "👁 얼굴 사진에서 눈 {n}곳을 찾아 분석했어요.";
            pFace.textContent = tmpl.replace('{n}', d.eyes_detected);
            disp.appendChild(pFace);
        }

        setTimeout(() => nextStep('step-ai-result'), 1000);
    } catch (e) {
        alert(translations[state.lang].srv_err || "Server Connection Error");
        nextStep('step-photo');
    }
}

// 눈별(좌/우) 분석 결과 카드를 그린다 (얼굴 모드 + 눈 2개일 때).
function renderEyeBreakdown(container, eyes) {
    const t = translations[state.lang];
    const sideLabel = { left: t.eye_left, right: t.eye_right };

    const wrap = document.createElement('div');
    wrap.className = 'mt-4 pt-4 border-t border-slate-200 text-left';

    const title = document.createElement('p');
    title.className = 'text-[11px] font-black text-slate-400 mb-2';
    title.textContent = t.eye_breakdown_title || '눈별 분석';
    wrap.appendChild(title);

    // 판정 코드별 배지 색: 위험=장미색 / 경계=호박색 / 정상=에메랄드
    const codeStyle = {
        risk: 'bg-rose-100 text-rose-600',
        borderline: 'bg-amber-100 text-amber-600',
        normal: 'bg-emerald-100 text-emerald-600'
    };
    eyes.forEach(e => {
        const row = document.createElement('div');
        row.className = 'flex items-center justify-between py-1.5';
        const label = document.createElement('span');
        label.className = 'text-sm font-bold text-slate-600';
        label.textContent = `👁 ${sideLabel[e.side] || e.side}`;
        const val = document.createElement('span');
        val.className = `text-sm font-black px-2.5 py-0.5 rounded-full ${codeStyle[e.code] || codeStyle.normal}`;
        val.textContent = `${e.probability}%`;
        row.appendChild(label);
        row.appendChild(val);
        wrap.appendChild(row);
    });

    if (state.asymmetric) {
        const badge = document.createElement('p');
        badge.className = 'mt-2 text-[11px] font-black text-rose-600 bg-rose-50 rounded-lg px-3 py-2';
        badge.textContent = t.eye_unilateral || '⚠️ 편측 의심';
        wrap.appendChild(badge);
    }

    const note = document.createElement('p');
    note.className = 'mt-2 text-[10px] text-slate-400 leading-relaxed';
    note.textContent = t.eye_ref_note || '';
    wrap.appendChild(note);

    container.appendChild(wrap);
}

function recordAmsler(bad) {
    state.hasAmsler = bad; // 상태 업데이트
    nextStep('step-chat');
    startChat();
}
