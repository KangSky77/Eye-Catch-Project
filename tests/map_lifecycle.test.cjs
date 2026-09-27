const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function setup() {
    const pending = [], rendered = [], timers = new Map();
    let timerId = 0;
    const nodes = {'map-status': {innerText: ''}, 'clinic-list': {innerHTML: 'old results'}};
    const context = vm.createContext({state: {lang: 'ko'}, console, AbortController,
        document: {getElementById: id => nodes[id]},
        setTimeout: fn => {timers.set(++timerId, fn); return timerId;},
        clearTimeout: id => timers.delete(id),
        fetch: (url, options) => new Promise((resolve, reject) => pending.push({url, options, resolve, reject}))});
    for (const file of ['data.js', 'app-map.js'])
        vm.runInContext(fs.readFileSync(path.join(__dirname, '../static', file), 'utf8'), context);
    context.renderClinics = (items, lat, lng) => rendered.push({items, lat, lng});
    context.renderFallbackLinks = (lat, lng) => rendered.push({fallback: true, lat, lng});
    return {context, pending, rendered, timers, nodes};
}
const reply = name => ({ok: true, json: async () => ({clinics: [{name, lat: 37, lng: 127, dist: 10}]})});

test('insecure mobile origin explains connection limitation without requesting location', () => {
    const h = setup();
    h.context.window = {isSecureContext: false};
    h.context.ensureMap = () => ({});
    h.context.setButtonBusy = () => () => {};
    h.context.navigator = {geolocation: {getCurrentPosition() {assert.fail('must not request location');}}};
    for (const lang of ['ko', 'en', 'es', 'fr', 'ja', 'zh']) {
        h.context.state.lang = lang;
        h.context.findNearbyClinics();
        const expected = vm.runInContext(`translations.${lang}.map_status_insecure`, h.context);
        assert.ok(expected);
        assert.equal(h.nodes['map-status'].innerText, expected);
    }
});

test('a slower previous clinic search cannot replace the latest location results', async () => {
    const h = setup();
    const old = h.context.fetchClinics(35, 125), latest = h.context.fetchClinics(37, 127);
    h.pending[1].resolve(reply('latest')); await latest;
    h.pending[0].resolve(reply('old')); await old;
    assert.deepEqual(h.rendered.map(x => x.items[0].name), ['latest']);
    assert.equal(h.timers.size, 0);
});

test('a stale failed clinic search cannot erase newer successful results', async () => {
    const h = setup();
    const old = h.context.fetchClinics(35, 125), latest = h.context.fetchClinics(37, 127);
    h.pending[1].resolve(reply('latest')); await latest;
    h.pending[0].reject(new Error('old failed')); await old;
    assert.equal(h.rendered.length, 1);
    assert.equal(h.rendered[0].items[0].name, 'latest');
});

test('clinic completion uses the language selected while the request was pending', async () => {
    const h = setup(); const done = h.context.fetchClinics(37, 127);
    h.context.state.lang = 'ja'; h.pending[0].resolve(reply('clinic')); await done;
    assert.equal(h.nodes['map-status'].innerText,
        vm.runInContext("translations.ja.map_found.replace('{n}', 1)", h.context));
});

test('stalled clinic response body falls back and ignores a late completion', async () => {
    const h = setup(); const done = h.context.fetchClinics(37, 127);
    let body;
    h.pending[0].resolve({ok: true, json: () => new Promise(resolve => {body = resolve;})});
    await new Promise(resolve => setImmediate(resolve));
    for (const fn of [...h.timers.values()]) fn();
    await done;
    assert.equal(h.pending[0].options.signal.aborted, true);
    assert.equal(h.rendered[0].fallback, true);
    body({clinics: [{name: 'late'}]});
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(h.rendered.length, 1);
    assert.equal(h.timers.size, 0);
});
