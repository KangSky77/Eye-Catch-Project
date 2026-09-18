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

test('detail is collapsed, summary is displayed, and full advice is saved', async () => {
    const h = setup(), c = h.context;
    c.state.opinionRequest = h.request('surgery');
    const pending = c.runAiOpinion();
    h.calls[0].resolve({ ok: true, text: 'Detailed advice.\n<<<SUMMARY>>>\nFirst.\nSecond.\nThird.' });
    await pending;
    assert.equal(h.element('gemma-opinion-text').innerText, 'First.\nSecond.\nThird.');
    assert.equal(h.element('opinion-detail-text').textContent, 'Detailed advice.');
    assert.equal(h.element('opinion-details').open, false);
    assert.match(h.saves[0].gemma_opinion, /Detailed advice/);
    c.cancelAiOpinion();
    assert.equal(h.element('opinion-details').classList.contains('hidden'), true);
    assert.equal(c.state.opinionFullText, '');
});

test('empty summary marker falls back to advice and empty advice cannot be saved', async () => {
 const h=setup(), c=h.context;
 c.state.opinionRequest=h.request('fallback');
 let pending=c.runAiOpinion();
 h.calls[0].resolve({ok:true,text:'Useful advice.\n<<<SUMMARY>>>\n'});await pending;
 assert.equal(c.state.opinionSummaryText,'Useful advice.');
 pending=c.runAiOpinion();h.calls[1].resolve({ok:true,text:'<<<SUMMARY>>>'});await pending;
 assert.equal(c.state.opinionSummaryText,'');
 assert.equal(h.saves.length,1);
});

test('PDF waits only while advice is streaming; failed advice and photo-less sessions still export', async () => {
 // 예전에는 요약이 없으면 무조건 막아, Ollama가 꺼져 있거나 '사진 없이 증상 확인'으로 끝낸 사람은
 // PDF를 영영 받을 수 없었다. 기다리게 하는 것은 소견을 '만드는 중'일 때뿐이어야 한다.
 const h=setup(),c=h.context,notices=[];let saved=0;
 const tick=()=>new Promise(r=>setImmediate(r));
 // .save()가 아니라 blob을 받아 <a download>로 내려받는다(팝업 차단·무한 대기 회피).
 const anchor={click(){},remove(){},set href(v){},set download(v){}};
 Object.assign(c,{showToast:m=>notices.push(m),setButtonBusy:()=>()=>{},hasCompletedScreening:()=>true,
  buildReportPdf:()=>({outputPdf:()=>{saved++;return Promise.resolve({});}}),
  URL:{createObjectURL:()=>'blob:x',revokeObjectURL(){}},
  setTimeout:(fn,ms)=>(ms>1000?0:setImmediate(fn))});
 c.document.createElement=()=>anchor;
 c.document.body={appendChild(){},removeChild(){}};
 c.window.scrollTo=()=>{};
 c.translations.ko.pdf_wait_opinion='Wait';
 c.state.opinionRequest=h.request('x');
 const pending=c.runAiOpinion();
 c.downloadPDF();assert.deepEqual(notices,['Wait']);assert.equal(saved,0);
 h.calls[0].resolve({ok:true,text:'x',error:true});await pending;      // 소견 생성 실패
 assert.equal(c.state.opinionSummaryText,'');
 c.downloadPDF();await tick();assert.equal(saved,1,'실패한 소견 때문에 PDF가 막혔다');
 c.state.aiResultData=null;                                             // 사진 없이 끝낸 회차
 c.downloadPDF();await tick();assert.equal(saved,2,'사진 없는 회차가 PDF를 못 받았다');
 c.hasCompletedScreening=()=>false;                                     // 검사를 안 끝냈으면 막는다
 c.downloadPDF();await tick();assert.equal(saved,2);assert.equal(notices.length,2);
});

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
