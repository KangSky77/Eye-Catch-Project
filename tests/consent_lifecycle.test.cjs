const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
function setup(){
 function el(){return {children:[],textContent:'',disabled:false,classList:{add(){},remove(){},toggle(){}},set innerHTML(v){this.children=[]},appendChild(n){this.children.push(n)},setAttribute(){}}}
 const box=el(), pending=[];
 const c=vm.createContext({state:{lang:'ko'},document:{getElementById:()=>box,createElement:el},fetch:(url,options)=>new Promise(resolve=>pending.push({resolve,options}))});
 for(const f of ['data.js','app-assess.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',f),'utf8'),c);
 return {c,box,pending,run:s=>vm.runInContext(s,c),agree:()=>box.children[0].children[2].children[0]};
}
test('language changes during and after save cannot create a second request',async()=>{
 const x=setup();x.run('requestSaveConsent({risk:1})');
 const stale=x.agree(), done=stale.onclick();
 for(const lang of ['en','es','fr','ja','zh','ko']){
  x.c.state.lang=lang;x.run('refreshSaveConsent()');
  assert.equal(x.agree().disabled,true);await x.agree().onclick();await stale.onclick();
 }
 assert.equal(x.pending.length,1);
 x.pending[0].resolve({ok:true,json:async()=>({status:'saved'})});await done;
 x.run("state.lang='en'; refreshSaveConsent()");
 assert.equal(x.agree().disabled,true);await x.agree().onclick();assert.equal(x.pending.length,1);
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
