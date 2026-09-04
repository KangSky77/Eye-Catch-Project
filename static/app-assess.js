// ==========================================
// app-assess.js — 위험도 층화 · 행동 권고(triage)
// app-core.js가 먼저 로드되어야 함
//
// 왜 필요한가:
//   기존 문진은 증상 예/아니오 2개뿐이었다. 그런데 "60세 + 당뇨"라는 정보 하나가
//   비문증 질문보다 예측력이 훨씬 크다. 나이·기저질환·가족력은 묻는 비용이 0에 가까운데
//   위험도 층화에는 가장 강력한 입력이다.
//
//   그리고 결과를 "위험 단계"라는 등급 대신 "언제 병원에 가야 하는가"라는 행동으로 바꾼다.
//   사용자가 실제로 필요한 건 등급이 아니라 다음 행동이고, 진단 표현을 피하는 쪽이
//   규제 측면에서도 안전하다.
// ==========================================

// 위험 점수 배점 근거(교육용 단순 모델 — 임상 검증된 위험예측식이 아님):
//   나이 0~5   노화가 백내장·황반변성·녹내장 공통 최대 위험요인
//   당뇨 3     당뇨망막병증의 직접 원인이며 백내장도 앞당긴다
//   가족력 2   녹내장·황반변성은 가족력 기여가 크다
//   흡연 2     황반변성·백내장 위험을 뚜렷이 높인다
//   고혈압 1   망막혈관 손상에 기여
// 최대 13점.
//
// 나이 구간(data.js의 riskQuestions): 40세 미만 0 / 40대 1 / 50대 2 / 60대 3 / 70대 4 / 80세 이상 5.
// 40세 미만을 더 잘게 쪼개지 않는 이유: 노화성 백내장·황반변성은 이 나이대 유병률이 매우 낮아
// 20대와 30대를 나눠도 배점이 똑같이 0이다 — 문진만 길어지고 결과는 안 바뀐다.
// 반대로 위쪽은 나눴다: 70대와 80대는 백내장 유병률 차이가 실제로 크다 (2026-09-04).
const RISK_MAX = 13;

/** 문진에서 모은 위험요인 답변 → 총점과 해당 항목 라벨. */
function computeRiskScore(answers) {
    let score = 0;
    const factors = [];
    for (const q of riskQuestions) {
        const a = answers[q.code];
        if (a == null) continue;
        if (q.type === 'choice') {
            const opt = q.options.find(o => o.v === a);
            if (opt) {
                score += opt.score;
                if (opt.score >= 2) factors.push(translations[state.lang][opt.key] || a);
            }
        } else if (a === true) {
            score += q.score;
            factors.push(translations[state.lang][q.labelKey] || q.code);
        }
    }
    return { score, factors, max: RISK_MAX };
}

/**
 * 검사 결과 + 위험요인 → 행동 권고 3단계.
 *   now     빠른 시일 내 진료   — 사진 AI 위험 소견 또는 암슬러 이상
 *   weeks   수 주 내 검진      — 사진 AI 경계 소견 또는 검수된 문진 증상
 *   monitor 경과 관찰          — 특별한 신호 없음
 * 등급이 아니라 '다음 행동'을 돌려주는 것이 이 함수의 요점.
 */
