// ==========================================
// app-report.js — 리포트 생성 및 PDF 내보내기 (Report & Export)
// app-core.js가 먼저 로드되어야 함 (state, createAiLoader, escapeHTML, safeStreamDisplay 등 사용)
// ==========================================
async function finish() {
    if ("Notification" in window && Notification.permission !== "denied") {
        Notification.requestPermission();
    }

    const d = new Date();
    document.getElementById('report-date').innerText = `${d.getFullYear()}.${d.getMonth()+1}.${d.getDate()} ISSUED`;

    const cataractRes = state.aiResult || "-";
    const amslerRes = state.hasAmsler ? translations[state.lang].res_ams_bad : translations[state.lang].res_ams_ok;
    const symptoms = state.chatSymptoms;

    document.getElementById('pdf-ai-result').innerText = cataractRes;
    document.getElementById('pdf-amsler-result').innerText = amslerRes;
    document.getElementById('pdf-chat-result').innerText = symptoms.length > 0 ? symptoms.join(", ") : translations[state.lang].res_chat_none;

    showTab('tab-report');

    const loadingContainer = document.getElementById('gemma-loading-container');
    const opinionText = document.getElementById('gemma-opinion-text');

    // 가짜 진행바 대신 실제 경과 시간을 보여주는 로더 표시
    let opinionLoader = null;
    if (loadingContainer) {
        loadingContainer.innerHTML = '';
        loadingContainer.classList.remove('hidden');
        opinionLoader = createAiLoader(translations[state.lang].opinion_writing || "AI가 소견서를 작성 중입니다");
        loadingContainer.appendChild(opinionLoader.el);
    }
    if (opinionText) {
        opinionText.classList.add('hidden');
        opinionText.innerText = "";
    }
    const stopOpinionLoader = () => {
        if (opinionLoader) { opinionLoader.stop(); opinionLoader = null; }
        if (loadingContainer) loadingContainer.classList.add('hidden');
        if (opinionText) opinionText.classList.remove('hidden');
    };

    try {
        const response = await fetch('/api/get-ai-opinion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lang: state.lang,
                cataract_res: cataractRes,
                amsler_res: amslerRes,
                chat_symptoms: symptoms,
                // RAG용 언어 중립 신호
                cataract_code: state.aiResultCode,
                amsler_abnormal: state.hasAmsler,
                symptom_codes: state.symptomCodes,
                eye_asymmetric: state.asymmetric   // 편측(한쪽 눈만) 위험 여부
            })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        // 공용 스트림 리더(app-core.js) — 하트비트 무시·마커 분리 감지 처리 포함
        const { text, hasError } = await readAiStream(response, disp => {
            stopOpinionLoader();   // 첫 실제 토큰 도착 → 로더 제거, 본문 표시 시작
            opinionText.innerText = disp;
        });
        stopOpinionLoader();       // 빈 응답이어도 로더는 정리
        opinionText.innerText = text;
        const streamError = hasError;

        // AI 오류면 의료 소견이 아님 → 에러로 표시하고 완료 알림·DB저장을 건너뜀
        if (streamError) {
            opinionText.innerText = translations[state.lang].opinion_error || "⚠️ AI 서버 응답에 문제가 발생했습니다.";
            opinionText.classList.add('text-rose-600');
            return;
        }
        opinionText.classList.remove('text-rose-600');
        // 모델이 마크다운(**)을 섞어 보내는 경우 평문으로 정리
        opinionText.innerText = opinionText.innerText.replace(/\*\*/g, '');

        if ("Notification" in window && Notification.permission === "granted") {
            new Notification(translations[state.lang].notif_title || "Eye-Catch 진단 완료 🏥", {
                body: translations[state.lang].notif_body || "Gemma AI의 맞춤형 소견서 작성이 완료되었습니다! 결과를 확인해보세요.",
            });
        }

        // 진단 결과 DB 저장 (백그라운드 — 실패해도 UX에 영향 없음)
        fetch('/api/save-diagnosis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cataract_result: cataractRes,
                amsler_result: amslerRes,
                chat_symptoms: symptoms,
                gemma_opinion: opinionText ? opinionText.innerText : ''
            })
        }).catch(() => {}); // 저장 실패는 조용히 무시

    } catch (e) {
        stopOpinionLoader();
        if (opinionText) opinionText.innerText = translations[state.lang].opinion_error || "⚠️ 로컬 AI 서버와 연결이 끊어졌습니다.";
    }
}

async function askGemmaMore() {
    const inputEl = document.getElementById('user-followup-input');
    const responseEl = document.getElementById('followup-response');
    const userMsg = inputEl.value.trim();

    if (!userMsg) return;

    const context = document.getElementById('gemma-opinion-text').innerText;

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
            responseEl.innerText = translations[state.lang].srv_err || "⚠️ 서버와 연결할 수 없습니다.";
            responseEl.classList.add('text-rose-600');
            return;
        }
        responseEl.classList.remove('text-rose-600');
        // 모델이 마크다운(**)을 섞어 보내는 경우 평문으로 정리
        responseEl.innerText = responseEl.innerText.replace(/\*\*/g, '');
    } catch (e) {
        loader.stop();
        responseEl.innerText = translations[state.lang].srv_err || "⚠️ 서버와 연결할 수 없습니다.";
    }
}

// 소견서를 '쪼개짐 방지' 문단들로 변환.
// 이유: 소견서가 빈 줄 없는 긴 한 덩어리면 html2pdf가 페이지 경계에서
//       텍스트 한 줄을 가로로 반 잘라 다음 장으로 넘긴다(보기 흉함).
//       빈 줄 문단이 있으면 그 문단을, 없으면 문장 3개씩 묶어 각각
//       page-break-inside:avoid <p>로 감싼다 → 페이지 경계가 문단 사이에 떨어짐.
//       (문단 하나는 한 페이지보다 짧아 'avoid가 통째로 자르는' 위험 없음)
// 입력은 이미 escapeHTML된 텍스트라 문장 분리/삽입이 안전하다.
function toAvoidBreakParagraphs(escapedText) {
    let paras = escapedText.split(/\n\s*\n/).map(s => s.trim()).filter(Boolean);
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

function downloadPDF() {
    // 이중 안전장치: 생성 동안 스크롤을 맨 위로 (완료 후 원위치 복원)
    const sx = window.scrollX, sy = window.scrollY;
    window.scrollTo(0, 0);
    const restore = () => { cleanupPdfHost(); window.scrollTo(sx, sy); };
    buildReportPdf().save().then(restore, restore);
}
