const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const read = name => fs.readFileSync(path.join(__dirname,'../static',name),'utf8');
function context() {
 const timers=[],steps=[];
 const box={innerHTML:'before answer',scrollHeight:1,scrollTop:0};
 const nodes={'chat-box':box,'survey-undo':{},'report-edit-answers':{},'survey-progress-text':{},'survey-skip-extra':{},'chat-current-question':{focus(){}}};
 const c=vm.createContext({console,structuredClone,AbortController,
  setTimeout:f=>{timers.push(f);return timers.length},clearTimeout(){},
  state:{lang:'ko',sessionGeneration:1,hadSurgery:false,gateAnswers:{surgery:'none'},riskIdx:1,symIdx:0,stepIdx:0,
   riskAnswers:{surgery:'none',age:'20s'},symptomAnswers:{},chatHistory:[],chatSymptoms:[],symptomCodes:[],
   redFlags:[],symptomScore:0,dynamicCount:0,dynamicAnswers:[],dynamicQuestion:null,freeAnswers:[],maxDynamic:2,aiResultCode:'normal',surveyUndo:[],step:'step-chat'},
  document:{getElementById:id=>nodes[id]||null},window:{addEventListener(){}},
  nextStep:s=>{steps.push(s);c.state.step=s},showTab(){},invalidateScreeningReport(){c.state.triage=null},removeLoadingMsg(){},
 });
 for(const file of ['data.js','app-report-text.js','app-safety-copy.js','app-ux-copy.js','app-surgery.js','app-chat.js']) vm.runInContext(read(file),c);
 c.addMsg=()=>{};c.refreshChatLanguage=()=>{};c.updateSurveyModeBanner=()=>{};c.refreshAiResultDisplay=()=>{};
 c.askRiskQuestion=()=>{c.asked=(c.asked||0)+1};c.askSymptomQuestion=()=>{c.asked=(c.asked||0)+1};
 return {c,box,nodes,timers,steps,run:s=>vm.runInContext(s,c)};
}
test('editing a risk answer restores its previous branch and suppresses the scheduled next question',()=>{
 const x=context();x.run('handleAnswer(true,"네")');
 assert.equal(x.c.state.riskAnswers.diabetes,true);
 assert.equal(x.c.state.surveyUndo.length,1);
 x.run('editLastSurveyAnswer()');
 assert.equal(x.c.state.riskAnswers.diabetes,undefined);
 assert.equal(x.c.state.riskIdx,1);
 assert.equal(x.box.innerHTML,'before answer');
 for(const timer of x.timers)timer();
 assert.equal(x.c.asked,undefined,'stale answer transition must not advance the restored question');
 x.run('handleAnswer(false,"아니오")');
 assert.equal(x.c.state.riskAnswers.diabetes,false);
 assert.ok(!x.run('activeSymptomQuestions().some(q=>q.code==="dr_fundus")'));
});
test('editing an emergency answer removes its derived score and flag before recalculating',()=>{
 const x=context();x.c.state.riskIdx=x.run('activeRiskQuestions().length');
 x.c.state.symIdx=x.run('activeSymptomQuestions().findIndex(q=>q.redFlag)');
 x.c.finish=()=>{x.c.state.triage={level:'urgent'}};
 x.run('handleSymptomAnswer(true)');
 assert.equal(x.c.state.triage.level,'urgent');assert.ok(x.c.state.redFlags.length);
 x.run('editLastSurveyAnswer()');
 assert.equal(x.c.state.triage,null);assert.equal(x.c.state.redFlags.length,0);assert.equal(x.c.state.symptomScore,0);
 assert.equal(x.c.state.chatSymptoms.length,0);
 x.run('handleSymptomAnswer(false)');assert.equal(x.c.state.redFlags.length,0);
});
test('editing an extra answer restores its unanswered question and cancels the stale next request',()=>{
 const x=context();x.c.state.stepIdx=x.run('questions.ko.length');x.c.state.riskIdx=x.run('activeRiskQuestions().length');
 x.c.state.symIdx=x.run('activeSymptomQuestions().length');
 x.c.state.chatHistory=[{q:'안약을 사용했나요?',a:'',question_id:'eye_drops'}];
 x.c.state.dynamicQuestion={text:'안약을 사용했나요?',lang:'ko',answerType:'yesno',id:'eye_drops'};
 x.run('handleChatAnswer(true)');assert.equal(x.c.state.dynamicCount,1);assert.equal(x.c.state.dynamicAnswers.length,1);
 let aborted=0;x.c.state.questionController={abort(){aborted++}};
 x.run('editLastSurveyAnswer()');assert.equal(aborted,1);
 assert.equal(x.c.state.dynamicCount,0);assert.equal(x.c.state.dynamicAnswers.length,0);
 assert.equal(x.c.state.chatHistory[0].a,'');assert.equal(x.c.state.dynamicQuestion.id,'eye_drops');
 for(const timer of x.timers)timer();assert.equal(x.c.state.dynamicCount,0);
});
test('optional-question skip cancels generation and does not preserve an unanswered result',()=>{
 const x=context();x.c.state.stepIdx=x.run('questions.ko.length');
 x.c.state.chatHistory=[{q:'Completed',a:'No'},{q:'Not answered',a:''}];
 let aborted=0,finished=0;x.c.state.questionController={abort(){aborted++}};x.c.finish=()=>finished++;
 x.c.clearChatControls=()=>{};x.run('skipExtraQuestions()');
 assert.equal(aborted,1);assert.equal(finished,1);assert.equal(x.c.state.chatHistory.length,1);
 assert.equal(x.c.state.dynamicQuestion,null);
});
test('home preserves completed findings; a cancelled new check preserves them too',()=>{
 const x=context();x.c.state.triage={level:'monitor'};x.c.state.aiResultCode='normal';x.c.state.navEpoch=1;
 x.c.screeningInProgress=()=>true;x.c.history={replaceState(){}};
 let resets=0,confirmations=0;x.c.resetScreeningState=()=>resets++;x.c.applyTrack=()=>{};
 x.c.window.confirm=()=>{confirmations++;return false};
 const core=read('app-core.js');vm.runInContext(core.slice(core.indexOf('function goHome()'),core.indexOf('/** Start a new screening')),x.c);
 x.run('goHome()');assert.equal(resets,0);assert.equal(x.c.state.triage.level,'monitor');assert.equal(confirmations,0);
 x.run('startScreening()');assert.equal(resets,0);assert.equal(confirmations,1);assert.equal(x.c.state.aiResultCode,'normal');
});
test('first-visit controls and progress labels exist in all six languages',()=>{
 const x=context();for(const lang of ['ko','en','es','fr','ja','zh']) {
  x.c.state.lang=lang;const t=x.run('translations[state.lang]');
  for(const key of ['intro_preparation','intro_limit','new_screening_confirm','leave_screening_confirm','survey_undo','survey_extra_hint','survey_skip_extra','report_details'])assert.ok(t[key],`${lang}:${key}`);
  const label=x.run('surveyProgressLabel("4","19")');assert.ok(label.includes('4')&&label.includes('19'),lang);
 }
});
test('score-question recognition is available in every language and unrelated questions remain free chat',()=>{
 const c=vm.createContext({});const source=read('app-report-chat.js');
 vm.runInContext(source.slice(source.indexOf('function isScoreQuestion('),source.indexOf('async function askGemmaMore(')),c);
 for(const message of ['AI 특징 점수','AI score','puntuación de IA','score de signes IA','AI特徴スコア','AI特征评分','0/100이 무슨 뜻?'])assert.ok(vm.runInContext(`isScoreQuestion(${JSON.stringify(message)})`,c));
 for(const message of ['관리 방법','How can I protect my eyes?'])assert.equal(vm.runInContext(`isScoreQuestion(${JSON.stringify(message)})`,c),false);
});
test('the next opinion retries only a cancelling visitor job and cancellation stops the retry',async()=>{
 const c=vm.createContext({AbortController,DOMException,setTimeout:f=>{f();return 1},clearTimeout(){}});
 const source=read('app-report.js');vm.runInContext(source.slice(source.indexOf('async function fetchOpinionWhenReady('),source.indexOf('async function runAiOpinion(')),c);
 let calls=0;
 c.fetch=async()=>++calls===1?{status:409,clone:()=>({json:async()=>({detail:{code:'VISITOR_BUSY'}})})}:{status:200};
 // Use a queued microtask to model a clock tick without real wait time.
 c.setTimeout=f=>{queueMicrotask(f);return 1};
 const controller=new AbortController();c.signal=controller.signal;
 assert.equal((await vm.runInContext('fetchOpinionWhenReady({},signal)',c)).status,200);assert.equal(calls,2);
 calls=0;c.fetch=async()=>{calls++;controller.abort();return {status:409,clone:()=>({json:async()=>({detail:{code:'VISITOR_BUSY'}})})}};
 await assert.rejects(vm.runInContext('fetchOpinionWhenReady({},signal)',c),{name:'AbortError'});
 assert.equal(calls,1);
 const other=new AbortController();c.signal=other.signal;c.fetch=async()=>({status:429,clone:()=>({json:async()=>({detail:{code:'WAITING_ROOM_REQUIRED'}})})});
 assert.equal((await vm.runInContext('fetchOpinionWhenReady({},signal)',c)).status,429);
});
test('score definition displays without admission or any server/model request',async()=>{
 const c=vm.createContext({state:{lang:'ko',triage:{level:'monitor'}},window:{addEventListener(){}},
  fetch(){throw new Error('No model request')},eyeCatchAdmission:{ensure(){throw new Error('No queue')}},
  document:{getElementById:id=>id==='user-followup-input'?input:response}});
 const input={value:'AI 특징 점수 0/100이 무슨 뜻인가요?'};
 const response={innerText:'',classList:{remove(){}}};
 for(const file of ['data.js','app-report-text.js','app-ux-copy.js','app-report-chat.js']) vm.runInContext(read(file),c);
 await vm.runInContext('askGemmaMore()',c);
 assert.ok(response.innerText.includes('질병에 걸릴 확률이 아니라'));
 assert.ok(response.innerText.includes('눈 전체의 건강 상태를 평가하는 점수도 아닙니다'));
 assert.equal(input.value,'');
});