function computeTriage(ctx) {
    const risk = ctx.riskScore || 0;
    const anySymptom = (ctx.symptomCodes || []).length > 0;

    // ─────────────────────────────────────────────────────────────────
    // 무엇이 '언제 병원에 가야 하는가'를 결정할 수 있는가 — 의도적으로 좁게 잡는다.
    //
    // 결정에 쓰는 것 (근거가 있는 것만):
    //   · 응급 신호 문진      — 급성 폐쇄각 녹내장·망막 이상은 몇 시간이 시력을 좌우
    //   · 사진 AI 판정        — 그룹분할 test에서 성능이 측정된 유일한 구성요소
    //   · 암슬러 이상 응답    — 확립된 자가검사 프로토콜
    //   · 문진에서 확인된 증상 — 사람이 검수한 질환별 문항
    //
    // 결정에 쓰지 않는 것 (측정은 하되 '참고 정보'로만 보여준다):
    //   · 시력·대비감도 기능검사 좌우 차이
    //       화면 축소 오차·검사 순서·피로·눈 가림 실패·화면 밝기/감마·주변 조명·
    //       굴절 이상 같은 교란을 아직 통제하지 못했다. 기기별 반복 검증 전에는
    //       이 값으로 의료 행동 시점을 바꾸면 안 된다.
    //   · 위험요인 총점(riskScore)
    //       배점은 우리가 임의로 정한 것이고 임상 검증된 예측식이 아니다.
    //       "왜 6점이 기준인가"에 답할 수 없는 숫자로 진료 시점을 정하면 안 된다.
    //       대신 '정기 검진을 권하는 이유'로 리포트에 항목만 보여준다.
    // ─────────────────────────────────────────────────────────────────
    let level;
    if ((ctx.redFlags || []).length > 0) {
        level = 'urgent';
    } else if (ctx.cataractCode === 'risk' || ctx.amslerAbnormal) {
        level = 'now';
    } else if (ctx.cataractCode === 'borderline') {
        level = 'weeks';
    } else if (anySymptom || (ctx.symptomScore || 0) >= 4) {
        level = 'weeks';
    } else {
        level = 'monitor';
    }

    const t = translations[state.lang];
    // 'uncertain'(사진만으로 판단 어려움)은 일부러 진료 시점을 올리지 않는다.
    //   근거: v6 test 분포에서 이 구간(2~25점)에 들어온 것은 정상 2,230장 중 8장(0.4%)이고
    //   백내장은 0장이었다. 임상 검증된 근거 없이 이 구간을 '수 주 내 검진'으로 올리면
    //   대부분 정상인 사람에게 불필요한 진료를 권하게 된다.
    // 대신 안내 문구를 덧붙인다. 이 처리가 없던 동안, 같은 리포트 화면에서 검사 요약은
    // "판단이 어려우니 다시 찍어보라"고 하는데 권장 조치는 "빠른 확인을 권할 신호는
    // 없었습니다"라고 정반대로 말했다. 판정 4단계가 추가될 때 이 함수가 함께 갱신되지 않은
    // 누락이었다(vision.py의 _classify()와 짝을 맞춰야 한다).
    const retakeNote = ctx.cataractCode === 'uncertain' ? (t.tri_note_uncertain || '') : '';

    return {
        level,
        label: t['tri_' + level] || level,
        why: t['tri_' + level + '_why'] || '',
        note: retakeNote,        // 진료 시점은 그대로 두고 덧붙이는 안내 (없으면 빈 문자열)
        riskScore: risk,
        riskMax: RISK_MAX,
    };
}

/** 리포트에 행동 권고 카드를 그린다. */
// 권장 조치 아이콘 — 리포트에서 가장 눈에 먼저 들어오는 자리다.
// 이모지는 기기·OS마다 모양과 색이 달라서(특히 🚑/🚨는 플랫폼별 차이가 크다)
// 위급도 단계를 색과 함께 읽어야 하는 요소에는 쓰지 않는다. 앱 전체 규칙과 동일한 선형 SVG.
const TRIAGE_ICONS = {
    urgent:  '<svg viewBox="0 0 24 24" fill="none"><path d="M3.5 8.5h9v8h-9z"/><path d="M12.5 11h4l4 3.5v2h-8z"/><circle cx="7" cy="18.5" r="1.9"/><circle cx="17" cy="18.5" r="1.9"/><path d="M8 10.5v4M6 12.5h4"/></svg>',
    now:     '<svg viewBox="0 0 24 24" fill="none"><path d="M12 8.6v4.2M12 16.4h.01"/><path d="M10.3 3.9 2.7 17.1A2 2 0 0 0 4.4 20h15.2a2 2 0 0 0 1.7-2.9L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>',
    weeks:   '<svg viewBox="0 0 24 24" fill="none"><rect x="3.5" y="5" width="17" height="15.5" rx="2"/><path d="M3.5 9.8h17M8 3.2v3.6M16 3.2v3.6"/><path d="M11 13.5h5"/></svg>',
    monitor: '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="8.6"/><path d="m8.2 12.3 2.7 2.7 5-5.3"/></svg>',
};

