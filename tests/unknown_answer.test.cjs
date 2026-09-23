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
 const tri=vm.runInContext(`computeTriage({cataractCode:'postop',redFlags:[]})`,r.c);
 assert.equal(tri.level,'now','퇴원 안내를 모르는데 경과 관찰로 안내했다');
 // 증상이 없으므로 '증상을 문의하세요'가 아니라 안내를 다시 확인하라고 말해야 한다
 assert.equal(tri.kind,'confirm');
 assert.equal(tri.label,vm.runInContext('translations.ko.post_confirm',r.c));
 // 실제 증상 악화가 함께 있으면 증상 문의가 우선이다
 vm.runInContext(`state.symptomAnswers.post_worse=true`,r.c);
 assert.equal(vm.runInContext(`computeTriage({cataractCode:'postop',redFlags:[]}).kind`,r.c),'contact');
});

test('문진 중 언어를 바꿔도 모르겠어요 버튼과 수술 시기 문구가 유지된다',()=>{
 const {c}=loadChat();
 c.__opts=[];
 vm.runInContext(`
  renderChatOptions=o=>__opts.push(o.map(x=>x.label));
  const realGet=document.getElementById;
  document.getElementById=id=>id==='step-chat'?{classList:{contains:()=>true}}
   :id==='chat-box'?{querySelectorAll:()=>[]}:realGet(id);
  state.chatBusy=false;state.symptomAnswers={};state.chatHistory=[];`,c);
 const ask=(setup,lang)=>{c.__setup=setup;c.__lang=lang;c.__opts.length=0;
  vm.runInContext(`Object.assign(state,__setup);state.lang=__lang;refreshChatLanguage();`,c);
  return c.__opts[0]||[];};
 // 위험요인(예/아니오형): 당뇨
 let opts=ask({hadSurgery:false,gateAnswers:{surgery:'none'},riskAnswers:{surgery:'none',age:'60s'},riskIdx:1},'en');
 assert.ok(opts.includes(vm.runInContext('translations.en.chat_unknown',c)),`언어 전환 후 모르겠어요가 사라졌다: ${opts}`);
 // 증상(비응급): 빛 번짐
 opts=ask({riskAnswers:{surgery:'none',age:'60s',diabetes:false,hypertension:false,family:false,smoking:false},
  riskIdx:99,symIdx:vm.runInContext(`activeSymptomQuestions().findIndex(q=>q.code==='cat_glare')`,c)},'ja');
 assert.equal(opts.length,3,`비응급 증상 문항의 선택지가 줄었다: ${opts}`);
 // 응급 문항에는 여전히 모르겠어요가 없다
 opts=ask({symIdx:0},'fr');
 assert.equal(opts.length,2,'응급 문항에 모르겠어요가 생겼다');
 // 수술 시기 질문: 화면에 떠 있는 질문 말풍선이 어떤 문장으로 바뀌는지 본다
 c.__text={nodeType:3,nodeValue:'언제 수술을 받으셨나요?'};
 vm.runInContext(`Node={TEXT_NODE:3};
  const prevGet=document.getElementById;
  document.getElementById=id=>id==='chat-box'
   ?{querySelectorAll:sel=>sel.includes('chat-bot')?[{firstElementChild:{lastChild:__text}}]:[]}:prevGet(id);`,c);
 ask({hadSurgery:true,gateAnswers:{},riskAnswers:{},riskIdx:0,symIdx:0},'en');
 assert.equal(c.__text.nodeValue,vm.runInContext('translations.en.gate_when_q',c),'수술 시기 질문이 수술 여부 질문으로 되돌아갔다');
});

test('증상 문항에서 모르겠어요는 위험 신호로 세지 않는다',()=>{
 // handleSymptomAnswer의 판정식이 엄격 비교여야 'unknown'이 어느 쪽에도 걸리지 않는다.
 const src=fs.readFileSync(path.join(__dirname,'../static/app-chat.js'),'utf8');
 const fn=src.slice(src.indexOf('function handleSymptomAnswer'));
 assert.match(fn,/q\.invert \? \(yes === false\) : \(yes === true\)/,
  '느슨한 비교로 바뀌면 모른다가 위험 신호로 세어진다');
});

test('AI 맞춤 질문 표시 중 언어 전환은 현재 질문과 버튼을 새 언어로 바꾼다',()=>{
 const {c}=loadChat();c.__opts=[];c.__modes=[];c.__text={nodeType:3,nodeValue:'한국어 맞춤 질문'};
 vm.runInContext(`
  Node={TEXT_NODE:3};
  renderChatOptions=o=>__opts.push(o.map(x=>x.label));
  setChatAnswerMode=mode=>__modes.push(mode);
  document.getElementById=id=>id==='step-chat'?{classList:{contains:()=>true}}
   :id==='chat-box'?{querySelectorAll:sel=>sel.includes('chat-bot')?[{firstElementChild:{lastChild:__text}}]:[]}
   :null;
  state.lang='en';state.chatBusy=false;state.riskAnswers={surgery:'none'};state.symptomAnswers={};
  state.riskIdx=99;state.symIdx=99;state.chatHistory=[{q:'한국어 맞춤 질문',a:''}];
  state.dynamicQuestion={text:'한국어 맞춤 질문',lang:'ko',answerType:'text'};
  refreshChatLanguage();`,c);
 const fallback=vm.runInContext('translations.en.nextq_fallback',c);
 assert.equal(c.__text.nodeValue,fallback);
 assert.equal(vm.runInContext('state.chatHistory.at(-1).q',c),fallback);
 assert.deepEqual(Array.from(c.__opts.at(-1)),[
  vm.runInContext('translations.en.chat_yes',c),vm.runInContext('translations.en.chat_no',c)]);
 assert.equal(c.__modes.at(-1),'yesno');
});

test('맞춤 질문 생성 중 바뀐 언어의 응답만 화면에 표시한다',async()=>{
 const {c}=loadChat();c.__msgs=[];c.__opts=[];let resolveFetch;
 c.fetch=()=>new Promise(resolve=>{resolveFetch=resolve});
 vm.runInContext(`
  addMsg=(who,text)=>__msgs.push(text);
  renderChatOptions=o=>__opts.push(o.map(x=>x.label));
  removeLoadingMsg=()=>{};setChatAnswerMode=()=>{};
  state.lang='ko';state.sessionGeneration=1;state.chatHistory=[];
  state.riskAnswers={surgery:'none'};
  state.riskIdx=99;state.symIdx=99;
 `,c);
 const pending=vm.runInContext('fetchNextQuestion()',c);
 vm.runInContext("state.lang='en'",c);
 resolveFetch({json:async()=>({question:'한국어로 만든 질문인가요?',answer_type:'text'})});
 await pending;
 assert.equal(c.__msgs.at(-1),vm.runInContext('translations.en.nextq_fallback',c));
 assert.equal(vm.runInContext('state.dynamicQuestion.lang',c),'en');
 assert.equal(c.__opts.at(-1)[0],vm.runInContext('translations.en.chat_yes',c));
});
