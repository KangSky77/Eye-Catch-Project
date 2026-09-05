const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function setup() {
    const elements = new Map();
    const element = id => {
        if (!elements.has(id)) {
            const classes = new Set();
            elements.set(id, { innerText: '', textContent: '', innerHTML: '',
                appendChild() {}, querySelector() { return null; },
                classList: { add: c => classes.add(c), remove: c => classes.delete(c),
                    contains: c => classes.has(c), toggle(c, force) {
                        if (force) classes.add(c); else classes.delete(c);
                    } } });
        }
        return elements.get(id);
    };
    const calls = [], saves = [], loaders = [];
    const context = { console, AbortController, window: { addEventListener() {} },
        state: { lang: 'ko', opinionRequest: null }, translations: { ko: {}, en: {} },
        document: { getElementById: element },
        formatCataractResult: () => 'current', formatAmslerResult: () => 'current',
        formatSymptoms: () => [], computeRiskScore: () => ({ factors: [] }),
        createAiLoader() { const loader = { el: {}, stopped: false, stop() { this.stopped = true; } };
            loaders.push(loader); return loader; },
        fetch(url, options) { return new Promise(resolve => calls.push({ options, resolve })); },
        async readAiStream(response, update) {
            update(response.text);
            if (response.wait) await response.wait;
            update(response.text);
            return { text: response.text, hasError: !!response.error };
        } };
    vm.createContext(context);
    vm.runInContext(fs.readFileSync(path.join(__dirname, '../static/app-report.js'), 'utf8'), context);
    const core = fs.readFileSync(path.join(__dirname, '../static/app-core.js'), 'utf8');
    vm.runInContext(core.slice(core.indexOf('function resetScreeningState()'), core.indexOf('\nfunction openMap()')), context);
    context.requestSaveConsent = data => saves.push(data);
    const request = label => ({ lang: 'ko', cataract_res: label, amsler_res: label, chat_symptoms: [label] });
    return { context, calls, saves, loaders, element, request };
}

test('restart aborts pending fetch; late old response cannot overwrite new report or consent', async () => {
    const h = setup(), c = h.context;
    c.state.opinionRequest = h.request('old');
    const old = c.runAiOpinion();
    c.resetScreeningState();
    assert.equal(h.calls[0].options.signal.aborted, true);
    assert.equal(h.loaders[0].stopped, true);
    c.state.opinionRequest = h.request('new');
    const next = c.runAiOpinion();
    h.calls[1].resolve({ ok: true, text: 'new opinion' }); await next;
    h.calls[0].resolve({ ok: true, text: 'old opinion' }); await old;
    assert.equal(h.element('gemma-opinion-text').innerText, 'new opinion');
    assert.equal(h.saves.length, 1);
    assert.equal(h.saves[0].cataract_result, 'new');
    assert.equal(h.saves[0].gemma_opinion, 'new opinion');
});

test('restart during token streaming ignores later tokens and completion', async () => {
    const h = setup(), c = h.context;
    let release;
    c.state.opinionRequest = h.request('old');
    const old = c.runAiOpinion();
    h.calls[0].resolve({ ok: true, text: 'old tokens', wait: new Promise(r => release = r) });
    await new Promise(r => setImmediate(r));
    c.resetScreeningState();
    h.element('gemma-opinion-text').innerText = 'new screen';
    release(); await old;
    assert.equal(h.element('gemma-opinion-text').innerText, 'new screen');
    assert.equal(h.saves.length, 0);
    assert.equal(c.state.opinionLang, '');
});

test('language change records original request language and displays regeneration notice', async () => {
    const h = setup(), c = h.context;
    c.state.opinionRequest = h.request('original');
    const pending = c.runAiOpinion();
    c.state.lang = 'en'; c.state.opinionRequest.lang = 'en';
    h.calls[0].resolve({ ok: true, text: 'Korean opinion' }); await pending;
    assert.equal(c.state.opinionLang, 'ko');
    assert.equal(h.element('opinion-stale').classList.contains('hidden'), false);
    const regenerated = c.regenerateOpinion();
    assert.equal(JSON.parse(h.calls[1].options.body).lang, 'en');
    h.calls[1].resolve({ ok: true, text: 'English opinion' });
    await new Promise(r => setImmediate(r));
    assert.equal(c.state.opinionLang, 'en');
    assert.equal(h.element('opinion-stale').classList.contains('hidden'), true);
});

test('failed response offers retry without consent; retry succeeds', async () => {
    const h = setup(), c = h.context;
    c.state.opinionRequest = h.request('current');
    const first = c.runAiOpinion();
    h.calls[0].resolve({ ok: false, status: 503 }); await first;
    assert.equal(h.saves.length, 0);
    assert.equal(h.element('opinion-retry').classList.contains('hidden'), false);
    const retry = c.runAiOpinion();
    h.calls[1].resolve({ ok: true, text: 'recovered' }); await retry;
    assert.equal(h.saves.length, 1);
    assert.equal(h.element('opinion-retry').classList.contains('hidden'), true);
});
