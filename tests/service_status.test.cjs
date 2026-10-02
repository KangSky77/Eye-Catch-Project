const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function setup() {
    const timers = new Map(), requests = [], nodes = new Map();
    let id = 0;
    const c = vm.createContext({state:{lang:'ko'}, AbortController,
        window:{addEventListener(){}},
        document:{getElementById(name){if (!nodes.has(name)) nodes.set(name,{dataset:{},setAttribute(){}}); return nodes.get(name);}},
        setTimeout(fn){timers.set(++id,fn); return id;}, clearTimeout(i){timers.delete(i);},
        fetch(url,options){return new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}));}});
    for (const file of ['data.js','app-status.js']) vm.runInContext(fs.readFileSync('static/'+file,'utf8'),c);
    return {c,timers,requests,nodes};
}
test('degraded service still exposes working photos and translates AI retry advice', async()=>{
    const h=setup(), work=h.c.checkServiceStatus();
    h.requests[0].resolve({status:503,json:async()=>({services:{photo:'ready',ollama:'unavailable'}})});
    await work;
    assert.equal(h.nodes.get('service-photo').dataset.status,'ready');
    assert.equal(h.nodes.get('service-ollama').dataset.status,'unavailable');
    for (const lang of ['ko','en','es','fr','ja','zh']) {
        h.c.state.lang=lang;h.c.refreshServiceStatus();
        assert.equal(h.nodes.get('service-note').textContent,vm.runInContext(`translations.${lang}.status_ai_unavailable`,h.c));
    }
    assert.equal(h.timers.size,0);
});
test('status body timeout unlocks retry and late success cannot claim readiness',async()=>{
    const h=setup(), work=h.c.checkServiceStatus();let late;
    h.requests[0].resolve({status:200,json:()=>new Promise(resolve=>late=resolve)});
    await new Promise(resolve=>setImmediate(resolve));
    for (const fn of h.timers.values()) fn();
    await work;
    assert.equal(h.requests[0].options.signal.aborted,true);
    assert.equal(h.nodes.get('service-recheck').disabled,false);
    late({services:{photo:'ready',ollama:'ready'}});
    await new Promise(resolve=>setImmediate(resolve));
    assert.equal(h.nodes.get('service-photo').dataset.status,'unavailable');
    const retry=h.c.checkServiceStatus();
    h.requests[1].resolve({status:200,json:async()=>({services:{photo:'ready',ollama:'ready'}})});
    await retry;
    assert.equal(h.nodes.get('service-photo').dataset.status,'ready');
});
test('malformed or failed service response cannot show ready',async()=>{
    for (const response of [{status:200,json:async()=>({services:{photo:'ready'}})},{status:500}]) {
        const h=setup(),work=h.c.checkServiceStatus();h.requests[0].resolve(response);await work;
        assert.equal(h.nodes.get('service-photo').dataset.status,'unavailable');
    }
});
