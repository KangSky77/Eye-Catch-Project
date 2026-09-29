// Report follow-up requests and deterministic result explanation.
// Loaded after app-report.js; uses state and the shared stream reader.

let _followupBusy = false;
let _activeFollowup = null;

function cancelFollowup() {
    const active = _activeFollowup;
    _activeFollowup = null;
    _followupBusy = false;
    if (active) {
        active.controller.abort();
        active.loader.stop();
    }
    const sendBtn = document.getElementById('followup-send-btn');
    if (sendBtn) { sendBtn.disabled = false; sendBtn.removeAttribute('aria-busy'); }
    const explainBtn = document.getElementById('followup-explain-btn');
    if (explainBtn) explainBtn.disabled = false;
}

/** 챗봇이 '내 결과'를 알 수 있게 넘기는 문맥.
 *
 *  예전에는 AI 3줄 요약(생활 조언)만 넘겨서, "내 검사 결과를 쉽게 설명해 줘"라고 물으면 챗봇이 결과를
 *  모른 채 "실제 검사 기록을 확인해야 합니다"라고 답했다(2026-09-28 실측 2/2). 검사 해석은 앱이 코드로
 *  만든 고정 문장(buildFindings)을 그대로 넘긴다 — 챗봇은 그 문장을 쉬운 말로 풀어 줄 뿐 새로 판정하지 않는다.
 *  서버 스키마 상한(ChatRequest.context 5000자)에 맞춰 자른다 — 넘기면 422가 나서 '서버 연결 불가'로 오인된다. */
function buildChatContext() {
    const t = translations[state.lang];
    const parts = [];
    // 권장 조치의 이유 문구(why)는 넘기지 않는다. "경계 소견, 확인이 필요한 증상, 또는 미뤄진 검진"처럼
    // '셋 중 하나'를 뜻하는 일반 문장이라, 챗봇이 "경계 소견이 발견되었다"로 읽었다(2026-09-28 실측).
    // 실제로 해당하는 항목은 아래 검사 요약 해석에 들어 있다.
    if (state.triage) parts.push(`[${t.tri_title || 'Recommended action'}] ${state.triage.label || ''}`);
    // 검사 요약 해석에는 AI 맞춤 질문 답변 줄도 들어 있다(app-findings.js) — 따로 넣지 않는다.
    const findings = typeof buildFindings === 'function' ? buildFindings() : [];
    if (findings.length) parts.push(`[${t.find_title || 'Result summary'}]\n` + findings.map(line => '- ' + line).join('\n'));
    const riskAnswers = Object.fromEntries(['diabetes', 'hypertension', 'smoking', 'family']
        .filter(key => [true, false, 'unknown'].includes(state.riskAnswers?.[key]))
        .map(key => [key, state.riskAnswers[key]]));
    parts.push('[Structured risk answers: true=yes, false=no, unknown=not sure; missing=unanswered] ' + JSON.stringify(riskAnswers));
    const factors = computeRiskScore(state.riskAnswers || {}).factors || [];
    if (factors.length) parts.push(`[${t.chat_ctx_risk || 'Risk factors'}] ${factors.join(', ')}`);
    const summary = state.opinionSummaryText || document.getElementById('gemma-opinion-text')?.innerText || '';
    if (summary) parts.push(`[${t.chat_ctx_summary || 'AI 3-line summary'}]\n${summary}`);
    return parts.join('\n\n').slice(0, 5000);
}

/**
 * 결과 설명은 모든 검사 소견·한계와 권장 조치를 고정 문장표로 풀어 쓴다.
 * 단어가 모두 있어도 AI가 의미를 뒤집을 수 있어 자유 생성한 검사 해석은 사용하지 않는다.
 * 문장은 buildFindings()에 실제로 들어간 줄만 쓴다 — 수술 이력으로 사진 판독을 뺀 회차 등은 거기서 이미 걸러진다.
 */
function explainCheckPayload() {
    const t = translations[state.lang];
    const findings = typeof buildFindings === 'function' ? buildFindings({ includePersonal: false }) : [];
    const required = [];
    const fallback = [...findings];
    const photo = { risk: t.find_cat_risk, borderline: t.find_cat_borderline,
                    uncertain: t.find_cat_uncertain, normal: t.find_cat_normal }[state.aiResultCode];
    if (photo && findings.includes(photo)) {
        if (state.aiResultCode === 'risk' || state.aiResultCode === 'borderline') required.push('cat_' + state.aiResultCode);
    }
    const ams = (t.find_ams_abnormal || '').replace('{eye}', formatAmslerResult());
    if (state.hasAmsler && findings.includes(ams)) {
        const r = state.amslerResult || {};
        required.push(r.left === true && r.right === true ? 'ams_both' : r.left === true ? 'ams_left' : 'ams_right');
    }
    const level = state.triage?.level;
    if (state.triage?.label) {
        if (level === 'now' || level === 'weeks') required.push('tri_' + level);
        fallback.push(state.triage.label);
    }
    return { explain_required: required, explain_fallback: fallback };
}

