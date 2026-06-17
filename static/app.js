// ==========================================
// 1. 상태 관리 (State Management)
// 전역 변수들을 하나의 객체로 묶어서 관리합니다.
// ==========================================
const state = {
    lang: 'ko',              // 현재 언어
    stepIdx: 0,              // 고정 질문 인덱스
    aiResult: "",            // 백내장 분석 결과
    hasAmsler: false,        // 황반변성 이상 여부
    chatSymptoms: [],        // 수집된 증상들 (리포트용)
    dynamicCount: 0,         // 젬마가 질문한 횟수
    maxDynamic: 1,           // 젬마 질문 최대 횟수
    chatHistory: []          // 젬마에게 넘길 전체 대화 기록
};

// ==========================================
// 2. 초기화 및 UI 제어 (UI & Navigation)
// ==========================================
window.addEventListener('DOMContentLoaded', () => {
    // 1순위: 사용자가 이전에 직접 고른 언어(localStorage) → 기기/브라우저 언어와 무관하게 유지
    // 2순위: 브라우저 언어  3순위: 영어
    const saved = localStorage.getItem('ec_lang');
    const browser = (navigator.language || navigator.userLanguage || 'en').substring(0, 2);
    const lang = (saved && translations[saved]) ? saved
               : (translations[browser] ? browser : 'en');
    updateUI(lang);
    showTab('tab-test'); // 네비 활성 상태 초기화
});

function changeLanguage(lang) {
    updateUI(lang);
}

function updateUI(lang) {
    state.lang = lang;
    localStorage.setItem('ec_lang', lang);   // 선택 언어 저장 → 새로고침/재방문 시 복원
    document.getElementById('lang-selector').value = lang;

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) el.innerHTML = translations[lang][key];
    });

    // placeholder 등 속성 번역 (data-i18n-ph="키")
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
        const key = el.getAttribute('data-i18n-ph');
        if (translations[lang][key]) el.placeholder = translations[lang][key];
    });

    // 리포트 페이지 하단 지도 버튼 라벨만 현지화 (스타일은 디자인 유지)
    const mapBtn = document.getElementById('dynamic-map-btn');
    if (mapBtn && translations[lang].map_btn) mapBtn.innerText = translations[lang].map_btn;

    renderDiseases(lang);
}

function showTab(tid) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    const target = document.getElementById(tid);
    if (target) target.classList.add('active');
    window.scrollTo(0, 0);

    // 상단/하단 네비 활성 상태 동기화 (data-tab 기준)
    document.querySelectorAll('[data-tab]').forEach(item => {
        item.classList.toggle('active', item.getAttribute('data-tab') === tid);
    });
}

function nextStep(sid) {
    document.querySelectorAll('.step-content').forEach(s => s.classList.remove('active'));
    document.getElementById(sid).classList.add('active');
}

function openMap() {
    if (state.lang === 'ko') window.open('https://map.kakao.com/?q=안과', '_blank');
    else window.open('https://www.google.com/maps/search/eye+clinic+near+me', '_blank');
}

// ==========================================
// 3. AI 비전 분석 (Vision AI)
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
        
        // 백내장 결과를 선택 언어로 표시 (result_code 기반)
        const resultText = translations[state.lang]['ai_' + d.result_code] || d.result;
        state.aiResult = `${resultText} (${d.probability}%)`;

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

        // 얼굴 사진에서 눈을 검출해 분석한 경우 안내 표시
        if (d.mode === 'face' && d.eyes_detected > 0) {
            const pFace = document.createElement('p');
            pFace.className = 'text-[11px] text-slate-500 font-bold mt-2';
            const tmpl = translations[state.lang].face_mode_note || "👁 얼굴 사진에서 눈 {n}곳을 찾아 분석했어요.";
            pFace.textContent = tmpl.replace('{n}', d.eyes_detected);
            disp.appendChild(pFace);
        }

        setTimeout(() => nextStep('step-ai-result'), 1000);
    } catch (e) {
        alert(translations[state.lang].srv_err || "Server Connection Error");
        nextStep('step-photo');
    }
}

function recordAmsler(bad) { 
    state.hasAmsler = bad; // 상태 업데이트
    nextStep('step-chat'); 
    startChat(); 
}

// ==========================================
// 4. 하이브리드 챗봇 (Rule-based + Gemma 4)
// ==========================================
function startChat() { 
    document.getElementById('chat-box').innerHTML = ''; 
    
    // 챗봇 관련 상태 초기화
    state.stepIdx = 0; 
    state.dynamicCount = 0;
    state.chatSymptoms = []; 
    state.chatHistory = []; 
    
    addMsg('bot', questions[state.lang][state.stepIdx].t); 
}

