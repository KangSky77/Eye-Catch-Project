// 수술 여부 확인(step-surgery)이 검사 경로를 실제로 가른다.
//
// 왜 함수를 돌려보는가: 답을 어디에 저장하느냐가 핵심이다. 사진을 올릴 때마다
// resetScreeningState()가 돌아 riskAnswers를 비우므로, 답을 riskAnswers에만 두면
// 문진에 닿기 전에 '수술한 눈'이라는 사실이 사라지고 사진 판독이 그대로 적용된다.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');

function slice(file,from,to){
 const src=fs.readFileSync(path.join(__dirname,'..','static',file),'utf8');
 const start=src.indexOf(from);assert.notEqual(start,-1,`${file}: ${from}`);
 const end=to?src.indexOf(to,start):src.length;assert.notEqual(end,-1,`${file}: ${to}`);
 return src.slice(start,end);
}
function setup(){
 const steps=[],messages=[],tracked=[];
 const c=vm.createContext({
  console,setTimeout(){},window:{addEventListener(){}},
  document:{body:{dataset:{}},getElementById:()=>({innerHTML:'',classList:{add(){},remove(){},toggle(){}}}),
   querySelectorAll:()=>tracked,querySelector:()=>null},
  state:{lang:'ko'},
  nextStep:s=>steps.push(s),showTab(){},addMsg:(who,text)=>messages.push(`${who}:${text}`),
  cancelEyeAnalysis(){},startAmslerStep:()=>steps.push('step-amsler'),
  invalidateScreeningReport(){},removeLoadingMsg(){},setChatAnswerMode(){},
  askRiskQuestion(){},scrollChatToLatest(){},renderChatOptions(){},
 });
 for(const f of ['data.js','app-report-text.js','app-safety-copy.js','app-surgery.js','app-chat.js'])
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',f),'utf8'),c);
 // 실제 초기화 함수를 쓴다 — 이 테스트의 핵심이 그것과의 상호작용이다
 vm.runInContext(slice('app-core.js','function resetScreeningState()','\nfunction invalidateScreeningReport()'),c);
 // 화면을 그리는 함수는 app-chat.js가 자기 정의로 덮어쓴다. 여기서 보는 것은 '무엇을
 // 묻는가'이므로 로드 뒤에 다시 스텁으로 바꾼다(DOM을 흉내 낼 필요가 없다).
 c.addMsg=(who,text)=>messages.push(`${who}:${text}`);
 c.askRiskQuestion=()=>{};
 c.renderChatOptions=()=>{};
 return {c,steps,messages,tracked,run:s=>vm.runInContext(s,c)};
}

test("'아니오'는 문진 첫 문항의 답이 되어 다시 묻지 않는다",()=>{
 const x=setup();
 x.run('answerSurgeryGate(false)');
 assert.equal(x.c.state.riskAnswers.surgery,'none');
 x.run('resetScreeningState()');   // 사진을 한 장 올릴 때마다 일어나는 일
 assert.equal(x.c.state.riskAnswers.surgery,'none','초기화가 게이트 답을 지웠다');
 x.run('startChat()');
 assert.equal(x.c.state.riskIdx,1,'수술 여부를 다시 물었다');
 assert.equal(x.run('activeRiskQuestions()[state.riskIdx].code'),'age');
 assert.ok(!x.messages.some(m=>m.includes('수술 병원에 문의')),'수술자 안내가 잘못 붙었다');
 assert.equal(x.steps[x.steps.length-1],'step-guide');
});

