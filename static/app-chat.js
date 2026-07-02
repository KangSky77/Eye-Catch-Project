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
                addLoadingMsg(translations[state.lang].survey_done || "기본 문진이 완료되었습니다. 맞춤형 추가 질문을 생성 중입니다... ⏳");
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
