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
        urgent:  { bg: 'bg-rose-100',   br: 'border-rose-400',    tx: 'text-rose-800',    ico: '🚑' },
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
        // 총점(n/12)은 표시하지 않는다 — 임상 검증된 지표가 아닌데 숫자로 보여주면
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