function addMsg(sender, text) {
    const box = document.getElementById('chat-box');
    const div = document.createElement('div');
    div.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} w-full`;
    const bubble = document.createElement('div');
    bubble.className = `max-w-[80%] p-3 rounded-2xl text-sm font-bold ${sender === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-white text-slate-700 rounded-tl-sm shadow-sm border border-slate-50'}`;
    bubble.textContent = text;
    div.appendChild(bubble);
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

// ==========================================
// AI 로딩 인디케이터 (타이핑 점 3개 + 실시간 경과 시간)
// 사용: const loader = createAiLoader("소견서 작성 중"); el에 loader.el 삽입;
//       응답 도착 시 loader.stop() (타이머 정지 + DOM 제거)
// ==========================================
function createAiLoader(label) {
    const wrap = document.createElement('div');
    wrap.className = 'ai-loading';

    const dots = document.createElement('span');
    dots.className = 'ai-dots';
    for (let i = 0; i < 3; i++) dots.appendChild(document.createElement('span'));

    const labelEl = document.createElement('span');
    labelEl.className = 'al-label';
    labelEl.textContent = (label || '').replace(/\n/g, ' ').trim();

    const elapsedEl = document.createElement('span');
    elapsedEl.className = 'al-elapsed';
    const tmpl = translations[state.lang].loading_elapsed || "{s}초 경과";
    elapsedEl.textContent = tmpl.replace('{s}', '0.0');

    wrap.appendChild(dots);
    wrap.appendChild(labelEl);
    wrap.appendChild(elapsedEl);

    const t0 = performance.now();
    const timer = setInterval(() => {
        const sec = ((performance.now() - t0) / 1000).toFixed(1);
        elapsedEl.textContent = tmpl.replace('{s}', sec);
    }, 100);

    return {
        el: wrap,
        stop() {
            clearInterval(timer);
            wrap.remove();
        }
    };
}

// 언어 무관하게 제거할 수 있는 "생성 중..." 로딩 메시지 (점 애니메이션 + 경과 시간)
function addLoadingMsg(text) {
    const box = document.getElementById('chat-box');
    const div = document.createElement('div');
    div.className = 'flex justify-start w-full';
    div.dataset.loading = '1';
    const bubble = document.createElement('div');
    bubble.className = 'max-w-[80%] p-3 rounded-2xl text-sm font-bold bg-white text-slate-700 rounded-tl-sm shadow-sm border border-slate-50';
    const loader = createAiLoader(text);
    bubble.appendChild(loader.el);
    div.appendChild(bubble);
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    state._chatLoaderStop = loader.stop;
}

function removeLoadingMsg() {
    if (state._chatLoaderStop) {
        state._chatLoaderStop();   // 경과 시간 타이머 정지
        state._chatLoaderStop = null;
    }
    const box = document.getElementById('chat-box');
    if (box.lastChild && box.lastChild.dataset && box.lastChild.dataset.loading) {
        box.removeChild(box.lastChild);
    }
}

async function fetchNextQuestion() {
    const cataractRes = state.aiResult || "-";
    // finish()와 동일하게 선택 언어로 전달 (LLM 프롬프트 컨텍스트 언어 일관성)
    const amslerRes = state.hasAmsler
        ? (translations[state.lang].res_ams_bad || "이상 있음")
        : (translations[state.lang].res_ams_ok || "정상");

    try {
        const response = await fetch('/api/generate-next-question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lang: state.lang,
                cataract_res: cataractRes,
                amsler_res: amslerRes,
                chat_history: state.chatHistory
            })
        });
        const result = await response.json();

        removeLoadingMsg(); // "생성 중..." 메시지 제거

        const fallbackQ = translations[state.lang].nextq_fallback || "추가적으로 눈이 불편하신 곳이 있나요?";
        const q = result.question || fallbackQ;
        addMsg('bot', q);
        state.chatHistory.push({ q: q, a: "" });

    } catch (e) {
        removeLoadingMsg();
        const fallbackQ = translations[state.lang].nextq_fallback || "추가적으로 눈이 불편하신 곳이 있나요?";
        addMsg('bot', fallbackQ);
        state.chatHistory.push({ q: fallbackQ, a: "" });
    }
}

