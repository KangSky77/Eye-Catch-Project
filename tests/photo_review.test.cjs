const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const SRC=path.join(__dirname,'../static/app-photo-review.js');
function el(){const n={children:[],className:'',attrs:{},textContent:'',hidden:false,
 appendChild(c){this.children.push(c)},setAttribute(k,v){this.attrs[k]=v},removeAttribute(k){delete this.attrs[k];if(k==='src')this.src=undefined},
 classList:{list:new Set(),toggle(c,on){on?this.list.add(c):this.list.delete(c)},contains(c){return this.list.has(c)}},focus(){},
 showModal(){this.open=true},close(){this.open=false}};
 // innerHTML='' 은 실제 DOM에서 자식을 지운다 — 스텁도 같아야 '다시 그리기'를 검증할 수 있다
 Object.defineProperty(n,'innerHTML',{get(){return ''},set(v){if(!v)n.children.length=0}});
 return n}
function setup(extra={}){
 const ids=['photo-check','photo-check-image','photo-check-body','photo-check-list','photo-check-retake',
  'photo-check-symptoms','photo-check-summary','photo-check-summary-list'];
 const nodes=Object.fromEntries(ids.map(id=>[id,el()]));
 const revoked=[],calls=[];
 const c=vm.createContext(Object.assign({
  translations:Object.fromEntries(['ko','en','es','fr','ja','zh'].map(l=>[l,{}])),
  state:{lang:'ko'},
  document:{getElementById:id=>nodes[id],createElement:()=>el()},
  URL:{createObjectURL:()=>'blob:fixture',revokeObjectURL:u=>revoked.push(u)},
  retakePhoto:()=>calls.push('retake'), skipPhotoStep:()=>calls.push('skip'),
 },extra));
 vm.runInContext(fs.readFileSync(SRC,'utf8'),c);
 return {nodes,revoked,calls,run:s=>vm.runInContext(s,c),c};
}
const CHECKS=[{key:'resolution',ok:true},{key:'sharp',ok:false},{key:'eye_open',ok:null}];

test('every criterion is marked pass, fail or not-checked in all six languages',()=>{
 const x=setup();
 for(const lang of ['ko','en','es','fr','ja','zh']){
  x.c.state.lang=lang;
  x.run(`renderPhotoChecks(document.getElementById('photo-check-list'),${JSON.stringify(CHECKS)})`);
  const items=x.nodes['photo-check-list'].children;
  assert.equal(items.length,3,lang);
  assert.deepEqual(items.map(i=>i.children[0].textContent),['✓','✕','–'],lang);
  // 라벨은 키 그대로가 아니라 해당 언어 문구여야 한다
  for(const [i,key] of ['chk_resolution','chk_sharp','chk_eye_open'].entries()){
   const label=x.run(`translations['${lang}'].${key}`);
   assert.ok(label,`${lang}/${key}`);
   assert.equal(items[i].children[1].textContent,label,lang);
  }
  // 색과 기호만으로는 스크린리더가 통과 여부를 알 수 없다
  assert.ok(!items[0].attrs['aria-label']);
  assert.ok(items[1].attrs['aria-label'],lang);
  assert.ok(items[2].attrs['aria-label'],lang);
 }
});

test('a rejected photo shows the AI reason and sends the user to another photo',()=>{
 const x=setup();
 x.run(`showPhotoCheckFailure({},${JSON.stringify(CHECKS)},'사진이 흔들렸어요')`);
 assert.equal(x.nodes['photo-check'].open,true);
 assert.equal(x.nodes['photo-check-body'].textContent,'사진이 흔들렸어요');
 assert.equal(x.nodes['photo-check-list'].children.length,3);
 x.nodes['photo-check-retake'].onclick();
 assert.deepEqual(x.calls,['retake']);
 assert.equal(x.nodes['photo-check'].open,false);
 assert.equal(x.revoked.length,1,'미리보기 blob이 회수되지 않았다');
});

test('the skip-photo hatch closes the dialog exactly once',()=>{
 const x=setup();
 x.run('showPhotoCheckFailure({},[],"")');
 x.nodes['photo-check-symptoms'].onclick();
 x.nodes['photo-check-retake'].onclick();   // 닫힌 뒤 늦게 눌려도 두 번 처리되면 안 된다
 assert.deepEqual(x.calls,['skip']);
 assert.equal(x.revoked.length,1);
});

test('browsers without <dialog> fall back to the upload banner instead of throwing',()=>{
 const x=setup({document:{getElementById:()=>({}),createElement:()=>el()}});
 x.run(`showPhotoCheckFailure({},${JSON.stringify(CHECKS)},'x')`);   // 예외 없이 지나가야 한다
 assert.equal(x.revoked.length,0,'열지도 않은 미리보기를 만들었다');
});

test('the result screen summary appears only when the server reported checks',()=>{
 const x=setup();
 x.run('showPhotoCheckSummary([])');
 assert.ok(x.nodes['photo-check-summary'].classList.contains('hidden'));
 x.run(`showPhotoCheckSummary(${JSON.stringify(CHECKS)})`);
 assert.ok(!x.nodes['photo-check-summary'].classList.contains('hidden'));
 assert.equal(x.nodes['photo-check-summary-list'].children.length,3);
});