/** '내 결과 쉽게 설명해 줘' 버튼 — 입력 없이 바로 묻는다. */
function askExplainResults() {
    const inputEl = document.getElementById('user-followup-input');
    if (!inputEl || _followupBusy) return;
    inputEl.value = translations[state.lang].rep_followup_explain || '';
    askGemmaMore(true);
}

async function askGemmaMore(explainResults = false) {
    if (state.triage?.level === 'urgent') return;
    if (_followupBusy) return;   // 답변 스트리밍 중 재전송 금지 (응답이 뒤섞이는 것 방지)

    const inputEl = document.getElementById('user-followup-input');
    const responseEl = document.getElementById('followup-response');
    const sendBtn = document.getElementById('followup-send-btn');
    const userMsg = inputEl.value.trim();

    if (!userMsg) { inputEl.focus(); return; }

    const context = buildChatContext();

    // 스트리밍 도중 새 검사가 시작되면(로고 클릭 등) 이 답변은 새 리포트의 것이 아니다.
    // 세대 번호를 찍어 두고 도착한 조각마다 같은 세션인지 확인한다.
    const generation = state.sessionGeneration;
    const lang = state.lang;
    const active = { controller: new AbortController(), loader: null };
    _activeFollowup = active;
    const isCurrent = () => _activeFollowup === active && state.sessionGeneration === generation && state.lang === lang;

    _followupBusy = true;
    if (sendBtn) { sendBtn.disabled = true; sendBtn.setAttribute('aria-busy', 'true'); }
    const explainBtn = document.getElementById('followup-explain-btn');
    if (explainBtn) explainBtn.disabled = true;
    inputEl.value = '';
    responseEl.classList.remove('hidden');
    responseEl.innerText = '';
    const loader = createAiLoader(translations[state.lang].followup_thinking || "답변을 생각하고 있습니다");
    active.loader = loader;
    responseEl.appendChild(loader.el);
    let firstChunk = true;

    try {
        const response = await fetch('/api/chat-with-gemma', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // facts: AI 소견 요청과 같은 사실 목록 — 서버 안전 필터가 이 사실과 어긋나는 문장을 지운다
            body: JSON.stringify({ lang: state.lang, user_msg: userMsg, context: context, explain_results: explainResults === true,
                                   facts: buildOpinionSymptoms(), ...(explainResults === true ? explainCheckPayload() : {}) }),
            signal: active.controller.signal
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        // 공용 스트림 리더(app-core.js) — 하트비트 무시·마커 분리 감지 처리 포함
        const { text, hasError } = await readAiStream(response, disp => {
            if (!isCurrent()) return;
            if (firstChunk) {       // 첫 실제 토큰 도착 → 로더 제거 후 답변 표시 시작
                loader.stop();
                firstChunk = false;
            }
            responseEl.innerText = `Q: ${userMsg}\nA: ` + disp;
        });
        loader.stop();              // 빈 응답이어도 로더는 정리
        if (!isCurrent()) return;   // 새 검사가 시작됐으면 이 답변은 버린다
        responseEl.innerText = `Q: ${userMsg}\nA: ` + text;
        const streamError = hasError;
        if (streamError) {          // AI 오류 → 에러 메시지로 대체
            responseEl.innerText = translations[state.lang].srv_err || "서버와 연결할 수 없습니다.";
            responseEl.classList.add('text-rose-600');
            return;
        }
        responseEl.classList.remove('text-rose-600');
        // 모델이 마크다운(**)을 섞어 보내는 경우 평문으로 정리
        responseEl.innerText = responseEl.innerText.replace(/\*\*/g, '');
    } catch (e) {
        loader.stop();
        if (!isCurrent()) return;
        responseEl.innerText = translations[state.lang].srv_err || "서버와 연결할 수 없습니다.";
    } finally {
        if (_activeFollowup === active) cancelFollowup();
    }
}

// 입력창에서 Enter로도 전송 (모바일 키보드의 '보내기' 포함)
window.addEventListener('DOMContentLoaded', () => {
    const inputEl = document.getElementById('user-followup-input');
    if (inputEl) {
        inputEl.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.isComposing) {   // isComposing: 한글/일본어 조합 중 Enter는 무시
                e.preventDefault();
                askGemmaMore();
            }
        });
    }
});
