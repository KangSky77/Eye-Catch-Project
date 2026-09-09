// 사진 업로드 왕복의 '생애주기' 테스트.
//
// 왜 필요한가: 2026-09-07에 업로드가 통째로 막힌 적이 있다. resetScreeningState()가
// 내부에서 cancelEyeAnalysis()를 불러 _analysisRequestId를 올리는데, runAIAnalysis()가
// 그보다 '먼저' 자기 요청 번호를 따 두는 바람에 방금 시작한 분석이 스스로 취소됐다.
// 서버는 200 OK로 응답하는데 화면은 로딩에서 3분간 멈췄다.
//
// 그때 pytest 267개와 npm 4개가 전부 통과했다. 파이썬 쪽은 서버 함수를 보고,
// 기존 JS 테스트는 소견서(Gemma)만 봤기 때문이다. 문자열 존재 검사로는 '호출 순서'를
// 잡을 수 없으므로, 여기서는 실제로 함수를 돌려 결과 화면까지 가는지 확인한다.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function slice(file, from, to) {
    const src = fs.readFileSync(path.join(__dirname, '..', 'static', file), 'utf8');
    const start = src.indexOf(from);
    assert.notEqual(start, -1, `${file}에서 "${from}"을 찾지 못했습니다`);
    const end = to ? src.indexOf(to, start) : src.length;
    assert.notEqual(end, -1, `${file}에서 "${to}"를 찾지 못했습니다`);
    return src.slice(start, end);
}

function setup() {
    const steps = [];        // nextStep()이 불린 순서
    const toasts = [];
    const banners = [];
    const pending = [];      // 업로드마다 {resolve, reject} — 개별로 완료시킬 수 있어야 한다

    const el = () => {
        const classes = new Set();
        const node = {
            innerHTML: '', innerText: '', textContent: '', src: '', value: '', files: null,
            style: {}, dataset: {},
            appendChild() {}, removeChild() {}, remove() {},
            querySelector() { return null; }, querySelectorAll() { return []; },
            addEventListener() {}, setAttribute() {}, removeAttribute() {},
            classList: {
                add: c => classes.add(c), remove: c => classes.delete(c),
                contains: c => classes.has(c),
                toggle: (c, force) => (force ? classes.add(c) : classes.delete(c)),
            },
        };
        return node;
    };
    const elements = new Map();
    const byId = id => {
        if (!elements.has(id)) elements.set(id, el());
        return elements.get(id);
    };

    const context = {
        console, AbortController, Promise, setTimeout, clearTimeout, Date, Math, JSON, Event,
        state: { lang: 'ko', sessionGeneration: 0, navEpoch: 0, amslerResult: {}, chatHistory: [] },
        translations: { ko: {} },
        document: { getElementById: byId, createElement: () => el(), querySelectorAll: () => [] },
        window: { addEventListener() {}, devicePixelRatio: 1 },
        history: { pushState() {}, replaceState() {}, state: null },
        FormData: class { append() {} },
        FileReader: class { readAsDataURL() { /* onload은 호출하지 않는다 — 비동기 미리보기 */ } },
        // 축소는 이 테스트의 관심사가 아니다. createImageBitmap이 없으면 shrinkForUpload가
        // 원본을 그대로 돌려주므로(설계된 폴백) 그 경로를 쓴다.
        showToast: (m) => toasts.push(m),
        showUploadError: (m) => banners.push(m),
        clearUploadError: () => {},
        nextStep: (sid) => steps.push(sid),
        showTab: () => {},
        cancelAiOpinion: () => {},
        renderEyeBreakdown: () => {},
        showAnalyzedPhoto: () => {},
        startLoadingProgress: () => ({ setProgress() {}, toAnalyzing() {}, stop() {} }),
        uploadWithProgress: () => new Promise((resolve, reject) => pending.push({ resolve, reject })),
    };
    vm.createContext(context);

    // app-vision.js에서 업로드 경로에 필요한 부분만 (uploadWithProgress는 위에서 스텁으로 대체)
    vm.runInContext(slice('app-vision.js', 'const MAX_UPLOAD_MB', 'function startLoadingProgress()'), context);
    vm.runInContext(slice('app-vision.js', 'const UPLOAD_ERROR_KEYS', 'function renderEyeBreakdown('), context);
    // 실제 resetScreeningState를 쓴다 — 이 테스트의 핵심이 그것과의 상호작용이기 때문
    vm.runInContext(slice('app-core.js', 'function resetScreeningState()', '\nfunction openMap()'), context);

    const file = { type: 'image/jpeg', name: 'eye.jpg', size: 1024, lastModified: 0 };
    const ok = (extra = {}) => ({ ok: true, data: Object.assign(
        { result_code: 'normal', probability: 0, mode: 'eye', eyes: [], eyes_detected: 0 }, extra) });
    return { context, steps, toasts, banners, file, ok, pending,
        resolve: (v, n) => pending[n === undefined ? pending.length - 1 : n].resolve(v),
        uploadCount: () => pending.length };
}

