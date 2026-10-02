const { readReportScripts } = require('./helpers/report-scripts.cjs');
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
                appendChild() {}, querySelector() { return null; }, removeAttribute() {}, setAttribute() {},
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
    context.setTimeout = setTimeout; context.clearTimeout = clearTimeout;
    vm.runInContext(readReportScripts(), context);
    const core = fs.readFileSync(path.join(__dirname, '../static/app-core.js'), 'utf8');
    vm.runInContext(core.slice(core.indexOf('function resetScreeningState()'), core.indexOf('\nfunction openMap()')), context);
    context.requestSaveConsent = data => saves.push(data);
    const request = label => ({ lang: 'ko', cataract_res: label, amsler_res: label, chat_symptoms: [label] });
    return { context, calls, saves, loaders, element, request };
}

test('urgent reports do not invite or send further AI questions and normal reports restore the form', async () => {
    const h = setup(), c = h.context;
    c.translations.ko.report_urgent_title = 'Urgent guidance';
    c.translations.ko.rep_info_title = 'AI advice';
    c.state.triage = { level: 'urgent' };
    c.refreshReportResults();
    assert.equal(h.element('opinion-section-title').innerText, 'Urgent guidance');
    assert.equal(h.element('followup-box').classList.contains('hidden'), true);
    h.element('user-followup-input').value = 'Can I wait until tomorrow?';
    await c.askGemmaMore();
    assert.equal(h.calls.length, 0);
    c.state.triage = { level: 'monitor' };
    c.refreshReportResults();
    assert.equal(h.element('opinion-section-title').innerText, 'AI advice');
    assert.equal(h.element('followup-box').classList.contains('hidden'), false);
});

test('detail is collapsed and full advice stays available for PDF without a server save', async () => {
    const h = setup(), c = h.context;
    c.state.opinionRequest = h.request('surgery');
    const pending = c.runAiOpinion();
    h.calls[0].resolve({ ok: true, text: 'Detailed advice.\n<<<SUMMARY>>>\nFirst.\nSecond.\nThird.' });
    await pending;
    assert.equal(h.element('gemma-opinion-text').innerText, 'First.\nSecond.\nThird.');
    assert.equal(h.element('opinion-detail-text').textContent, 'Detailed advice.');
    assert.equal(h.element('opinion-details').open, false);
    assert.match(c.state.opinionFullText, /Detailed advice/);
    assert.equal(h.saves.length, 0);
    c.cancelAiOpinion();
    assert.equal(h.element('opinion-details').classList.contains('hidden'), true);
    assert.equal(c.state.opinionFullText, '');
});

test('empty summary marker falls back to advice and empty advice fails safely', async () => {
 const h=setup(), c=h.context;
 c.state.opinionRequest=h.request('fallback');
 let pending=c.runAiOpinion();
 h.calls[0].resolve({ok:true,text:'Useful advice.\n<<<SUMMARY>>>\n'});await pending;
 assert.equal(c.state.opinionSummaryText,'Useful advice.');
 pending=c.runAiOpinion();h.calls[1].resolve({ok:true,text:'<<<SUMMARY>>>'});await pending;
 assert.equal(c.state.opinionSummaryText,'');
 assert.equal(h.saves.length,0);
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
  setTimeout:(fn,ms)=>(ms>1000?0:setImmediate(fn)),clearTimeout() {}});
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
    assert.equal(h.saves.length, 0);
    assert.equal(c.state.opinionFullText, 'new opinion');
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

test('failed response offers retry; success still never requests server storage', async () => {
    const h = setup(), c = h.context;
    c.state.opinionRequest = h.request('current');
    const first = c.runAiOpinion();
    h.calls[0].resolve({ ok: false, status: 503 }); await first;
    assert.equal(h.saves.length, 0);
    assert.equal(h.element('opinion-retry').classList.contains('hidden'), false);
    const retry = c.runAiOpinion();
    h.calls[1].resolve({ ok: true, text: 'recovered' }); await retry;
    assert.equal(h.saves.length, 0);
    assert.equal(h.element('opinion-retry').classList.contains('hidden'), true);
});

test('restarting while follow-up streams frees the new session and ignores old text', async () => {
 const h=setup(),c=h.context;
 c.state.sessionGeneration=0;c.state.opinionFullText='old context';
 h.element('user-followup-input').value='old question';
 const old=c.askGemmaMore();
 assert.equal(h.calls.length,1);
 c.resetScreeningState();
 assert.equal(h.calls[0].options.signal.aborted,true);
 c.state.opinionFullText='new context';
 h.element('user-followup-input').value='new question';
 const next=c.askGemmaMore();
 assert.equal(h.calls.length,2,'old request kept the new question blocked');
 h.calls[1].resolve({ok:true,text:'new answer'});await next;
 h.calls[0].resolve({ok:true,text:'old answer'});await old;
 assert.match(h.element('followup-response').innerText,/new answer/);
 assert.doesNotMatch(h.element('followup-response').innerText,/old answer/);
});

test('PDF completion after timeout does not download a late file', async () => {
 const h=setup(),c=h.context,timers=[],downloads=[];let release;
 c.hasCompletedScreening=()=>true;c.showToast=()=>{};c.setButtonBusy=()=>()=>{};
 c.window.scrollTo=()=>{};c.window.scrollX=0;c.window.scrollY=0;
 c.buildReportPdf=()=>({outputPdf:()=>new Promise(resolve=>{release=resolve})});
 c.setTimeout=(fn,ms)=>{if(ms===60000)timers.push(fn);return 1};c.clearTimeout=()=>{};
 c.URL={createObjectURL:()=>{downloads.push('url');return 'blob:x'},revokeObjectURL(){}};
 c.document.body={appendChild(){}};
 c.downloadPDF();assert.equal(timers.length,1);
 timers[0]();release({});await new Promise(r=>setImmediate(r));
 assert.equal(downloads.length,0,'timed-out PDF downloaded after the error');
});

