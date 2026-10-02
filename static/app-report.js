// ==========================================
// app-report.js — 리포트 화면 및 AI 소견 (Report & Opinion)
// app-core.js가 먼저 로드되어야 함 (state, createAiLoader, escapeHTML, safeStreamDisplay 등 사용)
// ==========================================
// 소견서로 보낼 chat_symptoms 목록을 만든다.
//
// 서버 스키마(app/schemas/ai.py)가 항목당 100자, 최대 30개다. 자유 답변을 그대로
// 넣었더니 한국어 두 문장(111자)에서 422가 났고, 프론트는 그걸 "로컬 AI 서버와
// 연결이 끊어졌습니다"로 표시했다 — 원인과 전혀 다른 안내다. 여기서 미리 맞춘다.
const OPINION_ITEM_MAX = 100;   // SymptomText Field(max_length=100)
const OPINION_LIST_MAX = 30;    // chat_symptoms Field(max_length=30)

function buildOpinionSymptoms() {
    const risk = computeRiskScore(state.riskAnswers || {});
    return []
        .concat(
            // 'Eye surgery:' 는 서버가 술후 전용 프롬프트를 고르는 신호다.
            //
            // 4주 이내(hasSurgery)일 때만 붙인다. 'past'에도 붙였더니 12년 전 라식을
            // 받은 30대에게 화면은 일반 검진인데 AI 소견만 "퇴원 지침을 철저히 준수하세요"가
            // 나왔다 — 같은 리포트 안에서 두 안내가 어긋난다.
            // 맨 앞에 두는 이유: 뒤에 두면 목록이 길 때 OPINION_LIST_MAX(30)에 잘려 나가
            // 조용히 일반 프롬프트로 돌아간다.
            (typeof hasSurgery === 'function' && hasSurgery())
                ? ['Eye surgery: ' + state.riskAnswers.surgery + ' / ' + translations[state.lang]['surgery_' + state.riskAnswers.surgery]] : [],
            // 오래된 수술 이력은 '술후 관리' 대상이 아니라 그냥 병력이다. 사실만 전달한다.
            (state.riskAnswers?.surgery === 'past')
                ? (typeof remoteSurgeryLabels === 'function'
                    ? remoteSurgeryLabels().map(item => 'Reported remote surgery: ' + item)
                    : [translations[state.lang].q_surgery + ': ' + translations[state.lang].surgery_past]) : [],
            // 부정 답변은 목록이 길어도 잘리지 않도록 앞에 둔다.
            ...(state.riskAnswers?.hypertension === false ? ['Hypertension: no'] : []),
            ...(state.riskAnswers?.diabetes === false ? ['Diabetes: no'] : []),
            // 챗봇 지시문이 비흡연자에게 '금연' 예시를 빼는 데 쓴다(llm._care_examples).
            ...(state.riskAnswers?.smoking === false ? ['Smoking: no'] : []),
            // '예'도 같은 형식으로 명시한다. 번역된 '당뇨' 한 단어만 보내면 소형 모델이 거의 무시해
            // 당뇨 환자에게 '규칙적인 생활 습관' 같은 일반론만 나왔다(2026-09-27: 명시 전 0/3 → 명시 후 3/4 혈당 관리).
            ...(state.riskAnswers?.diabetes === true ? ['Diabetes: yes'] : []),
            ...(state.riskAnswers?.hypertension === true ? ['Hypertension: yes'] : []),
            ...(state.riskAnswers?.smoking === true ? ['Smoking: yes'] : []),
            formatSymptoms(),
            ...(typeof hasSurgery === 'function' && hasSurgery()
                ? postoperativeQuestions.filter(q => [true, false, 'unknown'].includes(state.symptomAnswers?.[q.code]))
                    .map(q => {
                        const a = state.symptomAnswers[q.code], t = translations[state.lang];
                        return t[q.key] + ': ' + (a === 'unknown' ? t.chat_unknown : a ? t.chat_yes : t.chat_no);
                    })
                : []),
            ...(typeof hasSurgery === 'function' && hasSurgery()
                ? ['surgery_type','surgery_eye','surgery_sym_eye'].map(key => {
                    const q = surgeryRiskQuestions.find(q => q.code === key);
                    const opt = q.options.find(o => o.v === state.riskAnswers[key]);
                    return opt ? translations[state.lang][q.key] + ': ' + translations[state.lang][opt.key] : '';
                }) : []),
            risk.factors || [],
            (state.dynamicAnswers || []).map(item => `${item.q}: ${item.a}`),
            state.freeAnswers || [],
        )
        .filter(Boolean)
        .map(v => {
            const text = String(v).trim();
            // 자르는 편이 통째로 버리는 것보다 낫다 — 앞부분만으로도 생활 조언의 단서가 된다
            return text.length > OPINION_ITEM_MAX ? text.slice(0, OPINION_ITEM_MAX - 1) + '…' : text;
        })
        .slice(0, OPINION_LIST_MAX);
}

