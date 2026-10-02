// Report PDF composition, download and cleanup.
// Loaded after app-report.js; uses the same assessment as the screen.

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
    const gemmaOpinion = escapeHTML(state.opinionSummaryText || '');

    // 권장 조치와 검사 요약 해석 — 화면의 DOM을 긁지 않고 원자료에서 다시 만든다.
    //
    // 왜 PDF에 넣는가: 이 앱의 설계는 '등급'이 아니라 '언제 병원에 가야 하는가'를 먼저
    // 보여주는 것인데(computeTriage 주석), 정작 사용자가 병원에 들고 가는 PDF에는
    // 그 항목이 없었다. 더구나 사람이 검수한 결정론적 해석(app-findings.js)이 빠지고
    // LLM 요약만 실려, safety.py가 세운 '해석은 코드가, 생활 조언은 LLM이' 구조와
    // 정반대로 담기고 있었다.
    const triage = computeCurrentTriage();
    const findings = (typeof buildFindings === 'function') ? buildFindings() : [];

    // PDF 라벨을 선택 언어로 (한국어 폴백)
    const t = translations[state.lang] || {};
    const L = {
        title:   t.pdf_doc_title || "Eye-Catch 검사 결과 리포트",
        issued:  t.pdf_issued    || "발급일자",
        s1:      photoSectionLabel(t, t.pdf_s1 || "1. 백내장 AI 분석 결과"),
        s2:      t.pdf_s2        || "2. 황반변성 자가검사 (Amsler Grid)",
        s3:      t.pdf_s3        || "3. AI 문진 주요 소견",
        s4:      triage?.level === 'urgent' ? ('4. ' + t.report_urgent_title)
                    : (t.pdf_s4 || "4. 종합 AI 소견서 (Powered by Gemma)"),
        triage:  t.tri_title     || "권장 조치",
        finds:   t.find_title    || "검사 요약 해석",
        findNote: t.find_disclaimer || "",
        urgentNote: t.opinion_urgent_note || "",
        footer:  t.pdf_footer    || "본 리포트는 인공지능 기반의 자가검사 보조 자료입니다.<br>정확한 진단 및 처방을 위해서는 반드시 안과 전문의와 상담하시기 바랍니다."
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

        ${triage ? `
        <div style="margin-bottom: 28px; border: 2px solid #0f172a; padding: 16px 20px; page-break-inside: avoid;">
            <p style="font-size: 12px; font-weight: 900; color: #64748b; margin: 0 0 6px;">${escapeHTML(L.triage)}</p>
            <p style="font-size: 19px; font-weight: 900; color: #0f172a; margin: 0 0 8px;">${escapeHTML(triage.label)}</p>
            <p style="font-size: 13px; color: #475569; margin: 0; line-height: 1.6;">${escapeHTML(triage.why)}</p>
            ${triage.note ? `<p style="font-size: 13px; font-weight: bold; color: #334155; margin: 8px 0 0; line-height: 1.6;">${escapeHTML(triage.note)}</p>` : ''}
        </div>` : ''}

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

        ${findings.length ? `
        <div style="margin-bottom: 25px;">
            <h3 style="font-size: 16px; color: #334155; border-left: 5px solid #475569; padding-left: 10px; margin-bottom: 12px; margin-top: 0;">${escapeHTML(L.finds)}</h3>
            <ul style="margin: 0; padding-left: 18px; font-size: 13px; color: #334155; line-height: 1.75;">
                ${findings.map(f => `<li style="margin-bottom: 6px;">${escapeHTML(f)}</li>`).join('')}
            </ul>
            ${L.findNote ? `<p style="font-size: 11px; color: #94a3b8; margin: 10px 0 0; line-height: 1.5;">${escapeHTML(L.findNote)}</p>` : ''}
        </div>` : ''}

        <!-- 전문 대신 3줄 요약만 출력하므로 제목과 요약 박스를 같은 페이지에 유지한다. -->
        <div style="margin-bottom: 40px; page-break-inside: avoid;">
            <h3 style="font-size: 18px; color: #0f172a; border-left: 5px solid #0f172a; padding-left: 10px; margin-bottom: 15px; margin-top: 0;">${L.s4}</h3>
            <div style="padding: 25px; border: 2px solid #cbd5e1; background: #ffffff; line-height: 1.8; font-size: 15px; color: #334155; font-weight: 500;">
                ${triage && triage.level === 'urgent' && L.urgentNote ? `<p style="margin: 0 0 14px; padding: 10px 12px; border: 2px solid #fecdd3; background: #fff1f2; color: #9f1239; font-weight: 800; font-size: 13px; line-height: 1.6;">${escapeHTML(L.urgentNote)}</p>` : ''}
                ${gemmaOpinion
                    ? toAvoidBreakParagraphs(gemmaOpinion)
                    : `<p style="margin: 0; color: #64748b; font-size: 13px;">${escapeHTML(t.pdf_no_opinion || '')}</p>`}
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
    host.style.cssText = 'position:fixed; top:0; left:0; z-index:-9999; pointer-events:none; background:#ffffff;';
    host.appendChild(printDiv);
    document.body.appendChild(host);
    _pdfHost = host;

    const opt = {
        margin: [15, 12, 15, 12],
        filename: 'Eye-Catch_Screening_Report.pdf',
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
let _pdfObjectUrl = null, _cancelPdfExport = null;

function clearPdfDownload() {
    if (_cancelPdfExport) _cancelPdfExport();
    if (_pdfObjectUrl) { URL.revokeObjectURL(_pdfObjectUrl); _pdfObjectUrl = null; }
    const box = document.getElementById('pdf-download-help');
    if (box) box.classList.add('hidden');
    const link = document.getElementById('pdf-preview');
    if (link) link.removeAttribute('href');
}
// 구형 기기에서는 캡처만 십수 초가 걸리기도 한다. 넉넉히 두되, 끝은 반드시 있어야 한다.
const PDF_TIMEOUT_MS = 60000;

function downloadPDF() {
    if (_pdfBusy) return;   // 생성에 몇 초 걸려 연타하면 PDF가 여러 장 만들어진다
    const t = translations[state.lang];
    // 소견을 만드는 중이면 기다리게 한다 — 요약이 빠진 PDF가 먼저 저장되지 않게.
    // 하지만 '실패'는 기다린다고 풀리지 않는다. 요약이 없다는 이유로 막았더니 Ollama가 꺼져 있으면
    // PDF를 영영 받을 수 없었다. 권장 조치·검사 해석은 코드가 만든 결정론적 결과라 소견 없이도 본문이 된다.
    if (_activeOpinion) {
        showToast(t.pdf_wait_opinion, 'info');
        return;
    }
    // 빈 리포트 방지는 '사진 결과가 있는가'가 아니라 '검사를 끝냈는가'로 판단한다(리포트 탭 게이트와 같은 기준).
    // 사진 결과로 판단하면 '사진 없이 증상 확인하기'·수술 후 입구로 끝낸 사람은 PDF를 받을 방법이 없었다.
    const completed = typeof hasCompletedScreening === 'function'
        ? hasCompletedScreening() : !!state.aiResultData;
    if (!completed) {
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
    let settled = false;
    let timeoutId = null;
    const complete = () => {
        if (settled) return false;
        settled = true;
        _cancelPdfExport = null;
        if (timeoutId !== null) clearTimeout(timeoutId);
        restore();
        return true;
    };
    _cancelPdfExport = complete;
    const fail = err => {
        if (!complete()) return;
        showToast(t.pdf_err || "Could not create the PDF. Please try again.", 'error');
        console.error(err);
    };
    try {
        // .save() 대신 blob을 직접 받아 <a download>로 내려받는다.
        // jsPDF의 save()는 환경에 따라 새 창을 열어 팝업 차단에 막히고, 그때 프라미스가
        // 끝나지 않아 버튼이 'PDF를 만드는 중...'에 영영 갇혔다(iPhone XS 실측, 2026-09-17).
        // 사용자가 누른 뒤에 만드는 blob이라 <a>로 내려받는 편이 막힐 여지가 적다.
        const done = buildReportPdf().outputPdf('blob');
        timeoutId = setTimeout(() => fail(new Error('PDF 생성 시간 초과')), PDF_TIMEOUT_MS);
        Promise.resolve(done).then(blob => {
            // html2pdf has no cancellation API. Ignore a blob that arrives after
            // timeout instead of downloading it after an error or a new attempt.
            if (settled) return;
            const url = URL.createObjectURL(blob);
            if (_pdfObjectUrl) URL.revokeObjectURL(_pdfObjectUrl);
            _pdfObjectUrl = url;
            const preview = document.getElementById('pdf-preview');
            if (preview) preview.href = url;
            const help = document.getElementById('pdf-download-help');
            if (help) help.classList.remove('hidden');
            const a = document.createElement('a');
            a.href = url;
            a.download = 'Eye-Catch_Screening_Report.pdf';
            document.body.appendChild(a);
            a.click();
            a.remove();
            // Keep one downloadable PDF available until results change or a new PDF replaces it.
            complete();
        }).catch(fail);
    } catch (err) {         // html2pdf 미로딩 등 동기 실패도 버튼이 잠긴 채로 남지 않게
        fail(err);
    }
}