test('PDF stays available to open; replacing it and restarting revoke old copies', async()=>{
 const h=setup(),c=h.context,revoked=[];let next=0;
 c.hasCompletedScreening=()=>true;c.showToast=()=>{};c.setButtonBusy=()=>()=>{};
 c.window.scrollTo=()=>{};c.window.scrollX=0;c.window.scrollY=0;
 c.buildReportPdf=()=>({outputPdf:async()=>({})});
 c.setTimeout=()=>1;c.clearTimeout=()=>{};
 c.URL={createObjectURL:()=>`blob:${++next}`,revokeObjectURL:url=>revoked.push(url)};
 c.document.body={appendChild(){}};c.document.createElement=()=>({click(){},remove(){}});
 c.downloadPDF();await new Promise(r=>setImmediate(r));
 assert.equal(h.element('pdf-preview').href,'blob:1');
 assert.equal(h.element('pdf-download-help').classList.contains('hidden'),false);
 c.downloadPDF();await new Promise(r=>setImmediate(r));
 assert.deepEqual(revoked,['blob:1']);
 assert.equal(h.element('pdf-preview').href,'blob:2');
 c.clearPdfDownload();assert.deepEqual(revoked,['blob:1','blob:2']);
 assert.equal(h.element('pdf-download-help').classList.contains('hidden'),true);
});

test('restarting during PDF generation suppresses a late file and restores controls',async()=>{
 const h=setup(),c=h.context;let release,restored=0,created=0;
 c.hasCompletedScreening=()=>true;c.showToast=()=>{};c.setButtonBusy=()=>()=>restored++;
 c.window.scrollTo=()=>{};c.window.scrollX=0;c.window.scrollY=0;
 c.buildReportPdf=()=>({outputPdf:()=>new Promise(resolve=>release=resolve)});
 c.setTimeout=()=>1;c.clearTimeout=()=>{};
 c.URL={createObjectURL:()=>{created++;return 'blob:late'},revokeObjectURL(){}};
 c.document.body={appendChild(){}};
 c.downloadPDF();c.clearPdfDownload();release({});await new Promise(r=>setImmediate(r));
 assert.equal(created,0);assert.equal(restored,1);
});


test('user cancellation frees opinion controls and ignores a late successful answer', async () => {
 const h=setup(),c=h.context;
 c.state.opinionRequest=h.request('cancel');
 c.translations.ko.ai_cancelled='cancelled';
 const pending=c.runAiOpinion();
 c.stopOpinionRequest();
 await pending;
 assert.equal(h.calls[0].options.signal.aborted,true);
 assert.equal(h.element('gemma-opinion-text').innerText,'cancelled');
 assert.equal(h.element('opinion-retry').classList.contains('hidden'),false);
 assert.equal(h.element('opinion-cancel').classList.contains('hidden'),true);
 h.calls[0].resolve({ok:true,text:'late answer'});
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(h.element('gemma-opinion-text').innerText,'cancelled');
 assert.equal(h.saves.length,0);
});

test('whole-request timeout frees a stalled header request without losing screening inputs', async () => {
 const h=setup(),c=h.context;let timeout;
 c.setTimeout=(fn,ms)=>{if(ms===180000)timeout=fn;return 1};c.clearTimeout=()=>{};
 c.translations.ko.ai_timeout='timed out';
 c.state.aiResultCode='risk';c.state.opinionRequest=h.request('timeout');
 const pending=c.runAiOpinion();timeout();await pending;
 assert.equal(h.calls[0].options.signal.aborted,true);
 assert.equal(h.element('gemma-opinion-text').innerText,'timed out');
 assert.equal(c.state.aiResultCode,'risk');
 assert.equal(h.element('opinion-retry').classList.contains('hidden'),false);
});


test('cancel and timeout messages follow a later language switch',()=>{
 const h=setup(),c=h.context;
 c.translations.en.ai_cancelled='cancelled';c.translations.en.ai_timeout='timed out';
 c.state.lang='en';c.state.opinionErrorKey='ai_cancelled';c.state.followupErrorKey='ai_timeout';
 c.refreshAiFailureMessages();
 assert.equal(h.element('gemma-opinion-text').innerText,'cancelled');
 assert.equal(h.element('followup-response').innerText,'timed out');
});

for (const failure of ['cancel', 'timeout', 'http', 'stream']) {
 test(`follow-up ${failure} preserves a new draft and restores an untouched failed question`, async()=>{
  for (const draft of ['', 'next question']) {
   const h=setup(),c=h.context;
   const input=h.element('user-followup-input');
   input.value='original question';
   let timeout;
   c.setTimeout=(fn,ms)=>{if(ms===180000)timeout=fn;return 1};c.clearTimeout=()=>{};
   c.translations.ko.srv_err='connection failed';
   c.translations.en.srv_err='translated failure';
   const pending=c.askGemmaMore();
   input.value=draft;
   if(failure==='cancel')c.stopFollowupRequest();
   if(failure==='timeout')timeout();
   if(failure==='http')h.calls[0].resolve({ok:false,status:503});
   if(failure==='stream')h.calls[0].resolve({ok:true,text:'AI generation failed',error:true});
   await pending;
   assert.equal(input.value,draft||'original question');
   assert.equal(h.element('followup-send-btn').disabled,false);
   assert.equal(h.element('followup-cancel').classList.contains('hidden'),true);
   if(failure==='stream') {
    c.state.lang='en';c.refreshAiFailureMessages();
    assert.equal(h.element('followup-response').innerText,'translated failure');
   }
  }
 });
}