/** 문진 항목·위험요인의 언어 중립 코드. 서버가 '이 사람에게 해당하는 조언'만 선택지로 추린다(app/services/advice.py). */
function opinionFlagCodes() {
    return [
        ...(state.chatSymptoms || []).filter(k => /^sym_[a-z0-9_]+$/.test(k)),
        ...['diabetes', 'hypertension', 'smoking', 'family']
            .filter(k => state.riskAnswers?.[k] === true).map(k => 'risk_' + k),
        ...(state.riskAnswers?.age ? ['age_' + state.riskAnswers.age] : []),
        // 맞춤 질문에 '예'라고 답한 주제 → 그 답에 맞춘 조언이 선택지로 열린다(app/services/advice.py).
        ...(state.dynamicAnswers || [])
            .filter(item => item.value === true && /^[a-z_]{3,16}$/.test(item.question_id || ''))
            .map(item => 'ans_' + item.question_id),
    ].slice(0, 40);
}

async function finish() {
    // 리포트 진입은 알림 신청이 아니다. 권한 창이 진료 안내를 가리지 않게 한다.
    // 날짜만 저장하고 문구는 refreshReportResults가 현재 언어로 붙인다(예전엔 'ISSUED'만 영어로 남았다)
    const d = new Date();
    state.reportDate = `${d.getFullYear()}.${d.getMonth()+1}.${d.getDate()}`;

    refreshReportResults();
    const cataractRes = formatCataractResult();
    // 암슬러는 좌우를 따로 보므로 어느 쪽 눈인지까지 표기한다
    const amslerRes = formatAmslerResult();
    const symptoms = formatSymptoms();

    // 행동 권고 — 등급이 아니라 '언제 병원에 가야 하는가'를 먼저 보여준다
    const risk = computeRiskScore(state.riskAnswers || {});
    // 위험요인 문진과 자유 답변도 소견서의 생활 조언 근거로 전달한다. 기존에는 증상
    // 문항만 전달되어 사용자가 당뇨·흡연 등을 답해도 AI가 개인화할 수 없었다.
    const opinionSymptoms = buildOpinionSymptoms();
    state.triage = computeCurrentTriage();
    const triBox = document.getElementById('triage-box');
    if (triBox) renderTriage(triBox, state.triage, risk.factors);

    // 검사 결과 '해석'은 코드가 고정 문장으로 생성한다 — LLM은 생활 조언만 담당
    const findBox = document.getElementById('findings-box');
    if (findBox && typeof renderFindings === 'function') renderFindings(findBox);

    showTab('tab-report');

    // 소견서 생성은 실패해도 처음부터 다시 하지 않고 이 부분만 재시도할 수 있어야 한다.
    // (개발 중 --reload 서버 재시작, ngrok 끊김, Ollama 콜드스타트 등으로 흔히 끊긴다)
    state.opinionRequest = {
        lang: state.lang,
        cataract_res: cataractRes,
        amsler_res: amslerRes,
        chat_symptoms: opinionSymptoms,
        // RAG용 언어 중립 신호
        cataract_code: typeof effectiveCataractCode === 'function' ? effectiveCataractCode() : state.aiResultCode,
        amsler_abnormal: state.hasAmsler,
        symptom_codes: state.symptomCodes,
        eye_asymmetric: (typeof photoAssessmentExcluded !== 'function' || !photoAssessmentExcluded()) && state.asymmetric,
        // 응급 신호를 같이 넘긴다. 안 넘기면 서버 프롬프트가 이 회차가 응급인지 알 수 없어,
        // 화면이 '지금 바로 진료를 받으세요'라고 띄운 바로 밑에 '정기 검진을 받아보세요'가 붙는다.
        red_flags: state.redFlags || [],
        // 권장 조치는 앱이 결정론적으로 정한다(computeTriage). LLM에게 알려주지 않으면
        // 제 나름의 판단을 해서 같은 화면 안에서 두 안내가 어긋난다 — 실제로 카드는
        // '예정된 진료를 따르세요'인데 AI 소견 3줄이 전부 '지금 수술팀에 연락하세요'였다.
        // 수술 후 '퇴원 안내만 불확실'은 긴급도는 now지만 증상이 없다 — LLM이 증상을 지어내지 않게 따로 알린다.
        triage_level: (state.triage && (state.triage.kind === 'confirm' ? 'confirm' : state.triage.level)) || '',
        // 언어 중립 코드 — 서버가 '이 사람에게 해당하는 조언'만 선택지로 추린다(app/services/advice.py).
        // 번역된 문장(chat_symptoms)으로는 언어마다 판별 규칙을 따로 둬야 해서 코드를 따로 보낸다.
        flag_codes: opinionFlagCodes()
    };
    await runAiOpinion();
}

