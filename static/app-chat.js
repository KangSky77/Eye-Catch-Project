// ==========================================
// app-chat.js — 하이브리드 챗봇 (Rule-based + Gemma 4)
// app-core.js가 먼저 로드되어야 함 (state, createAiLoader, nextStep 등 사용)
// ==========================================
function startChat() {
    document.getElementById('chat-box').innerHTML = '';

    // 챗봇 관련 상태 초기화
    state.stepIdx = 0;
    state.dynamicCount = 0;
    state.chatSymptoms = [];
    state.symptomCodes = [];
    state.chatHistory = [];
    state.chatBusy = false;
    // 위험요인 문진을 증상 질문보다 먼저 받는다 — 예측력이 크고 비용이 거의 없다
    state.riskIdx = 0;
    state.riskAnswers = {};
    state.symIdx = 0;
    state.symptomScore = 0;
    state.redFlags = [];

    askRiskQuestion();
}

// ------------------------------------------------------------------
// 1단계: 위험요인 문진 (나이·당뇨·고혈압·가족력·흡연)
// 선택지형(나이)과 예/아니오형이 섞여 있어 버튼을 질문마다 새로 그린다.
// ------------------------------------------------------------------
function askRiskQuestion() {
    const q = riskQuestions[state.riskIdx];
    const t = translations[state.lang];
    addMsg('bot', t[q.key] || q.key);
    if (q.type === 'choice') {
        renderChatOptions(q.options.map(o => ({ label: t[o.key] || o.v, value: o.v })));
    } else {
        renderChatOptions([
            { label: t.chat_yes, value: true },
            { label: t.chat_no,  value: false },
        ]);
    }
    state.chatBusy = false;
}

/** 답변 버튼을 질문에 맞게 다시 그린다. 선택지 개수가 달라지므로 매번 재생성. */
function renderChatOptions(opts) {
    const box = document.getElementById('chat-controls');
    box.innerHTML = '';
    box.className = 'p-4 bg-white/80 border-t flex flex-wrap gap-2 backdrop-blur-md';
    opts.forEach(o => {
        const b = document.createElement('button');
        b.className = 'flex-1 py-3.5 bg-blue-600 text-white rounded-2xl font-bold text-sm btn-pop';
        if (o.value === false) b.className = 'flex-1 py-3.5 bg-slate-100 text-slate-600 rounded-2xl font-bold text-sm btn-pop';
        b.style.minWidth = '30%';
        b.textContent = o.label;
        b.onclick = () => handleAnswer(o.value, o.label);
        box.appendChild(b);
    });
}

/** 위험요인 구간과 증상 구간을 하나의 입구로 처리. */
function handleAnswer(value, label) {
    if (state.chatBusy) return;
    if (state.riskIdx < riskQuestions.length) {
        state.chatBusy = true;
        const q = riskQuestions[state.riskIdx];
        addMsg('user', label);
        state.riskAnswers[q.code] = value;
        state.chatHistory.push({ q: translations[state.lang][q.key] || q.key, a: label });
        state.riskIdx++;
        setTimeout(() => {
            if (state.riskIdx < riskQuestions.length) askRiskQuestion();
            else askSymptomQuestion();          // 위험요인이 끝나면 질환별 문진으로
        }, 500);
        return;
    }
    handleSymptomAnswer(value === true);
}

// ------------------------------------------------------------------
// 2단계: 질환별 문진
// 조건부 분기(showIf) — 당뇨망막병증 문항은 당뇨가 있다고 답한 사람에게만 묻는다.
// 비당뇨에게 "당뇨 10년 넘었나요?"를 묻는 것은 시간 낭비이자 결과 왜곡이다.
// ------------------------------------------------------------------

/** 이 사용자에게 실제로 물어볼 문항 목록(분기 반영). */
function activeSymptomQuestions() {
    return symptomQuestions.filter(q => !q.showIf || state.riskAnswers[q.showIf] === true);
}

function askSymptomQuestion() {
    const list = activeSymptomQuestions();
    if (state.symIdx >= list.length) { finishSurvey(); return; }
    const q = list[state.symIdx];
    const t = translations[state.lang];
    addMsg('bot', t[q.key] || q.key, `${state.symIdx + 1} / ${list.length}`);
    renderChatOptions([
        { label: t.chat_yes, value: true },
        { label: t.chat_no,  value: false },
    ]);
    state.chatBusy = false;
}

