// 문진의 세 번째 선택지 '모르겠어요'.
//
// 왜 필요한가: 위험요인·과거력에는 본인도 모르는 것이 있다("가족 중 녹내장 진단",
// "안압이 높다는 말"). 네/아니오만 주면 모르는 사람이 찍어서 답하고 그 답이 점수에 들어간다.
//
// 지켜야 할 두 가지:
//   1) '모르겠어요'는 위험요인으로 세지 않는다(모른다 ≠ 그렇다).
//   2) 응급 신호 문항에는 두지 않는다 — 지금 아픈지는 본인이 아는 것이고,
//      애매한 답을 받으면 응급 안내를 띄울지가 흐려진다.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');

function load(){
 const c=vm.createContext({console,state:{lang:'ko'},document:{getElementById:()=>null,createElement:()=>({})}});
 for(const f of ['data.js','app-safety-copy.js','app-assess.js'])
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',f),'utf8'),c);
 return c;
}

test('모르겠어요 라벨이 여섯 개 언어에 모두 있다',()=>{
 const c=load();
 const ko=vm.runInContext('translations.ko.chat_unknown',c);
 for(const lang of ['ko','en','es','fr','ja','zh']){
  const v=vm.runInContext(`translations.${lang}.chat_unknown`,c);
  assert.ok(v,`${lang}: chat_unknown이 없다`);
  if(lang!=='ko') assert.notEqual(v,ko,`${lang}: 한국어 문구가 그대로다`);
 }
});

test('모르겠어요는 위험 점수를 올리지 않는다',()=>{
 const c=load();
 const 네 = vm.runInContext("computeRiskScore({diabetes:true,hypertension:true,family:true,smoking:true})",c);
 const 모름 = vm.runInContext("computeRiskScore({diabetes:'unknown',hypertension:'unknown',family:'unknown',smoking:'unknown'})",c);
 const 아니오 = vm.runInContext("computeRiskScore({diabetes:false,hypertension:false,family:false,smoking:false})",c);
 assert.ok(네.score > 0,'대조군: 네는 점수가 올라야 한다');
 assert.equal(모름.score,아니오.score,'모른다가 위험요인으로 세어졌다');
 // vm 안에서 만들어진 배열이라 deepEqual은 realm이 달라 실패한다 — 길이로 본다
 assert.equal(모름.factors.length,0,'모른다가 위험요인 목록에 들어갔다');
});

test('응급 신호 문항에는 모르겠어요를 두지 않는다',()=>{
 const src=fs.readFileSync(path.join(__dirname,'../static/app-chat.js'),'utf8');
 const fn=src.slice(src.indexOf('function askSymptomQuestion()'),src.indexOf('function handleSymptomAnswer'));
 assert.match(fn,/q\.redFlag/,'적신호 문항을 가려내지 않는다');
 // 적신호 분기에는 yesNoUnknownOptions가 오면 안 된다
 const redFlagBranch=fn.slice(fn.indexOf('q.redFlag'),fn.indexOf('yesNoUnknownOptions'));
 assert.ok(!/chat_unknown/.test(redFlagBranch),'적신호 문항에 모르겠어요가 들어갔다');
});

