// 검사 요약 해석의 '쉬운 말' 보기 — 검증을 통과한 줄만 바뀌고, 실패하면 원문이 그대로 남아야 한다.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function el() {
    const node = {
        className: '', textContent: '', id: '', disabled: false, onclick: null,
        type: '', children: [],
        appendChild(child) { this.children.push(child); return child; },
        querySelector() { return null; },
        classList: { add() {}, remove() {}, contains: () => false, toggle() {} },
    };
    // renderFindings는 container.innerHTML = '' 로 화면을 비운다 — 가짜 DOM도 같이 비워야
    // 다시 그린 결과가 아니라 예전 렌더 결과를 읽는 일이 없다.
    Object.defineProperty(node, 'innerHTML', { get() { return ''; }, set(v) { if (!v) this.children = []; } });
    return node;
}

function setup(lines) {
    const box = el();
    const calls = [];
    const context = {
        console, JSON, Promise, setTimeout, fetch: (url, options) => {
            calls.push({ url, body: JSON.parse(options.body) });
            return Promise.resolve(lines === 'fail'
                ? { ok: false, json: async () => ({}) }
                : { ok: true, json: async () => ({ lines }) });
        },
        showToast: (m) => context.toasts.push(m),
        toasts: [],
        window: { addEventListener() {} },
        document: { createElement: () => el(), getElementById: id => (id === 'findings-box' ? box : null) },
        state: {
            lang: 'ko', aiResultCode: 'normal', aiResultData: { code: 'normal' },
            amslerResult: { left: false, right: false }, hasAmsler: false,
            riskAnswers: {}, symptomAnswers: {}, chatSymptoms: [], symptomCodes: [],
        },
    };
    vm.createContext(context);
    for (const file of ['data.js', 'app-report-text.js', 'app-surgery.js', 'app-findings.js']) {
        vm.runInContext(fs.readFileSync(path.join(__dirname, '../static', file), 'utf8'), context);
    }
    const shown = () => box.children[1].children.map(li => li.children[1].textContent).join(' ||| ');
    return { context, box, calls, shown, fixed: () => [...context.buildFindings()].join(' ||| ') };
}

test('기본은 코드가 만든 원래 문장을 보여준다', () => {
    const h = setup([]);
    h.context.renderFindings(h.box);
    assert.equal(h.shown(), h.fixed());
    assert.equal(h.calls.length, 0, '보기만 해도 서버를 부르면 안 된다');
});

test('검증을 통과한 줄만 쉬운 말로 바뀌고 나머지는 원문이 남는다', async () => {
    const probe = setup([]);
    probe.context.renderFindings(probe.box);
    const fixed = [...probe.context.buildFindings()];
    // 첫 줄만 검증 통과(rewritten), 나머지는 서버가 원문을 되돌려준 상태
    const lines = fixed.map((text, i) => i === 0 ? { text: '쉬운 말 첫 줄', rewritten: true } : { text, rewritten: false });

    const h = setup(lines);
    h.context.renderFindings(h.box);
    await h.context.togglePlainFindings();
    assert.equal(h.calls[0].body.findings.length, fixed.length);
    assert.equal(h.shown(), ['쉬운 말 첫 줄', ...fixed.slice(1)].join(' ||| '));

    // 다시 누르면 원래 문장으로 돌아오고, 서버를 또 부르지 않는다
    await h.context.togglePlainFindings();
    assert.equal(h.shown(), fixed.join(' ||| '));
    assert.equal(h.calls.length, 1);
});

test('서버가 실패하면 원래 문장을 그대로 두고 알린다', async () => {
    const h = setup('fail');
    h.context.renderFindings(h.box);
    const fixed = h.fixed();
    await h.context.togglePlainFindings();
    assert.equal(h.shown(), fixed);
    assert.equal(h.context.toasts.length, 1);
});

test('줄 수가 어긋난 응답은 쓰지 않는다', async () => {
    const h = setup([{ text: '한 줄만 왔다', rewritten: true }]);
    h.context.renderFindings(h.box);
    const fixed = [...h.context.buildFindings()];
    if (fixed.length === 1) return;          // 줄이 하나뿐인 구성에서는 이 검사가 의미 없다
    await h.context.togglePlainFindings();
    assert.equal(h.shown(), fixed.join(' ||| '));
    assert.equal(h.context.toasts.length, 1);
});