/** 사진 판독 절의 제목. 화면(rep-l1)과 PDF가 반드시 같은 술어를 쓴다.
 *  술후는 술후 문구를, 사진 없음·인공수정체 이력으로 판독 제외는 중립 문구를 쓴다 —
 *  사진을 건너뛴 비수술자에게 '수술 후에는 적용하지 않음'이라고 말하면 안 된다.
 *  (화면만 고쳐 두면 PDF에는 값이 '적용하지 않습니다'인데 제목은 '백내장 AI 분석 결과'로 남는다.) */
function photoSectionLabel(t, fallback) {
    // 자연 수정체 또는 수술하지 않은 반대쪽 눈에 실제 판독을 적용한 회차는
    // 수술 시기만으로 '적용하지 않음'이라고 표시하지 않는다. PDF도 이 함수를 쓴다.
    if (typeof hasPhotoVerdict === 'function' && hasPhotoVerdict()
        && !photoAssessmentExcluded()) return fallback;
    const postop = state.aiResultCode === 'postop'
        || (typeof hasSurgery === 'function' && hasSurgery());
    const excluded = state.aiResultCode === 'skipped'
        || (typeof photoAssessmentExcluded === 'function' && photoAssessmentExcluded());
    return (postop && t.rep_l1_postop) || (excluded && t.rep_l1_excluded) || fallback;
}

/** 리포트의 '값' 3칸을 현재 언어로 다시 그린다.
 *
 *  왜 필요한가: 예전에는 분석 시점 언어로 만든 문자열을 그대로 넣어놨기 때문에
 *  언어를 바꾸면 라벨만 번역되고 값은 이전 언어로 남았다(영어 리포트에 한국어가 섞임).
 *  updateUI(app-core.js)가 언어 전환 때 이 함수를 부른다. */
