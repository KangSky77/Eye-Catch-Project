// ==========================================================================
// scripts/check_i18n_limits.js — 6개국어 번역의 정합성·길이 상한 검사
//
// 왜 필요한가:
//   1) 언어별 키 누락: 한 언어에만 키를 추가하면 다른 언어 사용자에게는 폴백 문구나
//      키 이름이 그대로 노출된다. 브라우저에서는 에러가 나지 않아 알아채기 어렵다.
//   2) 서버 스키마 길이 상한: 판정 문구는 formatCataractResult()에서 한 문장으로
//      합쳐져 cataract_res(상한 200자)로 서버에 간다. 넘으면 422가 나고 사용자에게는
//      '서버 연결 오류'로 보인다 — 실제로 100자 상한 시절 fr/es에서 터진 적이 있다.
//
// 실행:  node scripts/check_i18n_limits.js
//   (문제가 있으면 종료 코드 1 — pytest에도 같은 검사가 들어 있다:
//    tests/test_static_assets.py::test_판정문구가_서버_스키마_길이_상한을_넘지_않는다)
//
// 상한값의 출처는 app/schemas/ai.py다. 스키마를 바꾸면 아래 LIMITS도 함께 고칠 것.
// ==========================================================================
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');

// app/schemas/ai.py의 Field(max_length=...)와 짝이 맞아야 한다
const LIMITS = { cataract_res: 200, amsler_res: 100, symptom_item: 100 };

function loadData() {
    const src = fs.readFileSync(path.join(ROOT, 'static', 'data.js'), 'utf8');
    // data.js는 브라우저용 전역 스크립트라 module 시스템이 없다 — vm으로 그대로 평가한다.
    const ctx = { window: {}, document: {} };
    vm.createContext(ctx);
    vm.runInContext(src + '\n;globalThis.__t = translations;'
        + 'globalThis.__e = (typeof extraStrings !== "undefined") ? extraStrings : {};', ctx);
    return { t: ctx.__t, e: ctx.__e };
}

const problems = [];
const { t, e } = loadData();
const langs = Object.keys(t);
const get = (l, k) => ({ ...t[l], ...(e[l] || {}) })[k] || '';

// --- 1) 키 정합성 (ko 기준) ---
for (const table of [['translations', t], ['extraStrings', e]]) {
    const [name, obj] = table;
    const base = Object.keys(obj.ko || {});
    for (const l of langs) {
        if (l === 'ko') continue;
        const have = new Set(Object.keys(obj[l] || {}));
        const missing = base.filter(k => !have.has(k));
        const extra = [...have].filter(k => !base.includes(k));
        if (missing.length) problems.push(`${name}.${l}: 키 누락 ${missing.length}개 — ${missing.slice(0, 10).join(', ')}`);
        if (extra.length) problems.push(`${name}.${l}: ko에 없는 키 ${extra.length}개 — ${extra.slice(0, 10).join(', ')}`);
    }
}

// --- 2) 길이 상한 ---
// formatCataractResult()(static/app-core.js)가 만드는 최장 문자열을 그대로 재현한다.
// 점수는 최대 3자리 + 소수 1자리("100.0")를 가정해 넉넉히 잡는다.
const SCORE = '100.0';
const CODES = ['ai_risk', 'ai_borderline', 'ai_uncertain', 'ai_normal'];
const report = [];
for (const l of langs) {
    let worst = 0, worstText = '';
    for (const c of CODES) {
        const twoEyes = `${get(l, c)} · ${get(l, 'score_label')} ${get(l, 'eye_left')} ${SCORE}/100 / ${get(l, 'eye_right')} ${SCORE}/100`;
        const oneEye = `${get(l, c)} · ${get(l, 'score_label')} ${SCORE}/100`;
        for (const s of [twoEyes, oneEye]) if (s.length > worst) { worst = s.length; worstText = s; }
    }
    if (worst > LIMITS.cataract_res) {
        problems.push(`${l}: cataract_res ${worst}자 > 상한 ${LIMITS.cataract_res}자\n    ${worstText}`);
    }

    const ams = Math.max(...['ams_result_bad', 'ams_result_left', 'ams_result_right', 'ams_result_both']
        .map(k => get(l, k).length));
    if (ams > LIMITS.amsler_res) {
        problems.push(`${l}: amsler_res ${ams}자 > 상한 ${LIMITS.amsler_res}자`);
    }

    const symKeys = Object.keys({ ...t[l], ...(e[l] || {}) }).filter(k => /^(sym_|symptom_extra$)/.test(k));
    const sym = Math.max(0, ...symKeys.map(k => get(l, k).length));
    if (sym > LIMITS.symptom_item) {
        problems.push(`${l}: chat_symptoms 항목 ${sym}자 > 상한 ${LIMITS.symptom_item}자`);
    }

    const headroom = LIMITS.cataract_res - worst;
    report.push(`  ${l}: cataract_res ${String(worst).padStart(3)}자 (여유 ${headroom})`
        + ` | amsler_res ${ams}자 | sym 최장 ${sym}자`);
}

console.log(`언어 ${langs.length}개: ${langs.join(', ')}`);
console.log(`translations 키 ${Object.keys(t.ko).length}개 / extraStrings 키 ${Object.keys(e.ko || {}).length}개`);
console.log(report.join('\n'));

if (problems.length) {
    console.error('\n❌ 문제 ' + problems.length + '건\n - ' + problems.join('\n - '));
    process.exit(1);
}
console.log('\n✅ 키 정합성·길이 상한 모두 통과');
