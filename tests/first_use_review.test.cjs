// 2026-09-27 발표 전 첫 사용 점검(PC + 갤럭시 S25 Ultra 실기기)에서 고친 것들의 회귀 테스트.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');

function setup(state) {
 const c=vm.createContext({state:{lang:'ko',riskAnswers:{},symptomAnswers:{},...state},window:{addEventListener(){}},console});
 for(const file of ['data.js','app-report-text.js','app-safety-copy.js','app-surgery.js','app-chat.js','app-assess.js'])
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',file),'utf8'),c);
 return c;
}

test('당뇨 비문증 질문은 응급 번쩍임·비문증 질문과 중복되지 않는다', () => {
 const c=setup({riskAnswers:{surgery:'none',diabetes:true}});
 const codes=vm.runInContext('activeSymptomQuestions().map(q=>q.code)',c);
 assert.ok(codes.includes('rf_flashes'), '모든 사람에게 묻는 응급 질문은 남아야 한다');
 assert.ok(codes.includes('dr_fundus'), '당뇨 분기 질문 자체는 남아야 한다');
 assert.ok(!codes.includes('dr_floaters'), '같은 비문증 급증을 두 번 묻는다');
});

test('수술 시기를 답하기 전에는 문진 배너가 일반 문진이라고 말하지 않는다', () => {
 for (const lang of ['ko','en','es','fr','ja','zh']) {
  const c=setup({lang,hadSurgery:true});
  const el={className:'',textContent:''};
  c.document={getElementById:()=>el};
  vm.runInContext('updateSurveyModeBanner()',c);
  const t=vm.runInContext(`translations.${lang}`,c);
  assert.ok(t.survey_mode_surgery_check, lang);
  assert.equal(el.textContent,t.survey_mode_surgery_check,lang);
  // 시기를 답하면 해당 경로의 배너로 바뀐다
  c.state.riskAnswers.surgery='recent';
  vm.runInContext('updateSurveyModeBanner()',c);
  assert.equal(el.textContent,t.survey_mode_postop,lang);
  c.state.riskAnswers.surgery='past';
  vm.runInContext('updateSurveyModeBanner()',c);
  assert.equal(el.textContent,t.survey_mode_general,lang);
 }
});

test('수술 후 권장 조치 카드는 검사 요약 첫 줄(post_limit)을 되풀이하지 않는다', () => {
 const c=setup({riskAnswers:{surgery:'recent'},symptomAnswers:{post_followup:false}});
 const tri=vm.runInContext('computeTriage({})',c);
 assert.notEqual(tri.note, vm.runInContext('translations.ko.post_limit',c));
});

test('수술 후 문진 요약은 수술 당일 같은 사실을 "증상"이라 부르지 않는다', () => {
 const c=setup({});
 for (const lang of ['ko','en','es','fr','ja','zh']) {
  const s=vm.runInContext(`translations.${lang}.find_post_sym`,c);
  assert.ok(s.includes('{items}'), lang);
  assert.ok(!/증상:|Symptoms reported|Síntomas comunicados|Symptômes signalés|報告された症状|报告的症状/.test(s), lang);
 }
});

test('수 주 내 검진 이유는 미뤄진 검진도 이유로 든다(증상이 없어도 이 단계가 된다)', () => {
 const c=setup({});
 assert.match(vm.runInContext('translations.ko.tri_weeks_why',c), /검진/);
 assert.match(vm.runInContext('translations.en.tri_weeks_why',c), /exam/);
});

test('카메라 버튼 아이콘은 글자와 한 줄에 놓인다', () => {
 // Tailwind preflight가 svg를 display:block으로 만들어 아이콘과 글자가 두 줄로 갈라졌다(실기기).
 const css=fs.readFileSync(path.join(__dirname,'../static/style.css'),'utf8');
 const rule=css.match(/\.camera-btn svg\s*\{[^}]*\}/)[0];
 assert.match(rule, /display:\s*inline-block/);
});

test('일반 촬영 가이드(흔들림·플래시)는 수술 경로에서도 보인다', () => {
 const html=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
 const tag=html.match(/<div id="upload-guide"[^>]*>/)[0];
 assert.ok(!tag.includes('data-general-only'));
});

