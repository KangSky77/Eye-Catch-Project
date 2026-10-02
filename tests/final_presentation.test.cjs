const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const core = fs.readFileSync('static/app-core.js','utf8');
const deadlineSource = core.slice(core.indexOf('async function withAiDeadline'),core.indexOf('// ------------------------------------------',core.indexOf('async function withAiDeadline')));

test('AI deadline aborts stalled headers, body and heartbeat-only work', async () => {
    const c = vm.createContext({setTimeout,clearTimeout});
    vm.runInContext(deadlineSource,c);
    for (const kind of ['headers','body','heartbeat']) {
        const controller = new AbortController();
        await assert.rejects(c.withAiDeadline(()=>new Promise(()=>{}),controller,10),{name:'TimeoutError'});
        assert.equal(controller.signal.aborted,true,kind);
    }
});
test('cancel settles even if the underlying connection never responds', async () => {
    const c = vm.createContext({setTimeout,clearTimeout});
    vm.runInContext(deadlineSource,c);
    const controller = new AbortController();
    const work = c.withAiDeadline(()=>new Promise(()=>{}),controller,10000);
    controller.abort();
    await assert.rejects(work);
});
test('completed AI work cancels its timer without aborting the request', async () => {
    const controller = new AbortController();
    const c = vm.createContext({setTimeout,clearTimeout});
    vm.runInContext(deadlineSource,c);
    assert.equal(await c.withAiDeadline(async()=>42,controller,10),42);
    await new Promise(resolve=>setTimeout(resolve,20));
    assert.equal(controller.signal.aborted,false);
});