// 버튼이 실제로 부르는 경로(handleAnswer)로 돌린다. 안쪽 비교식만 문자열로 검사하던 동안
// 호출부가 'unknown'을 false로 바꿔 넘겨, '모르겠어요'가 '아니오'로 기록되고
// 역문항(최근 2년 내 검진)에서는 '2년 내 검진 없음'이 위험 소견으로 추가됐다.
function loadChat(){
 const node=()=>({innerHTML:'',className:'',dataset:{},style:{},children:[],lastChild:null,
  classList:{add(){},remove(){},toggle(){},contains(){return false;}},
  appendChild(){},append(){},setAttribute(){},removeAttribute(){},focus(){},querySelectorAll(){return [];}});
 const msgs=[];
 const c=vm.createContext({console,__msgs:msgs,setTimeout:()=>0,clearTimeout(){},requestAnimationFrame:()=>0,
  performance:{now:()=>0},window:{addEventListener(){}},addEventListener(){},
  history:{pushState(){},replaceState(){}},localStorage:{getItem(){return null;},setItem(){}},navigator:{language:'ko'},
  document:{getElementById:()=>node(),createElement:()=>node(),createTextNode:()=>({}),querySelectorAll:()=>[],
   addEventListener(){},body:{dataset:{},classList:{add(){}}},documentElement:{setAttribute(){}}}});
 for(const f of ['data.js','app-photo-review.js','app-safety-copy.js','app-report-text.js','app-surgery.js','app-core.js','app-chat.js','app-assess.js'])
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',f),'utf8'),c);
 vm.runInContext(`addMsg=(who,text)=>__msgs.push(who+':'+text);renderChatOptions=()=>{};clearChatControls=()=>{};finish=()=>{};finishSurvey=()=>{};`,c);
 return {c,msgs};
}
function answerSymptom(code,value,{surgery='none',extra={}}={}){
 const {c,msgs}=loadChat();
 c.__setup={surgery,extra,code};
 vm.runInContext(`
  state.lang='ko';state.hadSurgery=__setup.surgery!=='none';state.gateAnswers={surgery:__setup.surgery};
  state.riskAnswers=Object.assign({surgery:__setup.surgery,age:'60s',diabetes:false,hypertension:false,family:false,smoking:false},__setup.extra);
  state.riskIdx=activeRiskQuestions().length;
  state.symptomAnswers={};state.chatSymptoms=[];state.symptomCodes=[];state.chatHistory=[];state.redFlags=[];state.symptomScore=0;
  state.symIdx=activeSymptomQuestions().findIndex(q=>q.code===__setup.code);state.chatBusy=false;`,c);
 assert.ok(vm.runInContext('state.symIdx',c)>=0,`${code} 문항을 찾지 못했다`);
 c.__value=value;
 vm.runInContext(`handleAnswer(__value, __value==='unknown'?translations.ko.chat_unknown:__value?translations.ko.chat_yes:translations.ko.chat_no)`,c);
 return {c,msgs,
  answer:vm.runInContext(`state.symptomAnswers[__setup.code]`,c),
  symptoms:vm.runInContext('state.chatSymptoms.join(",")',c),
  score:vm.runInContext('state.symptomScore',c)};
}

test('모르겠어요는 모르겠어요로 기록되고 역문항에서 위험 소견을 만들지 않는다',()=>{
 const unknown=answerSymptom('chk_recent','unknown');
 assert.equal(unknown.answer,'unknown','모르겠어요가 다른 답으로 바뀌어 기록됐다');
 assert.equal(unknown.msgs.at(-1),'user:'+vm.runInContext('translations.ko.chat_unknown',unknown.c),'대화에 다른 답이 찍혔다');
 assert.equal(unknown.symptoms,'','모르겠어요가 "2년 내 검진 없음"으로 세어졌다');
 assert.equal(unknown.score,0);
 // 대조군: 실제 '아니오'는 역문항에서 위험 소견이 된다
 const no=answerSymptom('chk_recent',false);
 assert.equal(no.symptoms,'sym_chk_recent');
 assert.equal(no.score,2);
});

test('안저검사 역문항도 모르겠어요를 미시행으로 세지 않는다',()=>{
 const r=answerSymptom('dr_fundus','unknown',{extra:{diabetes:true}});
 assert.equal(r.answer,'unknown');
 assert.equal(r.symptoms,'');
});

test('수술 후 퇴원 안내를 따를 수 있는지 모르면 수술팀 연락으로 안내한다',()=>{
 const r=answerSymptom('post_followup','unknown',{surgery:'recent',extra:{surgery_type:'laser'}});
 assert.equal(r.answer,'unknown');
 const level=vm.runInContext(`computeTriage({cataractCode:'postop',redFlags:[]}).level`,r.c);
 assert.equal(level,'now','퇴원 안내를 모르는데 경과 관찰로 안내했다');
});

test('증상 문항에서 모르겠어요는 위험 신호로 세지 않는다',()=>{
 // handleSymptomAnswer의 판정식이 엄격 비교여야 'unknown'이 어느 쪽에도 걸리지 않는다.
 const src=fs.readFileSync(path.join(__dirname,'../static/app-chat.js'),'utf8');
 const fn=src.slice(src.indexOf('function handleSymptomAnswer'));
 assert.match(fn,/q\.invert \? \(yes === false\) : \(yes === true\)/,
  '느슨한 비교로 바뀌면 모른다가 위험 신호로 세어진다');
});