test('스크립트가 다 로드되기 전에 새 회차를 시작해도 오류로 멈추지 않는다', () => {
 // index.html 순서대로 app-report.js 이전까지만 로드한 상태 = 느린 망에서 '시작하기'를 빨리 누른 순간.
 const c=vm.createContext({state:{lang:'ko',riskAnswers:{},symptomAnswers:{}},
  window:{addEventListener(){}},document:{getElementById:()=>null,addEventListener(){}},
  localStorage:{getItem:()=>null,setItem(){}},history:{replaceState(){}},console});
 for(const file of ['data.js','app-report-text.js','app-safety-copy.js','app-surgery.js','app-core.js'])
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',file),'utf8'),c);
 assert.equal(vm.runInContext("typeof cancelAiOpinion",c),'undefined');
 assert.doesNotThrow(()=>vm.runInContext('invalidateScreeningReport()',c));
});

function mapSetup(outcomes) {
 // outcomes: 차례로 돌려줄 결과 — 'timeout' 또는 'ok'
 const calls=[], status={innerText:''};
 const c=vm.createContext({state:{lang:'ko'},console,window:{addEventListener(){}},
  document:{getElementById:id=>id==='map-status'?status:{}},
  navigator:{geolocation:{getCurrentPosition(ok,err,opts){
   calls.push(opts.timeout);
   const o=outcomes.shift();
   if(o==='ok') ok({coords:{latitude:37.5,longitude:127}}); else err({code:3});
  }}},
  L:{marker:()=>({addTo(){return this},bindPopup(){return this},remove(){}})}});
 vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/data.js'),'utf8'),c);
 vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/app-map.js'),'utf8'),c);
 c.ensureMap=()=>({setView(){}}); c.clearMapExample=()=>{}; c.fetchClinics=()=>{c.fetched=true;};
 c.setButtonBusy=()=>()=>{c.restored=(c.restored||0)+1;};
 vm.runInContext('findNearbyClinics()',c);
 return {c,calls,status};
}

test('첫 위치 측정이 시간 초과면 한 번 더 길게 기다린다', () => {
 const {c,calls}=mapSetup(['timeout','ok']);
 assert.deepEqual(calls,[10000,20000]);
 assert.equal(c.fetched,true);
 assert.equal(c.restored,1,'버튼은 재시도 사이에 풀리지 않고 한 번만 복구된다');
 assert.equal(vm.runInContext('_locating',c),false);
});

test('두 번 다 시간 초과면 그때 안내하고 무한 재시도하지 않는다', () => {
 const {c,calls,status}=mapSetup(['timeout','timeout']);
 assert.deepEqual(calls,[10000,20000]);
 assert.equal(status.innerText,vm.runInContext('translations.ko.map_status_timeout',c));
 assert.equal(vm.runInContext('_locating',c),false);
});

test('시력교정 수술 이력이 있으면 고도근시를 "수술 전" 기준으로 묻는다', () => {
 // 2026-09-23 교수님 시연: 라섹 받은 60대로 진행하자 "수술했는데 왜 고도근시가 나오지?"
 for (const lang of ['ko','en','es','fr','ja','zh']) {
  const c=setup({lang,riskAnswers:{surgery:'past',surgery_type:'laser'}});
  const q=vm.runInContext("symptomQuestionText(activeSymptomQuestions().find(q=>q.code==='gla_myopia'))",c);
  assert.equal(q, vm.runInContext(`translations.${lang}.q_gla_myopia_prelaser`,c), lang);
  const plain=setup({lang,riskAnswers:{surgery:'none'}});
  assert.equal(vm.runInContext("symptomQuestionText(activeSymptomQuestions().find(q=>q.code==='gla_myopia'))",plain),
   vm.runInContext(`translations.${lang}.q_gla_myopia`,plain), lang);
 }
});

test('수술 경로의 촬영 버튼은 "수술 관련 사진"이라고 부르지 않는다', () => {
 // 같은 회의: "왜 수술 관련 사진 촬영이야? 수술 부위를 찍어야 하는지 헷갈린다"
 const c=setup({});
 for (const lang of ['ko','en','es','fr','ja','zh']) {
  const t=vm.runInContext(`translations.${lang}`,c);
  assert.ok(!/수술 관련|surgery-related|relacionada con la cirugía|liée à l’opération|手術に関する|手术相关/.test(t.post_camera_btn+t.post_photo_upload_title), lang);
 }
 assert.equal(vm.runInContext('translations.ko.nav_disease',c),'질환 안내');
});