test("'예'는 시기·종류를 문진에서 이어 묻는다 — 시작 화면은 질문 하나로 끝난다",()=>{
 const x=setup();
 x.run('answerSurgeryGate(true)');
 assert.equal(x.steps[x.steps.length-1],'step-guide','시작 화면에서 더 묻고 있다');
 assert.equal(x.c.state.hadSurgery,true);
 x.run('resetScreeningState()');
 assert.equal(x.c.state.hadSurgery,true,'초기화가 게이트 답을 지웠다');

 x.run('startChat()');
 assert.equal(x.c.state.riskIdx,0,'시기를 묻지 않고 건너뛰었다');
 assert.equal(x.run('activeRiskQuestions()[0].code'),'surgery');
 // 이미 '예'라고 답했으므로 '수술한 적 없습니다'는 선택지에 없어야 한다(모순 방지)
 assert.deepEqual(x.run('activeRiskQuestions()[0].options.map(o=>o.v).join()').split(','),
  ['recent','past']);
 assert.equal(x.run('riskQuestionText(activeRiskQuestions()[0])'),
  x.run('translations.ko.gate_when_q'),'문구가 아직 "받은 적이 있나요?"다');

 // 시기를 답하면 그때부터 종류·인공수정체 이력이 이어진다
 x.c.state.riskAnswers.surgery='recent';
 assert.equal(x.run("activeRiskQuestions().map(q=>q.code).join()"),
  'surgery,surgery_type,surgery_eye,surgery_sym_eye');
 x.c.state.riskAnswers.surgery_type='laser';
 assert.ok(x.run("activeRiskQuestions().some(q=>q.code==='surgery_lens_history')"));
});

test("시기를 모르는 동안에는 판독 적용 여부를 '미정'으로 둔다",()=>{
 const x=setup();
 x.run('answerSurgeryGate(true)');
 // 사진은 이미 올렸는데 시기·종류를 아직 안 물은 구간 — 점수를 먼저 보여주면 나중에 취소해야 한다
 x.c.state.aiResultCode='risk';
 x.c.state.aiResultData={code:'risk',probability:90,twoEyes:false};
 assert.equal(x.run('surgeryHistoryPending()'),true);
 assert.equal(x.run('lensStatus()'),'unknown','수술 이력을 잊었다');
 assert.equal(x.run('photoAssessmentExcluded()'),true);
 // 라식 + 인공수정체 없음이 확인되면 판독이 살아난다
 Object.assign(x.c.state.riskAnswers,{surgery:'recent',surgery_type:'laser',surgery_lens_history:'no'});
 assert.equal(x.run('surgeryHistoryPending()'),false);
 assert.equal(x.run('photoAssessmentExcluded()'),false);
});

test('수술 후 촬영 안내는 시기를 묻기 전에 이미 보여야 한다',()=>{
 // 보호대를 벗지 말라는 안내와 '사진 없이 다음 단계로'는 사진을 찍기 전에 필요하다.
 const x=setup();
 const only=[{hidden:true},{hidden:true}];
 x.c.document.querySelectorAll=()=>only;
 x.run('answerSurgeryGate(true)');
 assert.ok(only.every(el=>el.hidden===false),'수술 전용 안내가 감춰져 있다');
 x.run('answerSurgeryGate(false)');
 assert.ok(only.every(el=>el.hidden===true),'수술하지 않은 사람에게 술후 안내가 보인다');
});

test('안대·보호대로 못 찍는 사람은 사진을 건너뛰고 나머지 단계를 잇는다',()=>{
 const x=setup();
 x.run('answerSurgeryGate(true)');
 x.run('skipPhotoStep()');
 assert.equal(x.c.state.aiResultCode,'postop','사진을 올리지 않았다는 표시가 없다');
 assert.equal(x.c.state.aiResultData,null);
 assert.equal(x.steps[x.steps.length-1],'step-amsler','황반 검사로 이어지지 않았다');
 assert.equal(x.run('effectiveCataractCode()'),'postop');
});

test('일반 검사로 돌아오면 이전 회차의 수술 답이 남지 않는다',()=>{
 const x=setup();
 x.run('answerSurgeryGate(true)');
 x.c.state.riskAnswers.surgery='recent';
 x.run('startScreening()');
 assert.equal(x.c.state.hadSurgery,null);
 assert.equal(x.c.state.riskAnswers.surgery,undefined);
 assert.equal(x.run('hasSurgery()'),false);
 assert.equal(x.steps[x.steps.length-1],'step-surgery');
});
