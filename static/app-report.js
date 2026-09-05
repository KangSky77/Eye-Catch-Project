// ==========================================
// app-report.js — 리포트 생성 및 PDF 내보내기 (Report & Export)
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
            formatSymptoms(),
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

async function finish() {
    if ("Notification" in window && Notification.permission !== "denied") {
        Notification.requestPermission();
    }

    const d = new Date();
    document.getElementById('report-date').innerText = `${d.getFullYear()}.${d.getMonth()+1}.${d.getDate()} ISSUED`;

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
    state.triage = computeTriage({
        cataractCode: state.aiResultCode,
        amslerAbnormal: state.hasAmsler,
        symptomCodes: state.symptomCodes,
        riskScore: risk.score,
        symptomScore: state.symptomScore,
        redFlags: state.redFlags,
        visionAsymmetric: state.visionTest && state.visionTest.asymmetric,
    });
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
        cataract_code: state.aiResultCode,
        amsler_abnormal: state.hasAmsler,
        symptom_codes: state.symptomCodes,
        eye_asymmetric: state.asymmetric   // 편측(한쪽 눈만) 위험 여부
    };
    await runAiOpinion();
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
}

async function runAiOpinion() {
    if (!state.opinionRequest) return;
    cancelAiOpinion();
    const request = JSON.parse(JSON.stringify(state.opinionRequest));
    const active = { controller: new AbortController(), loader: null };
    _activeOpinion = active;
    const isCurrent = () => _activeOpinion === active;
    const consent = document.getElementById('consent-box');
    if (consent) consent.classList.add('hidden');

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
    const showFailure = () => {
        stopOpinionLoader();
        if (opinionText) {
            opinionText.innerText = translations[state.lang].opinion_error || "로컬 AI 서버와 연결이 끊어졌습니다.";
            opinionText.classList.add('text-rose-600');
        }
        if (retryBox) retryBox.classList.remove('hidden');
    };

    try {
        const response = await fetch('/api/get-ai-opinion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
            signal: active.controller.signal
        });

        if (!isCurrent()) return;
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        // 공용 스트림 리더(app-core.js) — 하트비트 무시·마커 분리 감지 처리 포함
        const { text, hasError } = await readAiStream(response, disp => {
            if (!isCurrent()) return;
            stopOpinionLoader();   // 첫 실제 토큰 도착 → 로더 제거, 본문 표시 시작
            opinionText.innerText = disp;
        });
        if (!isCurrent()) return;
        stopOpinionLoader();       // 빈 응답이어도 로더는 정리
        opinionText.innerText = text;

        // AI 오류면 의료 소견이 아님 → 에러로 표시하고 완료 알림·DB저장을 건너뜀
        if (hasError) { showFailure(); return; }

        opinionText.classList.remove('text-rose-600');
        // 모델이 마크다운(**)을 섞어 보내는 경우 평문으로 정리
        opinionText.innerText = opinionText.innerText.replace(/\*\*/g, '');
        // 어떤 언어로 쓰였는지 기록 — 이후 언어를 바꾸면 재생성을 안내한다
        state.opinionLang = request.lang || state.lang;
        refreshReportResults();
    } catch (e) {
        if (!isCurrent()) return;
        showFailure();
        return;
    } finally {
        if (isCurrent()) _activeOpinion = null;
    }

    // ── 여기부터는 소견을 이미 다 받은 뒤의 '부가 동작'이다. 위 try 안에 두면 안 된다:
    // 안드로이드 크롬은 new Notification()이 "Illegal constructor"로 예외를 던지는데(서비스워커
    // 알림만 허용), 그 예외가 catch로 흘러 멀쩡히 완성된 소견을 '로컬 AI 서버와 연결이
    // 끊어졌습니다'로 덮어썼다 (S25 Ultra 실기기 재현, 2026-09-02). 부가 동작 실패는 소견과 무관하다.
    notifyOpinionDone();
    try {
        // 진단 결과 DB 저장 — 건강정보는 민감정보라 '동의한 경우에만' 저장한다.
        requestSaveConsent({
            cataract_result: request.cataract_res,
            amsler_result: request.amsler_res,
            chat_symptoms: request.chat_symptoms,
            gemma_opinion: opinionText ? opinionText.innerText : ''
        });
    } catch (e) {
        console.warn('save-consent UI failed (opinion is intact)', e);
    }
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