test('AI 소견 요청에 문진 항목·위험요인 코드가 언어와 무관하게 실린다', () => {
 const c=vm.createContext({state:{lang:'en',riskAnswers:{diabetes:true,hypertension:false,smoking:true,age:'60s'},
  chatSymptoms:['sym_chk_recent','sym_dr_fundus','번역된 문장']},window:{addEventListener(){}},console});
 const src=fs.readFileSync(path.join(__dirname,'../static/app-report.js'),'utf8');
 vm.runInContext(src.slice(src.indexOf('function opinionFlagCodes'),src.indexOf('async function finish')),c);
 assert.deepEqual(Array.from(vm.runInContext('opinionFlagCodes()',c)),
  ['sym_chk_recent','sym_dr_fundus','risk_diabetes','risk_smoking','age_60s']);
});

test('맞춤 질문의 답이 리포트 해석·AI 조언 코드·챗봇 문맥에 모두 실린다', () => {
 // 2026-09-28: 맞춤 질문에 답해도 결과가 그대로라 "왜 물어봤지?"가 됐다.
 const c=setup({lang:'ko',riskAnswers:{surgery:'none',diabetes:true,age:'60s'},chatSymptoms:['sym_chk_recent'],
  dynamicAnswers:[{q:'최근 한 달 동안 안약을 사용한 적이 있나요?',a:'네',value:true,question_id:'eye_drops'},
                  {q:'혈당이 목표보다 자주 높나요?',a:'아니오',value:false,question_id:'sugar_off_target'}],
  amslerResult:{}});
 c.document={getElementById:()=>null};
 for(const f of ['app-findings.js']) vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',f),'utf8'),c);
 const core=fs.readFileSync(path.join(__dirname,'../static/app-core.js'),'utf8');
 vm.runInContext(core.slice(core.indexOf('function formatCataractResult()'),core.indexOf('const ERROR_MARKER')),c);
 const src=fs.readFileSync(path.join(__dirname,'../static/app-report.js'),'utf8');
 vm.runInContext(src.slice(src.indexOf('function opinionFlagCodes'),src.indexOf('async function finish')),c);
 vm.runInContext(src.slice(src.indexOf('function buildChatContext'),src.indexOf('/** \'내 결과 쉽게')),c);
 const findings=vm.runInContext('buildFindings()',c);
 const personal=findings.find(line=>line.startsWith('AI 맞춤 질문에 답한 내용'));
 assert.ok(personal && personal.includes('안약') && personal.includes('→ 네'));
 const codes=Array.from(vm.runInContext('opinionFlagCodes()',c));
 assert.ok(codes.includes('ans_eye_drops'));
 assert.ok(!codes.includes('ans_sugar_off_target'),"'아니오'는 조언을 열지 않는다");
 const ctx=vm.runInContext('buildChatContext()',c);
 assert.ok(ctx.includes('안약') && ctx.includes('검사 요약 해석'),'챗봇이 검사 해석과 맞춤 질문 답을 안다');
 assert.ok(ctx.length<=5000);
});

test('리포트에 "내 검사 결과를 쉽게 설명해 줘" 버튼이 6개 언어로 있다', () => {
 const html=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
 assert.match(html,/id="followup-explain-btn"[^>]*onclick="askExplainResults\(\)"/);
 const c=setup({});
 for(const lang of ['ko','en','es','fr','ja','zh']) assert.ok(vm.runInContext(`translations.${lang}.rep_followup_explain`,c),lang);
});

test('chat context distinguishes unknown, no and unanswered risk factors',()=>{
 const c=setup({lang:'ko',riskAnswers:{surgery:'none',diabetes:'unknown',hypertension:false},chatSymptoms:[],amslerResult:{}});
 c.document={getElementById:()=>null};
 const src=fs.readFileSync(path.join(__dirname,'../static/app-report.js'),'utf8');
 vm.runInContext(src.slice(src.indexOf('function buildChatContext'),src.indexOf('/** \'내 결과 쉽게')),c);
 const ctx=vm.runInContext('buildChatContext()',c);
 assert.ok(ctx.includes('"diabetes":"unknown"'));
 assert.ok(ctx.includes('"hypertension":false'));
 assert.ok(!ctx.includes('"smoking":false'));
});
