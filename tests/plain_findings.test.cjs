// 검사 요약 해석의 '쉬운 말' 보기 — 준비된 표현만 쓰고, 회차·언어가 바뀌면 이전 결과를 버린다.
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
        console, JSON, Promise, AbortController, setTimeout, clearTimeout, fetch: (url, options) => {
            calls.push({ url, body: JSON.parse(options.body) });
            return Promise.resolve(lines === 'fail'
                ? { ok: false, json: async () => ({}) }
                : { ok: true, json: async () => ({ lines }) });
        },
        showToast: (m) => context.toasts.push(m),
        cancelAiOpinion() {},
        toasts: [],
        window: { addEventListener() {} },
        document: { createElement: () => el(), getElementById: id => (id === 'findings-box' ? box : null) },
        state: {
            lang: 'ko', sessionGeneration: 0, aiResultCode: 'normal', aiResultData: { code: 'normal' },
            amslerResult: { left: false, right: false }, hasAmsler: false,
            riskAnswers: {}, symptomAnswers: {}, chatSymptoms: [], symptomCodes: [],
        },
    };
    vm.createContext(context);
    for (const file of ['data.js', 'app-report-text.js', 'app-surgery.js', 'app-findings.js']) {
        vm.runInContext(fs.readFileSync(path.join(__dirname, '../static', file), 'utf8'), context);
    }
    const core = fs.readFileSync(path.join(__dirname, '../static/app-core.js'), 'utf8');
    vm.runInContext(core.slice(core.indexOf('function resetScreeningState()'), core.indexOf('\nfunction openMap()')), context);
    const shown = () => box.children[1].children.map(li => li.children[1].textContent).join(' ||| ');
    return { context, box, calls, shown, fixed: () => [...context.buildFindings()].join(' ||| ') };
}

test('기본은 코드가 만든 원래 문장을 보여준다', () => {
    const h = setup([]);
    h.context.renderFindings(h.box);
    assert.equal(h.shown(), h.fixed());
    assert.equal(h.calls.length, 0, '보기만 해도 서버를 부르면 안 된다');
});

function pendingRequests(h) {
    const pending = [];
    h.context.fetch = (url, options) => new Promise((resolve, reject) => {
        const body = JSON.parse(options.body);
        // Deliberately ignore abort: even a response already in flight must be discarded.
        pending.push({ reject, signal: options.signal, resolve: () => resolve({
            ok: true, json: async () => ({ lines: body.findings.map(text => ({ text: `${body.lang}: ${text}`, rewritten: true })) })
        }) });
    });
    return pending;
}

test('new screening discards both cached findings and pending responses', async () => {
    for (const completeFirst of [false, true]) {
        const h = setup([]), c = h.context, pending = pendingRequests(h);
        const first = c.togglePlainFindings();
        if (completeFirst) { pending[0].resolve(); await first; }
        c.resetScreeningState();
        c.state.aiResultCode = 'risk';
        c.renderFindings(h.box);
        assert.equal(h.shown(), h.fixed());
        if (!completeFirst) { pending[0].resolve(); await first; }
        assert.equal(h.shown(), h.fixed(), 'late old result must not replace the new risk finding');
        const next = c.togglePlainFindings();
        assert.equal(pending.length, 2, 'new screening must request its own wording');
        pending[1].resolve(); await next;
        assert.match(h.shown(), /강하게/);
        assert.doesNotMatch(h.shown(), /감지하지 않았습니다/);
    }
});

test('changed findings invalidate cached wording even within the same session', async () => {
    const h = setup([]), c = h.context, pending = pendingRequests(h);
    const first = c.togglePlainFindings(); pending[0].resolve(); await first;
    c.state.aiResultCode = 'risk'; c.renderFindings(h.box);
    assert.equal(h.shown(), h.fixed());
    const next = c.togglePlainFindings();
    assert.equal(pending.length, 2);
    pending[1].resolve(); await next;
    assert.match(h.shown(), /강하게/);
});

test('language switch discards the old response and permits a fresh request', async () => {
    const h = setup([]), c = h.context, pending = pendingRequests(h);
    const old = c.togglePlainFindings();
    c.state.lang = 'en'; c.renderFindings(h.box);
    pending[0].resolve(); await old;
    assert.equal(h.shown(), h.fixed());
    const next = c.togglePlainFindings();
    pending[1].resolve(); await next;
    assert.match(h.shown(), /^en:/);
    assert.doesNotMatch(h.shown(), /백내장/);
});

test('old success or failure cannot overwrite a newer language request', async () => {
    for (const fail of [false, true]) {
        const h = setup([]), c = h.context, pending = pendingRequests(h);
        const old = c.togglePlainFindings();
        c.state.lang = 'en'; c.renderFindings(h.box);
        const next = c.togglePlainFindings();
        pending[1].resolve(); await next;
        const expected = h.shown();
        if (fail) pending[0].reject(new Error('old request failed'));
        else pending[0].resolve();
        await old;
        assert.equal(h.shown(), expected);
        assert.equal(c.toasts.length, 0);
    }
});

test('switching language away and back does not revive an invalidated response', async () => {
    const h = setup([]), c = h.context, pending = pendingRequests(h);
    const old = c.togglePlainFindings();
    c.state.lang = 'en'; c.renderFindings(h.box);
    c.state.lang = 'ko'; c.renderFindings(h.box);
    pending[0].resolve(); await old;
    assert.equal(h.shown(), h.fixed());
});

test('준비된 표현이 있는 줄만 쉬운 말로 바뀌고 나머지는 원문이 남는다', async () => {
    const probe = setup([]);
    probe.context.renderFindings(probe.box);
    const fixed = [...probe.context.buildFindings()];
    // 첫 줄만 준비된 표현이 있고(rewritten), 나머지는 서버가 원문을 되돌려준 상태
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

test('fixed wording catalog matches current source sentences in every language', () => {
    const h = setup([]);
    const catalog = JSON.parse(fs.readFileSync(path.join(__dirname, '../app/services/plain_findings.json'), 'utf8'));
    const translations = vm.runInContext('translations', h.context);
    assert.deepEqual(Object.keys(catalog).sort(), Object.keys(translations).sort());
    for (const [lang, entries] of Object.entries(catalog)) {
        for (const [key, entry] of Object.entries(entries)) {
            assert.equal(entry.original, translations[lang][key], `${lang}.${key}: review the plain wording when changing the source`);
            assert.ok(entry.plain.trim(), `${lang}.${key}`);
            assert.notEqual(entry.plain, entry.original, `${lang}.${key}`);
        }
    }
});

test('malformed line objects fall back instead of displaying blank findings', async () => {
    for (const badLine of [null, { text: '', rewritten: true }, { text: 'oops', rewritten: 'yes' }]) {
        const h = setup([]);
        h.context.fetch = async () => ({ ok: true, json: async () => ({
            lines: [...h.context.buildFindings()].map(() => badLine)
        }) });
        await h.context.togglePlainFindings();
        assert.equal(h.shown(), h.fixed());
        assert.equal(h.context.toasts.length, 1);
    }
});