function handleSymptomAnswer(yes) {
    if (state.chatBusy) return;
    state.chatBusy = true;

    const list = activeSymptomQuestions();
    const q = list[state.symIdx];
    const t = translations[state.lang];
    const label = yes ? t.chat_yes : t.chat_no;
    addMsg('user', label);
    state.chatHistory.push({ q: t[q.key] || q.key, a: label });

    // invert: '아니오'가 위험 신호인 문항(최근 검진 없음, 안저검사 미시행 등)
    const flagged = q.invert ? (yes === false) : (yes === true);
    if (flagged) {
        state.symptomScore = (state.symptomScore || 0) + (q.weight || 0);
        state.chatSymptoms.push(t['sym_' + q.code] || q.code);
        // RAG 검색은 질환 코드 기준 — 중복 없이 모은다
        if (q.disease && q.disease !== 'general' && !state.symptomCodes.includes(q.disease)) {
            state.symptomCodes.push(q.disease);
        }
        if (q.redFlag) state.redFlags = (state.redFlags || []).concat(q.code);
    }

    state.symIdx++;
    setTimeout(askSymptomQuestion, 450);
}

/** 문진 종료 → 기존 동적 질문(LLM) 단계로 넘긴다. */
function finishSurvey() {
    state.stepIdx = questions[state.lang].length;   // 고정 질문 구간을 건너뛴 상태로 맞춤
    addLoadingMsg(translations[state.lang].survey_done || '');
    fetchNextQuestion();
}

function addMsg(sender, text, progress) {
    const box = document.getElementById('chat-box');
    const div = document.createElement('div');
    div.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} w-full`;
    const bubble = document.createElement('div');
    bubble.className = `max-w-[80%] p-3 rounded-2xl text-sm font-bold ${sender === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-white text-slate-700 rounded-tl-sm shadow-sm border border-slate-50'}`;
    // 문항이 13개까지 늘어나 끝이 안 보이면 이탈한다 — 진행률을 보여준다
    if (progress) {
        const p = document.createElement('span');
        p.className = 'block text-[10px] font-black text-slate-400 mb-1';
        p.textContent = progress;
        bubble.appendChild(p);
        bubble.appendChild(document.createTextNode(text));
    } else {
        bubble.textContent = text;
    }
    div.appendChild(bubble);
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
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

    // 서버 실패·빈 응답이면 선택 언어의 기본 질문으로 폴백 (백엔드도 실패 시 ""를 반환)
    let q = translations[state.lang].nextq_fallback || "추가적으로 눈이 불편하신 곳이 있나요?";
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
        if (result.question) q = result.question;
    } catch (e) {
        // 네트워크 오류 → 위의 폴백 질문 그대로 사용
    } finally {
        removeLoadingMsg(); // "생성 중..." 메시지 제거
        addMsg('bot', q);
        state.chatHistory.push({ q: q, a: "" });
        state.chatBusy = false;   // 새 질문 표시 완료 → 답변 잠금 해제
    }
}

async function handleChatAnswer(yes) {
    if (state.chatBusy) return;          // 처리 중 중복 클릭 무시 (질문/답변 어긋남·중복 호출 방지)
    state.chatBusy = true;               // 다음 질문이 표시될 때까지 잠금

    const answerText = yes ? translations[state.lang].chat_yes : translations[state.lang].chat_no;
    addMsg('user', answerText);

    // [1단계] 고정 질문 구간
    if (state.stepIdx < questions[state.lang].length) {
        const currentQ = questions[state.lang][state.stepIdx];
        if (yes) { state.chatSymptoms.push(currentQ.type); state.symptomCodes.push(currentQ.code); }

        state.chatHistory.push({ q: currentQ.t, a: answerText });
        state.stepIdx++;

        if (state.stepIdx < questions[state.lang].length) {
            setTimeout(() => { addMsg('bot', questions[state.lang][state.stepIdx].t); state.chatBusy = false; }, 600);
        } else {
            setTimeout(() => {
                addLoadingMsg(translations[state.lang].survey_done || "기본 문진이 완료되었습니다. 맞춤형 추가 질문을 생성 중입니다...");
                fetchNextQuestion();
            }, 600);
        }
    }
    // [2단계] Gemma 맞춤형 질문 구간
    else {
        state.chatHistory[state.chatHistory.length - 1].a = answerText;
        if (yes) { state.chatSymptoms.push(translations[state.lang].symptom_extra || "기타 의심 증상 추가 발견"); state.symptomCodes.push('other'); }

        state.dynamicCount++;

        if (state.dynamicCount < state.maxDynamic) {
            setTimeout(() => {
                addLoadingMsg(translations[state.lang].next_q_generating || "다음 맞춤형 질문을 생성 중입니다...");
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