async function handleChatAnswer(yes) {
    const answerText = yes ? translations[state.lang].chat_yes : translations[state.lang].chat_no;
    addMsg('user', answerText);
    
    // [1단계] 고정 질문 구간
    if (state.stepIdx < questions[state.lang].length) {
        const currentQ = questions[state.lang][state.stepIdx];
        if (yes) state.chatSymptoms.push(currentQ.type); 
        
        state.chatHistory.push({ q: currentQ.t, a: answerText });
        state.stepIdx++;
        
        if (state.stepIdx < questions[state.lang].length) {
            setTimeout(() => addMsg('bot', questions[state.lang][state.stepIdx].t), 600);
        } else {
            setTimeout(() => {
                addLoadingMsg(translations[state.lang].survey_done || "기본 문진이 완료되었습니다. 맞춤형 추가 질문을 생성 중입니다... ⏳");
                fetchNextQuestion();
            }, 600);
        }
    }
    // [2단계] Gemma 맞춤형 질문 구간
    else {
        state.chatHistory[state.chatHistory.length - 1].a = answerText;
        if (yes) state.chatSymptoms.push(translations[state.lang].symptom_extra || "기타 의심 증상 추가 발견");

        state.dynamicCount++;

        if (state.dynamicCount < state.maxDynamic) {
            setTimeout(() => {
                addLoadingMsg(translations[state.lang].next_q_generating || "다음 맞춤형 질문을 생성 중입니다... ⏳");
                fetchNextQuestion();
            }, 600);
        } else {
            setTimeout(() => { 
                addMsg('bot', translations[state.lang].msg_gen); 
                setTimeout(finish, 1200); 
            }, 500); 
        }
    }
}

// ==========================================
// 5. 리포트 생성 및 부가 기능 (Report & Export)
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
                chat_symptoms: symptoms
            })
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            stopOpinionLoader();   // 첫 토큰 도착 → 로더 제거, 본문 표시 시작
            opinionText.innerText += decoder.decode(value, { stream: true });
        }
        stopOpinionLoader();       // 빈 응답이어도 로더는 정리
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

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            if (firstChunk) {       // 첫 토큰 도착 → 로더 제거 후 답변 표시 시작
                loader.stop();
                responseEl.innerText = `Q: ${userMsg}\nA: `;
                firstChunk = false;
            }
            responseEl.innerText += decoder.decode(value, { stream: true });
        }
        loader.stop();              // 빈 응답이어도 로더는 정리
        // 모델이 마크다운(**)을 섞어 보내는 경우 평문으로 정리
        responseEl.innerText = responseEl.innerText.replace(/\*\*/g, '');
    } catch (e) {
        loader.stop();
        responseEl.innerText = translations[state.lang].srv_err || "⚠️ 서버와 연결할 수 없습니다.";
    }
}

function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
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

// ==========================================
// 6. 질환 상세 모달 (Disease Modal)
// ==========================================
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

// ==========================================
// 7. 병원 찾기 (위치 기반 임베디드 지도)
// ==========================================
function findNearbyClinics() {
    const status = document.getElementById('map-status');
    if (!navigator.geolocation) {
        status.innerText = translations[state.lang].map_status_unsupported || "이 브라우저는 위치 기능을 지원하지 않아요.";
        return;
    }
    status.innerText = translations[state.lang].map_status_loading || "위치를 확인하는 중...";

    navigator.geolocation.getCurrentPosition(
        pos => {
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;
            const d = 0.02;
            const bbox = `${lng - d}%2C${lat - d}%2C${lng + d}%2C${lat + d}`;
            document.getElementById('map-frame').src =
                `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat}%2C${lng}`;
            status.innerText = translations[state.lang].map_status_done || "현재 위치 기준 가까운 안과예요.";
            renderClinicLinks(lat, lng);
        },
        () => {
            status.innerText = translations[state.lang].map_status_denied || "위치 권한이 거부되었어요. 전체 지도에서 검색해 주세요.";
        }
    );
}

function renderClinicLinks(lat, lng) {
    const box = document.getElementById('clinic-list');
    const ko = state.lang === 'ko';
    const kakao = `https://map.kakao.com/?q=${encodeURIComponent('안과')}`;
    const google = `https://www.google.com/maps/search/eye+clinic/@${lat},${lng},15z`;
    const label = ko ? '바로가기' : 'Open';
    box.innerHTML = `
        <div class="clinic-item">
            <span class="ci-ico">🏥</span>
            <div>
                <p class="ci-name">${ko ? '카카오맵 안과 검색' : 'Kakao Map – Eye Clinics'}</p>
                <p class="ci-desc">${ko ? '현재 위치 주변 안과 목록을 지도에서 확인' : 'Nearby eye clinics on the map'}</p>
            </div>
            <a href="${kakao}" target="_blank" rel="noopener">${label}</a>
        </div>
        <div class="clinic-item">
            <span class="ci-ico">🌎</span>
            <div>
                <p class="ci-name">${ko ? '구글맵 안과 검색' : 'Google Maps – Eye Clinics'}</p>
                <p class="ci-desc">${ko ? '내 좌표 기준 안과를 구글맵에서 탐색' : 'Search clinics around your location'}</p>
            </div>
            <a href="${google}" target="_blank" rel="noopener">${label}</a>
        </div>`;
}