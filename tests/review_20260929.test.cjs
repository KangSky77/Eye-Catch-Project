// 전체 리뷰에서 재현한 문제의 실제 상태 전이와 다국어 결과 계약.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const langs = ['ko','en','es','fr','ja','zh'];

test('분리한 리포트 스크립트는 제품에서 의존 순서대로 로드된다', () => {
 const {REPORT_SCRIPTS} = require('./helpers/report-scripts.cjs');
 const html = fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
 const scripts = Array.from(html.matchAll(/<script src="\/static\/([^?]+)\?/g), m=>m[1]);
 assert.deepEqual(scripts.filter(file=>REPORT_SCRIPTS.includes(file)), REPORT_SCRIPTS);
 for (const file of ['app-visiontest.js','calibration.js','calibration-demo.html'])
  assert.equal(fs.existsSync(path.join(__dirname,'../static',file)),false);
});

test('PDF의 권장 조치는 6개 언어의 일반·수술 후·응급 화면과 일치한다', () => {
 for (const lang of langs) for (const profile of ['general','post_contact','post_confirm','urgent']) {
  const x=setup(); let html='';
  x.run(`state.lang=${JSON.stringify(lang)}; state.riskAnswers={surgery:'none'}; state.chatSymptoms=[]; state.redFlags=[]; state.symptomAnswers={};`);
  if (profile.startsWith('post_')) {
   x.run("state.riskAnswers={surgery:'today',surgery_type:'cataract',surgery_eye:'right'};");
   if (profile==='post_contact') x.run("state.symptomAnswers={post_worse:true,post_followup:true};");
   else x.run("state.symptomAnswers={post_followup:false};");
  }
  if (profile==='urgent') x.run("state.redFlags=['rf_acute'];");
  for (const id of ['report-date','pdf-ai-result','pdf-amsler-result','pdf-chat-result']) x.nodes.set(id,{innerText:'test'});
  x.c.document.createElement=()=>({style:{},appendChild(){},remove(){},innerHTML:''});
  x.c.document.body.appendChild=()=>{};
  const worker={set(){return worker;},from(el){html=el.innerHTML;return worker;}};
  x.c.html2pdf=()=>worker;
  const triage=x.run('computeCurrentTriage()');
  if (profile.startsWith('post_')) assert.equal(triage.kind,profile.slice(5));
  if (profile==='urgent') assert.equal(triage.level,'urgent');
  x.run('buildReportPdf(); cleanupPdfHost();');
  assert.ok(html.includes(x.c.escapeHTML(triage.label)),`${lang}/${profile}: label`);
  assert.ok(html.includes(x.c.escapeHTML(triage.why)),`${lang}/${profile}: reason`);
 }
});

function setup() {
 const nodes = new Map(), frames = [], tracked = [];
 const node = () => ({hidden:false,children:[],style:{},dataset:{},innerHTML:'',textContent:'',
  classList:{add(){},remove(){},toggle(){},contains(){return false;}},
  setAttribute(){},removeAttribute(){},getAttribute(){return '';},focus(){},scrollIntoView(){},
  querySelector(){return null;},appendChild(){}});
 const c = vm.createContext({console,AbortController,setTimeout:()=>0,clearTimeout(){},
  requestAnimationFrame:f=>frames.push(f),getComputedStyle:()=>({paddingLeft:'0',paddingRight:'0'}),
  history:{pushState(){},replaceState(){}},localStorage:{getItem:()=>null,setItem(){}},
  window:{addEventListener(){},scrollTo(){},innerWidth:390},navigator:{language:'ko'},
  document:{getElementById:id=>nodes.get(id)||null,querySelectorAll:()=>[],querySelector:()=>null,
   addEventListener(){},createElement:node,body:{dataset:{}},documentElement:{setAttribute(){}}}});
 for (const id of ['lang-selector','chat-box','amsler-eye-instruction','amsler-answers','amsler-ready-btn','amsler-dist-note'])
  nodes.set(id,node());
 const box = node();
 box.visible = false; box.parentElement = {clientWidth:326};
 Object.defineProperty(box,'offsetParent',{get:()=>box.visible?box.parentElement:null});
 box.getBoundingClientRect=()=>({width:box.visible?326:0});
 nodes.set('amsler-box',box);
 for (const file of ['data.js','app-report-text.js','app-safety-copy.js','app-core.js','app-surgery.js',
                     'app-vision.js','app-chat.js','app-assess.js','app-findings.js','app-report.js','app-report-chat.js','app-report-pdf.js'])
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',file),'utf8'),c);
 c.renderDiseases=()=>{}; c.renderStepProgress=()=>{};
 c.refreshChatLanguage=()=>{};
 c.nextStep=step=>{vm.runInContext(`state.step=${JSON.stringify(step)}`,c);box.visible=step==='step-amsler';};
 c.startChat=()=>tracked.push('chat');
 c.showToast=()=>{}; c.addMsg=()=>{}; c.advanceAfterDynamicAnswer=()=>{};
 const run=s=>vm.runInContext(s,c);
 return {c,run,nodes,box,frames,tracked,t:lang=>run(`translations.${lang}`)};
}

test('왼쪽 답변 연속 입력은 오른쪽 준비 확인과 실제 답변을 건너뛰지 않는다',()=>{
 for (const left of [false,true,'unable']) for (const right of [false,true,'unable']) {
  const x=setup();
  x.run('startAmslerStep()');
  x.c.answer=left;
  x.run('recordAmsler(answer); recordAmsler(answer); recordAmsler(answer)');
  assert.equal(x.run('state.amslerResult.left'),left);
  assert.equal(x.run('state.amslerResult.right'),undefined);
  assert.equal(x.run('state.amslerStage'),'prepare');
  assert.equal(x.nodes.get('amsler-answers').hidden,true);
  assert.equal(x.nodes.get('amsler-ready-btn').hidden,false);
  assert.equal(x.tracked.length,0);
  x.run('prepareRightAmsler(); prepareRightAmsler()');
  assert.equal(x.nodes.get('amsler-answers').hidden,false);
  x.c.answer=right;
  x.run('recordAmsler(answer); recordAmsler(answer)');
  assert.equal(x.run('state.amslerResult.right'),right);
  assert.equal(x.run('state.hasAmsler'),left===true||right===true);
  assert.deepEqual(x.tracked,['chat']);
  x.run('startAmslerStep()');
  assert.equal(x.run('state.amslerStage'),'answer');
  assert.equal(x.run('Object.keys(state.amslerResult).length'),0);
  assert.equal(x.nodes.get('amsler-ready-btn').hidden,true);
 }
});

test('오른쪽 준비 단계의 언어 변경과 새 회차 초기화가 응답 잠금을 풀지 않는다',()=>{
 const x=setup();x.run('startAmslerStep(); recordAmsler(false)');
 for (const lang of langs) {
  x.run(`updateUI('${lang}'); recordAmsler(false)`);
  assert.equal(x.run('state.amslerResult.right'),undefined,lang);
  assert.ok(x.t(lang).ams_right_ready,lang);
 }
 x.run('resetScreeningState(); prepareRightAmsler(); recordAmsler(false)');
 assert.equal(x.run('Object.keys(state.amslerResult).length'),0);
 assert.equal(x.tracked.length,0);
});

test('완료 후 뒤로가기 재진입은 새 히스토리 없이 왼쪽 검사부터 다시 열린다',()=>{
 const x=setup();x.run('startAmslerStep(); recordAmsler(false); prepareRightAmsler(); recordAmsler(true)');
 x.nodes.set('step-amsler',{classList:{add(){}}});
 let pushes=0;x.c.history.pushState=()=>pushes++;
 const core=fs.readFileSync(path.join(__dirname,'../static/app-core.js'),'utf8');
 vm.runInContext(core.slice(core.indexOf('function nextStep('),core.indexOf('function renderStepProgress()')),x.c);
 x.run("nextStep('step-amsler',true)");
 assert.equal(x.run('state.amslerStage'),'answer');
 assert.equal(x.run('state.amslerEye'),'left');
 assert.equal(x.run('Object.keys(state.amslerResult).length'),0);
 assert.equal(x.nodes.get('amsler-answers').hidden,false);
 assert.equal(pushes,0);
});

test('숨겨진 격자는 언어 전환마다 RAF를 예약하지 않고 표시 후 20칸으로 그린다',()=>{
 const x=setup();
 for (const lang of langs) x.run(`updateUI('${lang}'); renderAmslerGrid()`);
 assert.equal(x.frames.length,0);
 assert.equal(x.box.style.width,undefined);
 x.run('startAmslerStep()');
 assert.equal(x.box.style.width,'326px');
 assert.equal(x.box.style.backgroundSize,'16.3px 16.3px');
 assert.ok(x.nodes.get('amsler-dist-note').textContent);
});

test('다른 탭에서 폭이 바뀌면 검사 탭 복귀 시 격자를 현재 폭으로 다시 그린다',()=>{
 const x=setup();x.run('startAmslerStep()');
 x.box.visible=false;x.box.parentElement.clientWidth=250;
 x.run('renderAmslerGrid()');
 assert.equal(x.box.style.width,'326px');
 x.nodes.set('tab-test',{classList:{add(){x.box.visible=true;}},focus(){}});
 x.run("showTab('tab-test')");
 assert.equal(x.box.style.width,'250px');
 assert.equal(x.box.style.backgroundSize,'12.5px 12.5px');
 assert.equal(x.frames.length,0);
});

test('언어가 바뀐 뒤 도착한 설명 조각은 새 언어의 답변을 덮지 않는다',async()=>{
 const x=setup(),pending=[];
 for(const id of ['user-followup-input','followup-response','followup-send-btn','followup-explain-btn'])
  x.nodes.set(id,{value:'',innerText:'',classList:{add(){},remove(){}},setAttribute(){},removeAttribute(){},appendChild(){}});
 x.c.fetch=(url,options)=>new Promise(resolve=>pending.push({options,resolve}));
 x.c.createAiLoader=()=>({el:{},stop(){}});
 x.c.readAiStream=async(response,update)=>{update(response.text);if(response.wait)await response.wait;
  update(response.text);return {text:response.text,hasError:false};};
 let release;
 x.nodes.get('user-followup-input').value='Old question';
 const old=x.run('askGemmaMore(true)');
 pending[0].resolve({ok:true,text:'Old explanation',wait:new Promise(r=>release=r)});
 await new Promise(r=>setImmediate(r));
 x.run("updateUI('en')");
 assert.equal(pending[0].options.signal.aborted,true);
 assert.equal(x.nodes.get('followup-response').innerText,'');
 x.nodes.get('user-followup-input').value='English question';
 const next=x.run('askGemmaMore(true)');
 pending[1].resolve({ok:true,text:'English explanation'});await next;
 release();await old;
 assert.match(x.nodes.get('followup-response').innerText,/English explanation/);
 assert.doesNotMatch(x.nodes.get('followup-response').innerText,/Old explanation/);
});

test('중립적인 맞춤 질문의 예·아니오·모름은 증상이 되지 않고 답변과 조언 코드가 보존된다',()=>{
 for (const lang of langs) for (const value of [true,false,'unknown']) {
  const x=setup();x.c.answer=value;
  x.run(`Object.assign(state,{lang:'${lang}',stepIdx:99,chatBusy:false,riskAnswers:{surgery:'none'},
   symptomScore:0,symptomCodes:[],redFlags:[],chatHistory:[{q:'Neutral question?',question_id:'eye_drops'}]});
   handleChatAnswer(answer)`);
  assert.equal(x.run('state.chatSymptoms.length'),0,lang);
  assert.equal(x.run('state.symptomCodes.length'),0,lang);
  assert.equal(x.run('state.symptomScore'),0,lang);
  assert.equal(x.run('computeCurrentTriage().level'),'monitor',lang);
  assert.equal(x.run('state.dynamicAnswers[0].value'),value,lang);
  assert.equal(x.run('state.dynamicAnswers[0].question_id'),'eye_drops',lang);
  const lines=Array.from(x.run('buildFindings()'));
  assert.ok(lines.includes(x.t(lang).find_nosym),lang);
  assert.ok(lines.some(s=>s.includes('Neutral question?')),lang);
  assert.equal(x.run("opinionFlagCodes().includes('ans_eye_drops')"),value===true,lang);
  // 이전 코드가 넣은 항목도 증상으로 표시하지 않는다. 실제 증상은 유지한다.
  x.run("state.chatSymptoms=['symptom_extra','sym_cat_foggy']");
  assert.equal(x.run('formatSymptoms().length'),1,lang);
  assert.ok(x.run('buildFindings()').includes(x.t(lang).find_sym.replace('{items}',x.t(lang).sym_cat_foggy)),lang);
 }
});

test('수술·일반 경로 전환과 모든 언어에서 업로드 안내가 경로에 맞게 표시된다',()=>{
 const x=setup();
 const general={hidden:false},surgery={hidden:true};
 x.c.document.querySelectorAll=s=>s==='[data-surgery-only]'?[surgery]:s==='[data-general-only]'?[general]:[];
 for (const lang of langs) {
  x.run(`state.lang='${lang}'; answerSurgeryGate(true)`);
  assert.equal(general.hidden,true,lang);assert.equal(surgery.hidden,false,lang);
  assert.equal((x.t(lang).post_upload_guide.match(/<li>/g)||[]).length,3,lang);
  assert.notEqual(x.t(lang).post_upload_guide,x.t(lang).guide_list,lang);
  x.run('answerSurgeryGate(false)');
  assert.equal(general.hidden,false,lang);assert.equal(surgery.hidden,true,lang);
 }
});

test('언어 전환은 저장된 권장 조치·챗봇 문맥·설명 문장을 함께 바꾸고 위험 점수를 유지한다',()=>{
 for (const input of [
  {aiResultCode:'risk',riskAnswers:{surgery:'none',age:'60s',diabetes:true}},
  {aiResultCode:'borderline',riskAnswers:{surgery:'none'}},
  {aiResultCode:'normal',riskAnswers:{surgery:'none'}},
  {aiResultCode:'postop',riskAnswers:{surgery:'recent'},symptomAnswers:{post_followup:false}},
  {aiResultCode:'postop',riskAnswers:{surgery:'recent'},redFlags:['post_pain']},
 ]) {
  const x=setup();x.c.input=input;
  x.run('Object.assign(state,input); state.triage=computeCurrentTriage()');
  const level=x.run('state.triage.level'),kind=x.run('state.triage.kind'),score=x.run('state.triage.riskScore');
  for (const lang of langs) {
   x.run(`updateUI('${lang}')`);
   const tri=x.run('state.triage');
   assert.equal(tri.label, x.t(lang)[kind?'post_'+kind:'tri_'+level],lang);
   assert.equal(tri.level,level,lang);assert.equal(tri.kind,kind,lang);assert.equal(tri.riskScore,score,lang);
   assert.ok(x.run('buildChatContext()').includes(tri.label),lang);
   assert.ok(x.run('explainCheckPayload().explain_fallback').includes(tri.label),lang);
  }
 }
});

test('결과 설명은 정상·미측정·수술·판독 제외를 포함한 모든 고정 소견과 권장 조치를 보존한다',()=>{
 for (const lang of langs) for (const input of [
  {aiResultCode:'risk',hasAmsler:true,amslerResult:{left:true,right:false},riskAnswers:{surgery:'none'}},
  {aiResultCode:'normal',amslerResult:{left:false,right:false},riskAnswers:{surgery:'none'}},
  {aiResultCode:'uncertain',amslerResult:{left:'unable',right:false},riskAnswers:{surgery:'none'}},
  {aiResultCode:'risk',riskAnswers:{surgery:'past',surgery_type:'cataract'}},
  {aiResultCode:'postop',amslerResult:{left:false,right:false},riskAnswers:{surgery:'recent'},symptomAnswers:{post_followup:true}},
 ]) {
  const x=setup();x.c.input=input;
  x.run(`Object.assign(state,input,{lang:'${lang}',dynamicAnswers:[{q:'Custom question',a:'Yes'}]});
   state.triage=computeCurrentTriage()`);
  const lines=Array.from(x.run('buildFindings({includePersonal:false})'));
  const p=x.run('explainCheckPayload()');
  assert.deepEqual(Array.from(p.explain_fallback),[...lines,x.run('state.triage.label')],lang);
  assert.ok(p.explain_fallback.length<=20 && p.explain_fallback.every(s=>s.length<=2000),lang);
  assert.ok(!p.explain_fallback.some(s=>s.includes('Custom question')),lang);
  if(x.run('photoAssessmentExcluded()')) assert.ok(!p.explain_fallback.includes(x.t(lang).find_cat_risk),lang);
 }
});