let _followupBusy = false;

async function askGemmaMore() {
    if (_followupBusy) return;   // 답변 스트리밍 중 재전송 금지 (응답이 뒤섞이는 것 방지)

    const inputEl = document.getElementById('user-followup-input');
    const responseEl = document.getElementById('followup-response');
    const sendBtn = document.getElementById('followup-send-btn');
    const userMsg = inputEl.value.trim();

    if (!userMsg) { inputEl.focus(); return; }

    // 서버 스키마 상한(ChatRequest.context 5000자)에 맞춰 자름 — 넘기면 422가 나서 '서버 연결 불가'로 오인
    const context = document.getElementById('gemma-opinion-text').innerText.slice(0, 5000);

    _followupBusy = true;
    if (sendBtn) { sendBtn.disabled = true; sendBtn.setAttribute('aria-busy', 'true'); }
    inputEl.value = '';
    responseEl.classList.remove('hidden');
    responseEl.innerText = '';
    const loader = createAiLoader(translations[state.lang].followup_thinking || "답변을 생각하고 있습니다");
    responseEl.appendChild(loader.el);
    let firstChunk = true;

    try {
        const response = await fetch('/api/chat-with-gemma', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lang: state.lang, user_msg: userMsg, context: context })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        // 공용 스트림 리더(app-core.js) — 하트비트 무시·마커 분리 감지 처리 포함
        const { text, hasError } = await readAiStream(response, disp => {
            if (firstChunk) {       // 첫 실제 토큰 도착 → 로더 제거 후 답변 표시 시작
                loader.stop();
                firstChunk = false;
            }
            responseEl.innerText = `Q: ${userMsg}\nA: ` + disp;
        });
        loader.stop();              // 빈 응답이어도 로더는 정리
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
        responseEl.innerText = translations[state.lang].srv_err || "서버와 연결할 수 없습니다.";
    } finally {
        _followupBusy = false;
        if (sendBtn) { sendBtn.disabled = false; sendBtn.removeAttribute('aria-busy'); }
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

// 소견서를 '쪼개짐 방지' 문단들로 변환.
// 이유: 소견서가 빈 줄 없는 긴 한 덩어리면 html2pdf가 페이지 경계에서
//       텍스트 한 줄을 가로로 반 잘라 다음 장으로 넘긴다(보기 흉함).
//       빈 줄 문단이 있으면 그 문단을, 없으면 문장 3개씩 묶어 각각
//       page-break-inside:avoid <p>로 감싼다 → 페이지 경계가 문단 사이에 떨어짐.
//       (문단 하나는 한 페이지보다 짧아 'avoid가 통째로 자르는' 위험 없음)
// 입력은 이미 escapeHTML된 텍스트라 문장 분리/삽입이 안전하다.
function toAvoidBreakParagraphs(escapedText) {
    let paras = escapedText.split(/\n\s*\n/).map(s => s.trim()).filter(Boolean);
    // 3줄 요약은 줄 하나가 한 항목 — 줄마다 문단으로 남겨 PDF에서도 3줄로 보이게
    if (paras.length <= 1) paras = escapedText.split(/\n/).map(s => s.trim()).filter(Boolean);
    if (paras.length <= 1) {
        const sentences = escapedText.replace(/\n/g, ' ')
            .split(/(?<=[.!?。！？])\s+/).map(s => s.trim()).filter(Boolean);
        paras = [];
        for (let i = 0; i < sentences.length; i += 3) paras.push(sentences.slice(i, i + 3).join(' '));
    }
    if (paras.length === 0) paras = [escapedText];
    return paras
        .map(p => `<p style="margin:0 0 12px; page-break-inside:avoid;">${p.replace(/\n/g, '<br>')}</p>`)
        .join('');
}

// PDF 생성기(저장 전 단계까지)를 반환 — downloadPDF()가 .save() 호출
function buildReportPdf() {
    const date = escapeHTML(document.getElementById('report-date').innerText);
    const aiResult = escapeHTML(document.getElementById('pdf-ai-result').innerText);
    const amslerResult = escapeHTML(document.getElementById('pdf-amsler-result').innerText);
    const chatResult = escapeHTML(document.getElementById('pdf-chat-result').innerText);
    // LLM 출력도 escape (다른 필드와 동일하게 — innerHTML 삽입 전 XSS 방지)
    const gemmaOpinion = escapeHTML(document.getElementById('gemma-opinion-text').innerText);

    // PDF 라벨을 선택 언어로 (한국어 폴백)
    const t = translations[state.lang] || {};
    const L = {
        title:   t.pdf_doc_title || "Eye-Catch 정밀 진단 리포트",
        issued:  t.pdf_issued    || "발급일자",
        s1:      t.pdf_s1        || "1. 백내장 AI 분석 결과",
        s2:      t.pdf_s2        || "2. 황반변성 자가진단 (Amsler Grid)",
        s3:      t.pdf_s3        || "3. AI 문진 주요 소견",
        s4:      t.pdf_s4        || "4. 종합 AI 소견서 (Powered by Gemma)",
        footer:  t.pdf_footer    || "본 리포트는 인공지능 기반의 자가진단 보조 자료입니다.<br>정확한 진단 및 처방을 위해서는 반드시 안과 전문의와 상담하시기 바랍니다."
    };

    const printDiv = document.createElement('div');
    printDiv.style.fontFamily = "'Pretendard', sans-serif";
    printDiv.style.color = '#1e293b';
    printDiv.style.backgroundColor = '#ffffff';
    // html2canvas가 안정적으로 레이아웃을 잡도록 A4 본문 폭(여백 제외)을 고정
    printDiv.style.width = '700px';
    // 좌우 안쪽 여유: 박스 테두리가 캡처 폭 경계에 딱 걸리면 오른쪽 선이 잘려 보임
    printDiv.style.boxSizing = 'border-box';
    printDiv.style.padding = '0 12px';

    printDiv.innerHTML = `
        <div style="text-align: center; border-bottom: 3px solid #1e293b; padding-bottom: 15px; margin-bottom: 30px;">
            <h1 style="font-size: 28px; font-weight: 900; margin: 0; color: #0f172a; letter-spacing: -1px;">${L.title}</h1>
            <p style="font-size: 13px; color: #64748b; margin-top: 10px; font-weight: bold;">${L.issued}: ${date}</p>
        </div>

        <div style="margin-bottom: 25px;">
            <h3 style="font-size: 16px; color: #2563eb; border-left: 5px solid #2563eb; padding-left: 10px; margin-bottom: 12px; margin-top: 0;">${L.s1}</h3>
            <div style="background: #f8fafc; padding: 15px 20px; border: 1px solid #e2e8f0; font-weight: 900; font-size: 15px; color: #1e40af;">
                ${aiResult}
            </div>
        </div>

        <div style="margin-bottom: 25px;">
            <h3 style="font-size: 16px; color: #334155; border-left: 5px solid #475569; padding-left: 10px; margin-bottom: 12px; margin-top: 0;">${L.s2}</h3>
            <div style="background: #f8fafc; padding: 15px 20px; border: 1px solid #e2e8f0; font-size: 15px; font-weight: bold;">
                ${amslerResult}
            </div>
        </div>

        <div style="margin-bottom: 25px;">
            <h3 style="font-size: 16px; color: #334155; border-left: 5px solid #475569; padding-left: 10px; margin-bottom: 12px; margin-top: 0;">${L.s3}</h3>
            <div style="background: #f8fafc; padding: 15px 20px; border: 1px solid #e2e8f0; font-size: 15px; font-weight: bold;">
                ${chatResult}
            </div>
        </div>

        <!-- 소견서는 한 페이지보다 길 수 있으므로 page-break-inside: avoid를 넣으면 안 됨
             (avoid를 넣으면 html2pdf가 자를 곳을 못 찾아 내용이 통째로 잘림) -->
        <div style="margin-bottom: 40px;">
            <h3 style="font-size: 18px; color: #0f172a; border-left: 5px solid #0f172a; padding-left: 10px; margin-bottom: 15px; margin-top: 0;">${L.s4}</h3>
            <div style="padding: 25px; border: 2px solid #cbd5e1; background: #ffffff; line-height: 1.8; font-size: 15px; color: #334155; font-weight: 500;">
                ${toAvoidBreakParagraphs(gemmaOpinion)}
            </div>
        </div>

        <div style="text-align: center; margin-top: 50px; padding-top: 20px; border-top: 1px solid #cbd5e1; font-size: 12px; color: #94a3b8; line-height: 1.5; page-break-inside: avoid;">
            ${L.footer}<br>
            <br>
            <strong style="color: #64748b; font-size: 14px;">Eye-Catch AI System</strong>
        </div>
    `;

    // [핵심] printDiv를 화면 (0,0)에 실제로 붙여놓고 캡처.
    // 떼어놓은(detached) 상태로 캡처하면 브라우저 창 크기·스크롤 위치에 따라
    // 내용이 가로/세로로 밀려 백지·반토막 PDF가 나오는 html2canvas 버그들이 있음.
    // 고정 위치에 부착하면 좌표 계산이 어긋날 여지가 없다.
    const host = document.createElement('div');
    host.style.cssText = 'position:fixed; top:0; left:0; z-index:-9999; opacity:0; pointer-events:none; background:#ffffff;';
    host.appendChild(printDiv);
    document.body.appendChild(host);
    _pdfHost = host;

    const opt = {
        margin: [15, 12, 15, 12],
        filename: 'Eye-Catch_Official_Report.pdf',
        image: { type: 'jpeg', quality: 0.95 },
        // windowWidth는 절대 넣지 말 것: 실제 창 폭과 어긋나며 가로 밀림 발생
        html2canvas: { scale: 2, useCORS: true, scrollX: 0, scrollY: 0 },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        // 'avoid-all' 제거: 페이지보다 긴 블록(소견서)이 있으면 내용이 잘리는 원인
        pagebreak: { mode: ['css', 'legacy'] }
    };

    return html2pdf().set(opt).from(printDiv);
}

// 캡처용 임시 호스트 (생성 후 반드시 cleanupPdfHost로 제거)
let _pdfHost = null;
function cleanupPdfHost() {
    if (_pdfHost) { _pdfHost.remove(); _pdfHost = null; }
}

let _pdfBusy = false;

function downloadPDF() {
    if (_pdfBusy) return;   // 생성에 몇 초 걸려 연타하면 PDF가 여러 장 만들어진다
    const t = translations[state.lang];
    if (!state.aiResultData) {  // 전부 "-"인 빈 리포트를 내려받는 일 방지
        showToast(t.report_hint_empty || "Run the AI analysis first.", 'info');
        return;
    }

    _pdfBusy = true;
    const btn = document.getElementById('pdf-btn');
    const restoreBtn = setButtonBusy(btn, t.pdf_making || "Creating your PDF...");

    // 이중 안전장치: 생성 동안 스크롤을 맨 위로 (완료 후 원위치 복원)
    const sx = window.scrollX, sy = window.scrollY;
    window.scrollTo(0, 0);
    const restore = () => {
        cleanupPdfHost();
        window.scrollTo(sx, sy);
        restoreBtn();
        _pdfBusy = false;
    };
    try {
        buildReportPdf().save().then(restore, err => {
            restore();
            showToast(t.pdf_err || "Could not create the PDF. Please try again.", 'error');
            console.error(err);
        });
    } catch (err) {         // html2pdf 미로딩 등 동기 실패도 버튼이 잠긴 채로 남지 않게
        restore();
        showToast(t.pdf_err || "Could not create the PDF. Please try again.", 'error');
        console.error(err);
    }
}
