// ==========================================
// app-chat.js — 하이브리드 챗봇 (Rule-based + Gemma 4)
// app-core.js가 먼저 로드되어야 함 (state, createAiLoader, nextStep 등 사용)
// ==========================================
function startChat() {
    document.getElementById('chat-box').innerHTML = '';
    setChatAnswerMode('yesno');   // 이전 회차에서 자유 입력칸이 열려 있었을 수 있다

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
    state.symptomAnswers = {};
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
    addMsg('bot', t[q.key] || q.key, surveyProgress());
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

/** 답변 버튼을 질문에 맞게 다시 그린다. 선택지 개수가 달라지므로 매번 재생성.
 *  onPick을 반드시 받는다 — 예전에는 handleAnswer에 고정돼 있어서, 문진이 끝난 뒤
 *  Gemma 맞춤형 질문에 답해도 문진 핸들러가 호출돼 문진이 그 자리에서 멈췄다. */
function renderChatOptions(opts, onPick) {
    const pick = onPick || handleAnswer;
    const box = document.getElementById('chat-controls');
    box.innerHTML = '';
    // className을 통째로 덮어쓰므로 hidden 상태가 날아간다 —
    // 버튼을 그린다는 건 '버튼이 답변 수단'이라는 뜻이므로 자유 입력칸은 닫아준다.
    box.className = 'p-4 bg-white/80 border-t flex flex-wrap gap-2 backdrop-blur-md';
    const freeBox = document.getElementById('chat-free');
    if (freeBox) freeBox.classList.add('hidden');
    opts.forEach(o => {
        const b = document.createElement('button');
        // '네'만 파란 primary, '아니오'는 회색이면 의학 문진에서 응답 편향을 만든다
        // (묵종 편향). 두 선택지의 시각 무게를 같게 둔다.
        b.className = 'flex-1 py-3.5 bg-white text-blue-700 border-2 border-blue-200 rounded-2xl font-bold text-sm btn-pop';
        b.style.minWidth = '30%';
        b.textContent = o.label;
        b.onclick = () => pick(o.value, o.label);
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

/** 이 사용자에게 실제로 물어볼 문항 목록(분기 반영).
 *  showIf: 조건이 참일 때만 묻는다(당뇨망막병증 문항 → 당뇨 있는 사람만).
 *  skipIf: 앞선 답으로 이미 정해진 문항은 묻지 않는다(안저검사 1년 내 → 2년 내 검진). */
function activeSymptomQuestions() {
    return symptomQuestions.filter(q => {
        if (q.showIf && state.riskAnswers[q.showIf] !== true) return false;
        if (q.skipIf && state.symptomAnswers[q.skipIf.code] === q.skipIf.answer) return false;
        return true;
    });
}

/** 문진 전체(위험요인 + 증상) 기준 진행 위치 "n / N".
 *
 *  왜 통합하는가: 위험요인 5문항에는 진행률이 없고 증상 문항부터 1/13이 시작돼,
 *  사용자가 전체 길이를 끝까지 알 수 없었다.
 *
 *  총수가 도중에 바뀌는 문제: 분기(showIf)는 당뇨 답변에, skipIf는 안저검사 답변에
 *  달려 있다. 아직 모르는 동안에는 '최대치'로 잡아 총수가 줄기만 하게 한다 —
 *  늘어나면 끝이 멀어지는 느낌을 준다. */
function surveyProgress() {
    const branchKnown = state.riskAnswers.diabetes !== undefined;
    const symCount = branchKnown ? activeSymptomQuestions().length : symptomQuestions.length;
    const total = riskQuestions.length + symCount;
    const pos = state.riskIdx < riskQuestions.length
        ? state.riskIdx + 1
        : riskQuestions.length + state.symIdx + 1;
    return `${Math.min(pos, total)} / ${total}`;
}

function askSymptomQuestion() {
    const list = activeSymptomQuestions();
    if (state.symIdx >= list.length) { finishSurvey(); return; }
    const q = list[state.symIdx];
    const t = translations[state.lang];
    addMsg('bot', t[q.key] || q.key, surveyProgress());
    renderChatOptions([
        { label: t.chat_yes, value: true },
        { label: t.chat_no,  value: false },
    ]);
    state.chatBusy = false;
}

function handleSymptomAnswer(yes) {
    if (state.chatBusy) return;

    const list = activeSymptomQuestions();
    const q = list[state.symIdx];
    // 문진이 이미 끝났는데 호출되면(예전 버튼이 남아 있던 경우) q가 undefined다.
    // 잠금을 걸기 전에 빠져나간다 — 걸어놓고 예외로 죽으면 이후 모든 입력이 무시된다.
    if (!q) return;

    state.chatBusy = true;
    const t = translations[state.lang];
    const label = yes ? t.chat_yes : t.chat_no;
    addMsg('user', label);
    state.chatHistory.push({ q: t[q.key] || q.key, a: label });
    state.symptomAnswers[q.code] = yes;   // skipIf 판단용(언어 중립)

    // invert: '아니오'가 위험 신호인 문항(최근 검진 없음, 안저검사 미시행 등)
    const flagged = q.invert ? (yes === false) : (yes === true);
    if (flagged) {
        state.symptomScore = (state.symptomScore || 0) + (q.weight || 0);
        // 번역된 문장이 아니라 i18n 키를 저장한다 — 언어를 바꾸면 리포트가
        // formatSymptoms()로 현재 언어에 맞춰 다시 만든다.
        state.chatSymptoms.push('sym_' + q.code);
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
    const cataractRes = formatCataractResult();
    // finish()와 동일하게 선택 언어로 전달 (LLM 프롬프트 컨텍스트 언어 일관성)
    const amslerRes = state.hasAmsler
        ? (translations[state.lang].res_ams_bad || "이상 있음")
        : (translations[state.lang].res_ams_ok || "정상");

    // 서버 실패·빈 응답이면 선택 언어의 기본 질문으로 폴백 (백엔드도 실패 시 ""를 반환)
    let q = translations[state.lang].nextq_fallback || "추가적으로 눈이 불편하신 곳이 있나요?";
    let answerType = 'yesno';
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
        if (result.question) {
            q = result.question;
            // 서버가 이 질문을 네/아니오로 답할 수 있는지 알려준다.
            // 서술형이면 버튼 대신 자유 입력칸을 띄운다 — 버튼만 있으면 답할 방법이 없다.
            answerType = result.answer_type === 'text' ? 'text' : 'yesno';
        }
    } catch (e) {
        // 네트워크 오류 → 위의 폴백 질문(예/아니오형) 그대로 사용
    } finally {
        removeLoadingMsg(); // "생성 중..." 메시지 제거
        addMsg('bot', q);
        state.chatHistory.push({ q: q, a: "" });
        setChatAnswerMode(answerType);
        if (answerType !== 'text') {
            // 맞춤형 질문 전용 버튼을 새로 그린다(문진 핸들러가 아니라 handleChatAnswer로).
            const tt = translations[state.lang];
            renderChatOptions(
                [{ label: tt.chat_yes, value: true }, { label: tt.chat_no, value: false }],
                v => handleChatAnswer(v === true)
            );
        }
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
        if (yes) { state.chatSymptoms.push('sym_' + currentQ.code); state.symptomCodes.push(currentQ.code); }

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
        // 소견서 문맥과 리포트 표시에만 남긴다(chatSymptoms). symptomCodes에는 넣지 않는다 —
        // computeTriage의 anySymptom이 그것을 세기 때문에, LLM이 즉석에서 만든 검수되지 않은
        // 질문에 '네' 하나로 권장 조치가 monitor에서 weeks로 올라갔다(2026-09-04 확인).
        // computeTriage 주석이 명시하듯 진료 시점은 '사람이 검수한 문항'만으로 정해야 한다.
        // 자유 입력 경로(handleChatFreeAnswer)는 원래부터 symptomCodes를 건드리지 않았으므로,
        // 답변 수단(버튼/입력칸)에 따라 판정이 달라지던 불일치도 함께 사라진다.
        if (yes) state.chatSymptoms.push('symptom_extra');

        state.dynamicCount++;
        advanceAfterDynamicAnswer();
    }
}


// ------------------------------------------
// 답변 입력 모드 전환 (네/아니오 버튼 <-> 자유 입력칸)
// AI가 서술형 질문을 내면 버튼으로는 답할 수 없으므로 입력칸으로 바꾼다.
// ------------------------------------------
function setChatAnswerMode(mode) {
    const buttons = document.getElementById('chat-controls');
    const free = document.getElementById('chat-free');
    if (!buttons || !free) return;
    const isText = mode === 'text';
    buttons.classList.toggle('hidden', isText);
    free.classList.toggle('hidden', !isText);
    if (isText) {
        const input = document.getElementById('chat-free-input');
        if (input) { input.value = ''; input.focus(); }
    }
}

// 자유 답변 전송. skip=true면 "답변 안 함"으로 넘어간다.
function handleChatFreeAnswer(skip) {
    if (state.chatBusy) return;
    const input = document.getElementById('chat-free-input');
    const text = skip ? '' : (input ? input.value.trim() : '');
    if (!skip && !text) { if (input) input.focus(); return; }   // 빈 답변은 전송하지 않는다

    state.chatBusy = true;
    const shown = text || (translations[state.lang].chat_free_skip || '건너뛰기');
    addMsg('user', shown);
    if (input) input.value = '';
    setChatAnswerMode('yesno');   // 다음 질문은 보통 예/아니오형이므로 기본으로 되돌린다

    // 자유 답변은 소견서 문맥(chatHistory)에만 남긴다.
    // symptomCodes/triage는 검증된 고정 문항으로만 계산한다 — 자유 문장을
    // 코드로 자동 변환하면 근거 없는 의료 판정이 섞인다.
    if (state.chatHistory.length) {
        state.chatHistory[state.chatHistory.length - 1].a =
            text || (translations[state.lang].res_chat_none || '답변 없음');
    }

    state.dynamicCount++;
    advanceAfterDynamicAnswer();
}

// 맞춤형 질문 구간에서 답변 후 다음 단계로 (버튼 답변·자유 답변 공통)
function advanceAfterDynamicAnswer() {
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

// 입력칸에서 Enter로도 전송 (한글·일본어 조합 중 Enter는 무시)
window.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('chat-free-input');
    if (!input) return;
    input.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); handleChatFreeAnswer(); }
    });
});
