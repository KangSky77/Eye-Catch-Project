const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
function setup(){
 function el(){return {children:[],textContent:'',disabled:false,classList:{add(){},remove(){},toggle(){}},set innerHTML(v){this.children=[]},appendChild(n){this.children.push(n)},setAttribute(){}}}
 const box=el(), pending=[], timers=new Map(); let timerId=0;
 const c=vm.createContext({state:{lang:'ko'},AbortController,
  setTimeout:fn=>{timers.set(++timerId,fn);return timerId},clearTimeout:id=>timers.delete(id),
  document:{getElementById:()=>box,createElement:el},fetch:(url,options)=>new Promise(resolve=>pending.push({resolve,options}))});
 for(const f of ['data.js','app-safety-copy.js','app-assess.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',f),'utf8'),c);
 return {c,box,pending,timers,run:s=>vm.runInContext(s,c),agree:()=>box.children[0].children[2].children[0]};
}
test('language changes during and after save cannot create a second request',async()=>{
 const x=setup();x.run('requestSaveConsent({risk:1})');
 const stale=x.agree(), done=stale.onclick();
 for(const lang of ['en','es','fr','ja','zh','ko']){
  x.c.state.lang=lang;x.run('refreshSaveConsent()');
  assert.equal(x.agree().disabled,true);await x.agree().onclick();await stale.onclick();
 }
 assert.equal(x.pending.length,1);
 assert.equal(JSON.parse(x.pending[0].options.body).consent_to_store,true);
 x.pending[0].resolve({ok:true,json:async()=>({status:'saved'})});await done;
 x.run("state.lang='en'; refreshSaveConsent()");
 assert.equal(x.agree().disabled,true);await x.agree().onclick();assert.equal(x.pending.length,1);
});

for (const bodyStalled of [false,true]) test(`save timeout unlocks controls (body stalled: ${bodyStalled})`,async()=>{
 const x=setup();x.run('requestSaveConsent({risk:1})');const done=x.agree().onclick();
 if(bodyStalled){x.pending[0].resolve({ok:true,json:()=>new Promise(()=>{})});await Promise.resolve();}
 assert.equal(x.timers.size,1,'saving needs a deadline even when the server never replies');
 for(const fn of [...x.timers.values()])fn();await done;
 assert.equal(x.pending[0].options.signal.aborted,true);
 assert.equal(x.agree().disabled,false);
 assert.equal(x.run('_saveConsent.phase'),'failed');
 assert.equal(x.timers.size,0);
 x.box.children[0].children[2].children[1].onclick();
 assert.equal(x.run('_saveConsent.phase'),'declined_unknown');
});

test('declining never posts and cannot be reversed by stale buttons or language changes',async()=>{
 const x=setup();x.run('requestSaveConsent({risk:1})');
 const stale=x.agree();
 x.box.children[0].children[2].children[1].onclick();
 for(const lang of ['ko','en','es','fr','ja','zh']){
  x.c.state.lang=lang;x.run('refreshSaveConsent()');
  assert.equal(x.box.children[0].children[3].textContent,x.run('translations[state.lang].save_declined'));
  await stale.onclick();await x.agree().onclick();
 }
 assert.equal(x.pending.length,0);
 x.run('cancelSaveConsent();requestSaveConsent({risk:2})');
 assert.equal(x.agree().disabled,false);
});

test('declining after an unconfirmed save does not falsely promise non-storage',async()=>{
 const x=setup();x.run('requestSaveConsent({risk:1})');const pending=x.agree().onclick();
 x.pending[0].resolve({ok:false,json:async()=>({})});await pending;
 x.box.children[0].children[2].children[1].onclick();
 assert.equal(x.box.children[0].children[3].textContent,x.run('translations.ko.save_declined_unknown'));
 assert.equal(x.pending.length,1);await x.agree().onclick();assert.equal(x.pending.length,1);
});
test('failed save retries immutable payload and stale completion cannot affect new consent',async()=>{
 const x=setup();x.run('var payload={risk:1};requestSaveConsent(payload);payload.risk=99');
 let done=x.agree().onclick();x.pending[0].resolve({ok:true,json:async()=>({status:'skipped'})});await done;
 assert.equal(x.agree().disabled,false);
 done=x.agree().onclick();assert.equal(JSON.parse(x.pending[1].options.body).risk,1);
 x.run('cancelSaveConsent();requestSaveConsent({risk:2})');
 x.pending[1].resolve({ok:true,json:async()=>({status:'saved'})});await done;
 assert.equal(x.agree().disabled,false);
 x.run('cancelSaveConsent();refreshSaveConsent()');assert.equal(x.box.children.length,0);
});

test('a retry after a timed-out save sends the same save key; a new consent gets a new key', async()=>{
 // 응답이 늦어 '실패'가 뜬 뒤 다시 눌러도 서버가 같은 키로 알아보고 한 번만 저장한다(2026-09-28).
 const x=setup();x.run('requestSaveConsent({risk:1})');
 const first=x.agree().onclick();
 for(const fn of [...x.timers.values()])fn();await first;
 assert.equal(x.run('_saveConsent.phase'),'failed');
 const retry=x.agree().onclick();
 x.pending[1].resolve({ok:true,json:async()=>({status:'saved'})});await retry;
 const keys=x.pending.map(p=>JSON.parse(p.options.body).save_key);
 assert.match(keys[0],/^[A-Za-z0-9-]{8,64}$/);
 assert.equal(keys[1],keys[0]);
 x.run('cancelSaveConsent();requestSaveConsent({risk:2})');
 const next=x.agree().onclick();
 x.pending[2].resolve({ok:true,json:async()=>({status:'saved'})});await next;
 assert.notEqual(JSON.parse(x.pending[2].options.body).save_key,keys[0]);
});