function refreshReportResults() {
    const t = translations[state.lang];
    const set = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.innerText = text;
    };
    if (state.reportDate) set('report-date', (t.report_issued_on || '{date}').replace('{date}', state.reportDate));
    set('pdf-ai-result', formatCataractResult());
    set('pdf-amsler-result', formatAmslerResult());
    const symptoms = formatSymptoms();
    set('pdf-chat-result', symptoms.length ? symptoms.join(', ') : (t.res_chat_none || '-'));

    // LLM 소견서는 생성 시점 언어로 고정된다 — 자동 번역하지 않고, 다시 생성할 수
    // 있다는 사실만 알린다(재생성은 수 초가 걸리므로 사용자가 고르게 한다).
    const stale = document.getElementById('opinion-stale');
    if (stale) {
        const mismatch = !!state.opinionLang && state.opinionLang !== state.lang;
        stale.classList.toggle('hidden', !mismatch);
        const msg = stale.querySelector('[data-role="msg"]');
        if (msg) msg.textContent = t.opinion_stale || '';
        const btn = stale.querySelector('[data-role="regen"]');
        if (btn) btn.textContent = t.opinion_regen || '';
    }

    // 응급 회차에서는 AI 조언 위에 고정 문장을 띄운다.
    // 서버도 응급 회차에는 모델을 호출하지 않고 고정 안내만 반환한다.
    const surgeryNote = document.getElementById('report-surgery-note');
    if (surgeryNote) surgeryNote.classList.toggle('hidden', !state.riskAnswers?.surgery || state.riskAnswers.surgery === 'none');
    // 술후 경로는 사진 판독을 쓰지 않는다(formatCataractResult가 post_limit을 돌려준다).
    // 제목만 '백내장 AI 결과'로 남으면 판독을 한 것처럼 읽힌다.
    const l1 = document.getElementById('rep-l1');
    if (l1) {
        // 판독을 쓰지 않은 회차는 제목도 바꿔야 한다. 값은 '적용하지 않습니다'인데 제목만
        // '백내장 AI 결과'로 남으면 판독을 해놓고 숨긴 것처럼 읽힌다.
        // 4주 이내 수술은 술후 문구를, 그 밖(사진 없음·인공수정체 이력)은 중립 문구를 쓴다 —
        // 사진을 건너뛴 비수술자에게 '수술 후에는 적용하지 않음'이라고 말하면 안 된다.
        //
        // 조건은 반드시 formatCataractResult()와 같은 술어에서 파생시킨다. 제목이 조건을
        // 따로 세면(예전에는 hasSurgery()만 봤다) 값은 post_limit인데 제목은 '백내장 AI 결과'로
        // 남는 조합이 생긴다 — 6개 언어 × 조합 전수 점검에서 144건이 그렇게 어긋났다.
        l1.textContent = photoSectionLabel(t, t.rep_l1 || l1.textContent);
    }
    const urgentNote = document.getElementById('opinion-urgent-note');
    const isUrgent = state.triage?.level === 'urgent';
    set('opinion-section-title', isUrgent ? t.report_urgent_title : t.rep_info_title);
    // Do not invite someone to keep chatting instead of acting on urgent advice.
    const followupBox = document.getElementById('followup-box');
    if (followupBox) followupBox.classList.toggle('hidden', isUrgent);
    if (urgentNote) {
        urgentNote.textContent = t.opinion_urgent_note || '';
        urgentNote.classList.toggle('hidden', !isUrgent);
    }
}

/** 현재 언어로 소견서를 다시 생성한다(언어 전환 후 사용자가 눌렀을 때). */
function regenerateOpinion() {
    if (!state.opinionRequest) return;
    state.opinionRequest.lang = state.lang;
    state.opinionRequest.cataract_res = formatCataractResult();
    state.opinionRequest.amsler_res = formatAmslerResult();
    state.opinionRequest.chat_symptoms = buildOpinionSymptoms();
    const stale = document.getElementById('opinion-stale');
    if (stale) stale.classList.add('hidden');
    runAiOpinion();
}

// 소견서 생성 1회 시도. 실패하면 본문 자리에 '다시 시도' 버튼을 남긴다.
let _activeOpinion = null;

function cancelAiOpinion() {
    state.opinionErrorKey = '';
    state.opinionFullText = '';
    state.opinionSummaryText = '';
    const details = document.getElementById('opinion-details');
    if (details) { details.open = false; details.classList.add('hidden'); }
    const active = _activeOpinion;
    _activeOpinion = null;
    if (active) {
        active.controller.abort();
        if (active.loader) active.loader.stop();
    }
    const loading = document.getElementById('gemma-loading-container');
    if (loading) loading.classList.add('hidden');
    const retry = document.getElementById('opinion-retry');
    if (retry) retry.classList.add('hidden');
    const cancelBtn = document.getElementById('opinion-cancel');
    if (cancelBtn) cancelBtn.classList.add('hidden');
}

