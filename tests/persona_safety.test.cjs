const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
function setup(surgery='none',lang='ko'){
 const c=vm.createContext({state:{lang,riskAnswers:{surgery},symptomAnswers:{},amslerResult:{},chatSymptoms:[]},window:{addEventListener(){}},console});
 for(const f of ['data.js','app-safety-copy.js','app-report-text.js','app-surgery.js','app-chat.js','app-assess.js','app-findings.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',f),'utf8'),c);
 const core=fs.readFileSync(path.join(__dirname,'../static/app-core.js'),'utf8');
 vm.runInContext(core.slice(core.indexOf('function formatCataractResult()'),core.indexOf('const ERROR_MARKER')),c);
 return c;
}
test('new flashes are screened regardless of diabetes or remote surgery',()=>{
 for(const surgery of ['none','past'])for(const diabetes of [true,false]){
  const c=setup(surgery);c.state.riskAnswers.diabetes=diabetes;
  assert.equal(vm.runInContext("activeSymptomQuestions().some(q=>q.code==='rf_flashes' && q.redFlag)",c),true);
 }
});
test('unmeasurable Amsler is never normal and preserves opposite-eye abnormality',()=>{
 for(const lang of ['ko','en','es','fr','ja','zh'])for(const other of [false,true,'unable']){
  const c=setup('none',lang);c.state.amslerResult={left:'unable',right:other};c.state.hasAmsler=other===true;
  assert.equal(vm.runInContext('amslerComplete()',c),false);
  const text=vm.runInContext('formatAmslerResult()',c);
  assert.ok(text.includes(vm.runInContext('translations[state.lang].ams_unmeasured',c)));
  assert.ok(text.length<=100);
  assert.equal(vm.runInContext('buildFindings().includes(translations[state.lang].find_ams_normal)',c),false);
 }
});
test('remote cataract surgery suppresses unlocalized photo inference but retains general screening',()=>{
 const c=setup('past');c.state.riskAnswers.surgery_type='cataract';c.state.aiResultCode='risk';c.state.aiResultData={code:'risk',probability:99};
 assert.equal(vm.runInContext("activeRiskQuestions().some(q=>q.code==='surgery_type')",c),true);
 assert.equal(vm.runInContext("activeRiskQuestions().some(q=>q.code==='diabetes')",c),true);
 assert.equal(vm.runInContext("computeTriage({cataractCode:'risk',redFlags:[]}).level",c),'monitor');
 assert.equal(vm.runInContext("computeTriage({cataractCode:'risk',redFlags:['rf_sudden']}).level",c),'urgent');
 assert.equal(vm.runInContext('buildFindings().includes(translations.ko.find_cat_risk)',c),false);
});
test('unperformed Amsler is passed to additional-question AI as unperformed',async()=>{
 const c=setup('today');let payload;
 Object.assign(c,{fetch:async(url,options)=>{payload=JSON.parse(options.body);return {json:async()=>({question:''})}},removeLoadingMsg(){},addMsg(){},setChatAnswerMode(){},renderChatOptions(){},addLoadingMsg(){}});
 c.state.chatHistory=[];c.state.sessionGeneration=1;c.state.hasAmsler=false;
 await vm.runInContext('fetchNextQuestion()',c);
 assert.equal(payload.amsler_res,vm.runInContext('formatAmslerResult()',c));
});

test('every urgent question ends the actual questionnaire before any extra AI request',()=>{
 let checked=0;
 for(const lang of ['ko','en','es','fr','ja','zh'])for(const surgery of ['none','past','today','recent']){
  const c=setup(surgery,lang);let finishes=0;
  Object.assign(c,{addMsg(){},clearChatControls(){},finish(){finishes++},setTimeout(){throw Error('urgent answer must not queue next question')}});
  const flags=vm.runInContext('activeSymptomQuestions().filter(q=>q.redFlag).map(q=>q.code)',c);
  for(const flag of flags){
   c.flag=flag;Object.assign(c.state,{chatBusy:false,chatHistory:[],chatSymptoms:[],symptomCodes:[],redFlags:[]});
   vm.runInContext('state.symIdx=activeSymptomQuestions().findIndex(q=>q.code===flag);handleSymptomAnswer(true)',c);
   assert.equal(c.state.redFlags[0],flag);assert.equal(vm.runInContext("computeTriage({redFlags:state.redFlags,cataractCode:'normal'}).level",c),'urgent');
   checked++;
  }
  assert.equal(finishes,flags.length);
 }
 assert.equal(checked,114);
});

test('12960 combinations preserve urgency, postoperative limits and remote laser screening',()=>{
 let count=0;
 for(const lang of ['ko','en','es','fr','ja','zh']){
  const c=setup('none',lang);
  for(const surgery of ['none','past','today','recent'])for(const type of ['cataract','laser','unknown'])for(const eye of ['left','right','both'])
  for(const symptomEye of ['left','right','none'])for(const photo of ['normal','risk','uncertain','skipped','postop'])for(const ams of [true,false,'unable','none']){
   c.state.riskAnswers={surgery,surgery_type:type,surgery_eye:eye,surgery_sym_eye:symptomEye};c.state.symptomAnswers={post_followup:true};
   c.state.aiResultCode=photo;c.state.aiResultData={code:photo,probability:90};c.state.amslerResult=ams==='none'?{}:{left:ams,right:false};c.state.hasAmsler=ams===true;
   c.ctx={cataractCode:photo,amslerAbnormal:ams===true,redFlags:['rf_sudden']};
   assert.equal(vm.runInContext('computeTriage(ctx).level',c),'urgent');
   c.ctx.redFlags=[];
   const tri=vm.runInContext('computeTriage(ctx)',c);
   if(ams===true)assert.equal(tri.level,'now');
   if(['today','recent'].includes(surgery)&&ams!==true)assert.equal(tri.level,'monitor');
   if(surgery==='past'&&type==='laser'&&photo==='risk')assert.equal(tri.level,'now');
   if(surgery==='past'&&type==='cataract')assert.equal(vm.runInContext("effectiveCataractCode()",c),photo==='postop'?'postop':'excluded');
   assert.ok(vm.runInContext('formatCataractResult().length',c)<=200);
   assert.ok(vm.runInContext('formatAmslerResult().length',c)<=100);
   count++;
  }
 }
 assert.equal(count,12960);
});
