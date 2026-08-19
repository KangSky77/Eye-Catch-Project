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
//   나이 0~4   노화가 백내장·황반변성·녹내장 공통 최대 위험요인
//   당뇨 3     당뇨망막병증의 직접 원인이며 백내장도 앞당긴다
//   가족력 2   녹내장·황반변성은 가족력 기여가 크다
//   흡연 2     황반변성·백내장 위험을 뚜렷이 높인다
//   고혈압 1   망막혈관 손상에 기여
// 최대 12점.
const RISK_MAX = 12;

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
 *   now     빠른 시일 내 진료   — 위험 소견이 있거나, 경계 소견 + 높은 위험도
 *   weeks   수 주 내 검진      — 경계 소견, 암슬러 이상, 증상, 또는 높은 위험도
 *   monitor 경과 관찰          — 특별한 신호 없음
 * 등급이 아니라 '다음 행동'을 돌려주는 것이 이 함수의 요점.
 */
function computeTriage(ctx) {
    const risk = ctx.riskScore || 0;
    const highRisk = risk >= 6;
    const anySymptom = (ctx.symptomCodes || []).length > 0;

    let level;
    if (ctx.cataractCode === 'risk' || ctx.amslerAbnormal) {
        level = 'now';
    } else if (ctx.cataractCode === 'borderline') {
        level = highRisk ? 'now' : 'weeks';
    } else if (ctx.visionAsymmetric) {
        // 사진은 정상이어도 좌우 기능 차이가 크면 확인이 필요하다
        level = 'weeks';
    } else if (anySymptom || highRisk) {
        level = 'weeks';
    } else {
        level = 'monitor';
    }

    const t = translations[state.lang];
    return {
        level,
        label: t['tri_' + level] || level,
        why: t['tri_' + level + '_why'] || '',
        riskScore: risk,
        riskMax: RISK_MAX,
    };
}

/** 리포트에 행동 권고 카드를 그린다. */
function renderTriage(container, triage, factors) {
    const t = translations[state.lang];
    container.innerHTML = '';

    const style = {
        now:     { bg: 'bg-rose-50',    br: 'border-rose-200',    tx: 'text-rose-700',    ico: '🚨' },
        weeks:   { bg: 'bg-amber-50',   br: 'border-amber-200',   tx: 'text-amber-800',   ico: '📅' },
        monitor: { bg: 'bg-emerald-50', br: 'border-emerald-200', tx: 'text-emerald-700', ico: '✅' },
    }[triage.level];

    const box = document.createElement('div');
    box.className = `${style.bg} border ${style.br} rounded-2xl p-4`;

    const head = document.createElement('p');
    head.className = 'text-[10px] font-black text-slate-400 mb-1';
    head.textContent = t.tri_title || '권장 조치';
    box.appendChild(head);

    const main = document.createElement('p');
    main.className = `font-black text-sm ${style.tx}`;
    main.textContent = `${style.ico} ${triage.label}`;
    box.appendChild(main);

    const why = document.createElement('p');
    why.className = 'text-[11px] text-slate-500 mt-1 leading-relaxed';
    why.textContent = triage.why;
    box.appendChild(why);

    if (factors && factors.length) {
        const f = document.createElement('p');
        f.className = 'text-[11px] text-slate-500 mt-2';
        f.textContent = `· ${factors.join(', ')} (${triage.riskScore}/${triage.riskMax})`;
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
    agree.onclick = () => {
        fetch('/api/save-diagnosis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).catch(() => {});          // 저장 실패는 조용히 무시 (UX 영향 없음)
        box.classList.add('hidden');
    };

    const skip = document.createElement('button');
    skip.className = 'flex-1 py-2.5 bg-slate-100 text-slate-600 rounded-xl font-bold text-[12px] btn-pop';
    skip.textContent = t.consent_skip || '저장하지 않기';
    skip.onclick = () => box.classList.add('hidden');

    row.appendChild(agree); row.appendChild(skip);
    wrap.appendChild(title); wrap.appendChild(body); wrap.appendChild(row);
    box.appendChild(wrap);
}