async function runAiOpinion() {
    if (typeof clearPdfDownload === 'function') clearPdfDownload();
    if (!state.opinionRequest) return;
    cancelAiOpinion();
    const request = JSON.parse(JSON.stringify(state.opinionRequest));
    const active = { controller: new AbortController(), loader: null };
    _activeOpinion = active;
    const isCurrent = () => _activeOpinion === active;
    const loadingContainer = document.getElementById('gemma-loading-container');
    const opinionText = document.getElementById('gemma-opinion-text');
    const retryBox = document.getElementById('opinion-retry');
    if (retryBox) retryBox.classList.add('hidden');

    // 가짜 진행바 대신 실제 경과 시간을 보여주는 로더 표시
    let opinionLoader = null;
    if (loadingContainer) {
        loadingContainer.innerHTML = '';
        loadingContainer.classList.remove('hidden');
        opinionLoader = createAiLoader(translations[state.lang].opinion_writing || "AI가 소견서를 작성 중입니다");
        active.loader = opinionLoader;
        loadingContainer.appendChild(opinionLoader.el);
    }
    if (opinionText) {
        opinionText.classList.add('hidden');
        opinionText.innerText = "";
    }
    const stopOpinionLoader = () => {
        if (opinionLoader) { opinionLoader.stop(); opinionLoader = null; active.loader = null; }
        if (loadingContainer) loadingContainer.classList.add('hidden');
        if (opinionText) opinionText.classList.remove('hidden');
    };
    // 실패 시 공통 처리 — 문구를 남기고 '다시 시도' 버튼을 보여준다
    const showFailure = (message, key = 'opinion_error') => {
        state.opinionErrorKey = key;
        stopOpinionLoader();
        if (opinionText) {
            opinionText.innerText = message || translations[state.lang].opinion_error || "로컬 AI 서버와 연결이 끊어졌습니다.";
            opinionText.classList.add('text-rose-600');
        }
        if (retryBox) retryBox.classList.remove('hidden');
    };

    const cancelBtn = document.getElementById('opinion-cancel');
    if (cancelBtn) cancelBtn.classList.remove('hidden');
    try {
        const { text, hasError } = await withAiDeadline(async () => {
            const response = await fetch('/api/get-ai-opinion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(request),
                signal: active.controller.signal
            });

            if (!isCurrent()) return;
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            // 공용 스트림 리더(app-core.js) — 하트비트 무시·마커 분리 감지 처리 포함
            return await readAiStream(response, disp => {
                if (!isCurrent()) return;
                stopOpinionLoader();   // 첫 실제 토큰 도착 → 로더 제거, 본문 표시 시작
                // 마커 앞(상세 설명)까지만 흘려보낸다. 요약은 완료 시점에 3줄로 정리해
                // 이 자리로 옮기고, 상세는 접힘 영역으로 내려간다.
                // 고정 문구를 넣으면 로더까지 걷힌 뒤라 생성이 끝날 때까지 화면이 멈춘 것처럼 보인다
                // (상세 6~8문장 + 요약 3줄이라 그 시간이 짧지 않다).
                opinionText.innerText = disp.split('<<<SUMMARY>>>')[0].replace(/\*\*/g, '');
            });
        }, active.controller);
        if (!isCurrent()) return;
        stopOpinionLoader();       // 빈 응답이어도 로더는 정리
        opinionText.innerText = text;

        // AI 오류면 의료 소견이 아님 → 에러로 표시하고 완료 알림을 건너뜀
        if (hasError) { showFailure(); return; }

        opinionText.classList.remove('text-rose-600');
        // 모델이 마크다운(**)을 섞어 보내는 경우 평문으로 정리
        const clean = text.replace(/\*\*/g, '').trim();
        const parts = clean.split('<<<SUMMARY>>>');
        const lines = v => v.split(/\n/).map(x => x.trim()).filter(Boolean);
        // 마커가 오면 앞이 상세, 뒤가 요약이다. 모델이 마커를 빠뜨리는 일이 실제로 있는데,
        // 그때 전문을 양쪽에 다 넣으면 같은 글이 요약칸과 상세칸에 두 번 보인다.
        // 마커가 없으면 앞 3줄을 요약으로 쓰고 나머지를 상세로 돌린다.
        let markedSummary = parts.length > 1 ? lines(parts.slice(1).join('\n')) : [];
        // 큰 모델(e4b)은 요약 3문장을 줄바꿈 없이 한 줄로 이어 쓰는 일이 잦았다(2026-09-27 측정 30번 중 8번).
        // 그대로 두면 '3줄 요약'이 한 문단 덩어리로 보인다 — 한 줄이면 문장 단위로 나눈다.
        if (markedSummary.length === 1) {
            // 일본어·중국어는 마침표 뒤에 공백이 없다
            const sentences = markedSummary[0].split(/(?<=[.!?])\s+|(?<=[。！？])/).map(x => x.trim()).filter(Boolean);
            if (sentences.length > 1) markedSummary = sentences;
        }
        const summary = markedSummary.length ? markedSummary : lines(parts[0]).slice(0, 3);
        if (!summary.length) { showFailure(); return; }
        const detail = parts.length > 1 ? parts[0].trim() : lines(clean).slice(3).join('\n');
        opinionText.innerText = summary.slice(0, 3).join('\n');
        state.opinionSummaryText = opinionText.innerText;
        state.opinionFullText = clean.replace('<<<SUMMARY>>>', '\n\n');
        const details = document.getElementById('opinion-details');
        const detailText = document.getElementById('opinion-detail-text');
        if (details && detailText) {
            detailText.textContent = detail;
            details.classList.toggle('hidden', !detail);
        }
        // 어떤 언어로 쓰였는지 기록 — 이후 언어를 바꾸면 재생성을 안내한다
        state.opinionLang = request.lang || state.lang;
        refreshReportResults();
    } catch (e) {
        if (!isCurrent()) return;
        const t = translations[state.lang];
        const key = e.name === 'TimeoutError' ? 'ai_timeout' : active.controller.signal.aborted ? 'ai_cancelled' : 'opinion_error';
        showFailure(t[key], key);
        return;
    } finally {
        if (isCurrent()) {
            _activeOpinion = null;
            if (cancelBtn) cancelBtn.classList.add('hidden');
        }
    }

    // ── 여기부터는 소견을 이미 다 받은 뒤의 '부가 동작'이다. 위 try 안에 두면 안 된다:
    // 안드로이드 크롬은 new Notification()이 "Illegal constructor"로 예외를 던지는데(서비스워커
    // 알림만 허용), 그 예외가 catch로 흘러 멀쩡히 완성된 소견을 '로컬 AI 서버와 연결이
    // 끊어졌습니다'로 덮어썼다 (S25 Ultra 실기기 재현, 2026-09-02). 부가 동작 실패는 소견과 무관하다.
    notifyOpinionDone();
    // Presentation build: PDF is the only persistent copy; no server save request.

}

// 완료 알림 — 데스크톱 브라우저에서만 동작한다. 모바일(안드로이드 크롬)은 페이지 컨텍스트의
// new Notification()을 금지해 예외를 던지므로 반드시 삼킨다. 알림은 있으면 좋은 것이지 소견의 일부가 아니다.
function notifyOpinionDone() {
    try {
        if (!("Notification" in window) || Notification.permission !== "granted") return;
        new Notification(translations[state.lang].notif_title || "Eye-Catch 진단 완료", {
            body: translations[state.lang].notif_body || "Gemma AI의 맞춤형 소견서 작성이 완료되었습니다! 결과를 확인해보세요.",
        });
    } catch (e) {
        /* 모바일: Illegal constructor — 무시 */
    }
}

function stopOpinionRequest() {
    if (_activeOpinion) _activeOpinion.controller.abort();
}