test('업로드가 결과 화면까지 간다 — resetScreeningState가 자기 요청을 취소하면 안 된다', async () => {
    const h = setup(), c = h.context;
    const done = c.runAIAnalysis(h.file);
    await new Promise(r => setImmediate(r));
    assert.equal(h.uploadCount(), 1, '업로드가 시작되지 않았다');
    h.resolve(h.ok());
    await done;
    assert.equal(c.state.aiResultCode, 'normal', '결과 코드가 저장되지 않았다');
    assert.ok(h.steps.includes('step-ai-loading'), '로딩 단계로 가지 않았다');
    // 실패하면 로딩 화면에 머문다 — 사용자에게는 3분짜리 무한 스피너로 보인다
    assert.ok(!h.steps.includes('step-photo'),
        `업로드가 조용히 취소되고 업로드 화면으로 되돌아갔다: ${h.steps.join(' -> ')}`);
});

test('재촬영 코드는 결과가 아니라 안내로 처리된다', async () => {
    const h = setup(), c = h.context;
    const done = c.runAIAnalysis(h.file);
    await new Promise(r => setImmediate(r));
    h.resolve(h.ok({ result_code: 'multiple_faces' }));
    await done;
    assert.equal(c.state.aiResultCode, '', '재촬영 코드가 판정으로 저장됐다');
    assert.equal(h.steps[h.steps.length - 1], 'step-photo');
    assert.equal(h.banners.length, 1, '업로드 카드에 안내 배너가 없다');
});

test('새 업로드가 시작되면 이전 업로드의 늦은 응답은 버려진다', async () => {
    const h = setup(), c = h.context;
    const first = c.runAIAnalysis(h.file);
    await new Promise(r => setImmediate(r));

    const second = c.runAIAnalysis(h.file);   // 두 번째 업로드가 첫 번째를 무효화
    await new Promise(r => setImmediate(r));
    assert.equal(h.uploadCount(), 2);
    h.resolve(h.ok({ result_code: 'risk', probability: 90 }), 1);
    await second;
    assert.equal(c.state.aiResultCode, 'risk');

    h.resolve(h.ok({ result_code: 'normal' }), 0);   // 첫 번째가 뒤늦게 도착
    await first;
    assert.equal(c.state.aiResultCode, 'risk', '오래된 응답이 새 결과를 덮었다');
});

test('서버 오류는 언어 중립 코드로 번역된다', async () => {
    const h = setup(), c = h.context;
    c.translations.ko.err_img_resolution = '해상도가 너무 높아요';
    const done = c.runAIAnalysis(h.file);
    await new Promise(r => setImmediate(r));
    h.resolve({ ok: false, data: { detail: { code: 'IMAGE_RESOLUTION', message: '한국어 기본값' } } });
    await done;
    assert.equal(h.banners[0], '해상도가 너무 높아요');
    assert.equal(h.steps[h.steps.length - 1], 'step-photo');
});