function renderTriage(container, triage, factors) {
    const t = translations[state.lang];
    container.innerHTML = '';

    const style = {
        urgent:  { bg: 'bg-rose-100',   br: 'border-rose-400',    tx: 'text-rose-800',    ico: TRIAGE_ICONS.urgent },
        now:     { bg: 'bg-rose-50',    br: 'border-rose-200',    tx: 'text-rose-700',    ico: TRIAGE_ICONS.now },
        weeks:   { bg: 'bg-amber-50',   br: 'border-amber-200',   tx: 'text-amber-800',   ico: TRIAGE_ICONS.weeks },
        monitor: { bg: 'bg-emerald-50', br: 'border-emerald-200', tx: 'text-emerald-700', ico: TRIAGE_ICONS.monitor },
    }[triage.level];

    const box = document.createElement('div');
    box.className = `${style.bg} border ${style.br} rounded-2xl p-4`;

    const head = document.createElement('p');
    head.className = 'text-[10px] font-black text-slate-400 mb-1';
    head.textContent = t.tri_title || '권장 조치';
    box.appendChild(head);

    const main = document.createElement('p');
    main.className = `tri-main font-black text-sm ${style.tx}`;
    const mainIco = document.createElement('span');
    mainIco.className = 'tri-ico';
    mainIco.setAttribute('aria-hidden', 'true');
    mainIco.innerHTML = style.ico;              // 고정 상수 (아래 TRIAGE_ICONS)
    const mainTxt = document.createElement('span');
    mainTxt.textContent = triage.label;         // 서버/번역 문자열은 항상 textContent
    main.append(mainIco, mainTxt);
    box.appendChild(main);

    const why = document.createElement('p');
    why.className = 'text-[11px] text-slate-500 mt-1 leading-relaxed';
    why.textContent = triage.why;
    box.appendChild(why);

    // 판정이 'uncertain'일 때만 붙는 재촬영 안내. 진료 시점(triage.level)은 바꾸지 않고,
    // "이번 사진으로는 판단이 어려웠다"는 사실만 권장 조치 자리에서도 말해준다 —
    // 바로 위 검사 요약과 서로 반대되는 말을 하지 않도록.
    if (triage.note) {
        const note = document.createElement('p');
        note.className = 'text-[11px] font-bold text-slate-600 mt-2 leading-relaxed';
        note.textContent = triage.note;
        box.appendChild(note);
    }

    if (factors && factors.length) {
        // 총점(RISK_MAX 만점)은 표시하지 않는다 — 임상 검증된 지표가 아닌데 숫자로 보여주면
        // 사용자가 의료 등급으로 받아들인다. 항목만 '정기검진을 권하는 이유'로 제시한다.
        const f = document.createElement('p');
        f.className = 'text-[11px] text-slate-500 mt-2 leading-relaxed';
        f.textContent = (t.tri_factors || '정기 검진을 권하는 이유: {items}')
            .replace('{items}', factors.join(', '));
        box.appendChild(f);
    }
    container.appendChild(box);
}

// ------------------------------------------------------------------
// 저장 동의 — 건강정보는 민감정보라 별도 동의가 필요하다.
// 동의 전에는 어떤 결과도 서버로 보내지 않는다. 사진은 애초에 저장하지 않는다.
// ------------------------------------------------------------------
function requestSaveConsent(payload) {
    const t = translations[state.lang];
    const box = document.getElementById('consent-box');
    if (!box) return;
    box.innerHTML = '';
    box.classList.remove('hidden');

    const wrap = document.createElement('div');
    wrap.className = 'bg-slate-50 border border-slate-200 rounded-2xl p-4';

    const title = document.createElement('p');
    title.className = 'text-[10px] font-black text-slate-400 mb-1';
    title.textContent = t.consent_title || '결과 저장 동의';

    const body = document.createElement('p');
    body.className = 'text-[11px] text-slate-500 leading-relaxed mb-3';
    body.textContent = t.consent_text || '';

    const row = document.createElement('div');
    row.className = 'flex gap-2';

    const agree = document.createElement('button');
    agree.className = 'flex-1 py-2.5 bg-blue-600 text-white rounded-xl font-bold text-[12px] btn-pop';
    agree.textContent = t.consent_agree || '동의하고 저장';
    // 저장 결과를 사용자에게 알린다. 서버는 DB 장애 시에도 200 + status:'skipped'를
    // 돌려주므로(앱을 죽이지 않기 위해) 상태 코드만 보면 '성공'으로 착각한다.
    // 동의까지 받아놓고 실제로는 저장이 안 됐다면 그 사실을 알려야 한다.
    const status = document.createElement('p');
    status.className = 'text-[11px] font-bold mt-2';
    agree.onclick = async () => {
        agree.disabled = true;
        status.className = 'text-[11px] font-bold mt-2 text-slate-500';
        status.textContent = t.save_saving || '저장 중...';
        if (!wrap.contains(status)) wrap.appendChild(status);
        try {
            const res = await fetch('/api/save-diagnosis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.status === 'saved') {
                status.className = 'text-[11px] font-bold mt-2 text-emerald-600';
                status.textContent = t.save_done || '저장했습니다.';
                setTimeout(() => box.classList.add('hidden'), 1200);
            } else {
                throw new Error(data.status || 'failed');
            }
        } catch (e) {
            status.className = 'text-[11px] font-bold mt-2 text-amber-700';
            status.textContent = t.save_failed || '저장하지 못했습니다. 결과는 화면에서 계속 보실 수 있습니다.';
            agree.disabled = false;
            agree.textContent = t.save_retry || '다시 시도';
        }
    };

    const skip = document.createElement('button');
    skip.className = 'flex-1 py-2.5 bg-slate-100 text-slate-600 rounded-xl font-bold text-[12px] btn-pop';
    skip.textContent = t.consent_skip || '저장하지 않기';
    skip.onclick = () => box.classList.add('hidden');

    row.appendChild(agree); row.appendChild(skip);
    wrap.appendChild(title); wrap.appendChild(body); wrap.appendChild(row);
    box.appendChild(wrap);
}