test('사진 준비 중 초기화하면 완료된 축소 작업도 업로드하지 않는다', async () => {
    const h = setup(), c = h.context;
    let release;
    c.shrinkForUpload = file => new Promise(resolve => { release = () => resolve(file); });
    const done = c.runAIAnalysis(h.file);
    c.resetScreeningState();
    release();
    await new Promise(r => setImmediate(r));
    const count = h.uploadCount();
    if (count) h.resolve(h.ok());
    await done;
    assert.equal(count, 0);
    assert.equal(c.state.aiResultCode, '');
});

test('두 사진의 준비 순서가 역전돼도 마지막 선택만 분석한다', async () => {
    const h = setup(), c = h.context, releases = [];
    c.shrinkForUpload = file => new Promise(resolve => releases.push(() => resolve(file)));
    const old = c.runAIAnalysis(h.file);
    const current = c.runAIAnalysis(h.file);
    releases[1]();
    await new Promise(r => setImmediate(r));
    h.resolve(h.ok({ result_code: 'risk', probability: 90 }));
    await current;
    releases[0]();
    await new Promise(r => setImmediate(r));
    const count = h.uploadCount();
    if (count > 1) h.resolve(h.ok());
    await old;
    assert.equal(count, 1);
    assert.equal(c.state.aiResultCode, 'risk');
});

function chatSetup() {
    const h = setup(), c = h.context;
    const timers = [];
    c.setTimeout = fn => timers.push(fn);
    c.riskQuestions = [{ code: 'age', key: 'age', type: 'choice', options: [] }];
    c.symptomQuestions = [{ code: 'blur', key: 'blur' }];
    vm.runInContext(fs.readFileSync(path.join(__dirname, '../static/app-chat.js'), 'utf8'), c);
    c.addMsg = () => {};
    c.askRiskQuestion = () => { c.state.chatBusy = false; };
    return { ...h, timers };
}

test('문진 재시작은 이전 완료 판정과 소견서를 무효화하고 사진은 유지한다', () => {
    const h = chatSetup(), c = h.context;
    vm.runInContext(slice('app-findings.js', 'function hasCompletedScreening()', '/** 리포트 탭'), c);
    c.state.aiResultCode = 'risk';
    c.state.triage = { level: 'now' };
    c.state.opinionRequest = { cataract_code: 'risk' };
    const opinion = c.document.getElementById('gemma-opinion-text');
    opinion.textContent = 'Previous report';
    c.document.getElementById('followup-response').innerText = 'Previous answer';
    assert.equal(c.hasCompletedScreening(), true);
    c.startChat();
    assert.equal(c.hasCompletedScreening(), false);
    assert.equal(c.state.opinionRequest, null);
    assert.equal(opinion.textContent, '');
    assert.equal(c.document.getElementById('followup-response').innerText, '');
    assert.equal(c.state.aiResultCode, 'risk');
});

for (const stage of ['risk', 'symptom']) {
    test(`${stage} 문항 타이머는 새 문진에서 실행되지 않는다`, () => {
        const h = chatSetup(), c = h.context;
        c.startChat();
        if (stage === 'risk') c.handleAnswer('adult', 'Adult');
        else c.handleSymptomAnswer(false);
        assert.equal(h.timers.length, 1);
        c.startChat();
        let staleCalls = 0;
        c.addMsg = () => staleCalls++;
        c.askRiskQuestion = c.askSymptomQuestion = () => staleCalls++;
        h.timers.forEach(fn => fn());
        assert.equal(staleCalls, 0);
    });
}

test('시력검사 기능은 제품 화면에서 로드되지 않는다', () => {
    const html = fs.readFileSync(path.join(__dirname, '../static/index.html'), 'utf8');
    const core = fs.readFileSync(path.join(__dirname, '../static/app-core.js'), 'utf8');
    assert.equal(html.includes('app-visiontest.js'), false);
    assert.equal(html.includes('id="tab-vision"'), false);
    assert.equal(core.includes('state.visionTest'), false);
});
