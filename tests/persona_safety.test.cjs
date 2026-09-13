const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
function setup(surgery='none',lang='ko'){
 const c=vm.createContext({state:{lang,riskAnswers:{surgery},symptomAnswers:{},amslerResult:{},chatSymptoms:[]},window:{addEventListener(){}},console});
 for(const f of ['data.js','app-safety-copy.js','app-report-text.js','app-surgery.js','app-chat.js','app-assess.js','app-findings.js','app-report.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',f),'utf8'),c);
 const core=fs.readFileSync(path.join(__dirname,'../static/app-core.js'),'utf8');
 vm.runInContext(core.slice(core.indexOf('function formatCataractResult()'),core.indexOf('const ERROR_MARKER')),c);
 return c;
}
// 리포트 한 화면이 스스로 모순되지 않는가. 제목·값·검사 요약 해석·권장 조치는 서로
// 다른 함수가 만들기 때문에, 한쪽만 고치면 조용히 어긋난다(실제로 그렇게 어긋나 있었다).
test('the report never contradicts or repeats itself across 1728 combinations',()=>{
 const VERDICT=['risk','borderline','uncertain','normal'];
 let n=0;
 for(const lang of ['ko','en','es','fr','ja','zh']){
  const c=setup('none',lang);
  for(const surgery of ['none','past','today','recent'])for(const type of ['cataract','laser','other','unknown'])
  for(const code of [...VERDICT,'skipped','postop'])for(const ams of [true,false,'unable']){
   Object.assign(c.state,{riskAnswers:{surgery,surgery_type:type,surgery_eye:'left',surgery_sym_eye:'left',age:'60s'},
    symptomAnswers:{post_followup:true},aiResultCode:code,aiResultData:VERDICT.includes(code)?{code,probability:80}:null,
    amslerResult:{left:ams,right:false},hasAmsler:ams===true,chatSymptoms:[],symptomCodes:[],redFlags:[],symptomScore:0});
   const t=vm.runInContext("(()=>{const x=translations[state.lang];return{post_limit:x.post_limit,photo_skipped:x.photo_skipped,photo_history_limit:x.photo_history_limit,find_cat_risk:x.find_cat_risk,find_cat_borderline:x.find_cat_borderline,find_cat_uncertain:x.find_cat_uncertain,find_cat_normal:x.find_cat_normal}})()",c);
   const value=vm.runInContext('formatCataractResult()',c);
   const findings=vm.runInContext('buildFindings()',c);
   const tri=vm.runInContext("computeTriage({cataractCode:state.aiResultCode,amslerAbnormal:state.hasAmsler,symptomCodes:[],redFlags:[]})",c);
   const id=[lang,surgery,type,code,ams].join('|');
   const noVerdict=[t.post_limit,t.photo_skipped,t.photo_history_limit].includes(value);
   // 판독을 쓰지 않았다고 말했으면 백내장 소견을 함께 내면 안 된다.
   if(noVerdict)assert.ok(!findings.some(x=>[t.find_cat_risk,t.find_cat_borderline,t.find_cat_uncertain,t.find_cat_normal].includes(x)),id);
   // 값이 대시 하나로 비면 '이상 없음'으로 읽힌다.
   assert.notEqual(value,'-',id);
   // 사진을 한 장도 받지 않은 회차를 '인공수정체라서 제외'라고 설명하면 안 된다.
   if(!VERDICT.includes(code))assert.notEqual(value,t.photo_history_limit,id);
   // 판독을 쓰지 않은 사실은 검사 요약 해석에도 있어야 하고, 딱 한 번만 있어야 한다.
   if(noVerdict)assert.ok(findings.includes(value),id);
   assert.equal(findings.filter(x=>[t.photo_history_limit,t.photo_skipped,t.post_limit].includes(x)).length,noVerdict?1:0,id);
   assert.equal(new Set(findings).size,findings.length,id);
   // 권장 조치 카드 안에서 같은 문장을 두 번 찍지 않는다.
   assert.ok(!tri.note||tri.note!==tri.why,id);
   n++;
  }
 }
 assert.equal(n,1728);
});

// 진행률 분모는 줄어들기만 해야 한다 — 늘어나면 끝이 멀어지는 느낌을 준다.
test('the questionnaire progress total never grows mid-survey',()=>{
 for(const answer of ['none','past','today','recent']){
  const c=setup('none');
  Object.assign(c.state,{riskAnswers:{},riskIdx:0,symIdx:0,symptomAnswers:{},maxDynamic:2});
  const before=Number(vm.runInContext('surveyProgress()',c).split('/')[1]);
  c.state.riskAnswers.surgery=answer;c.state.riskIdx=1;
  const after=Number(vm.runInContext('surveyProgress()',c).split('/')[1]);
  assert.ok(after<=before,`${answer}: ${before} -> ${after}`);
 }
});

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

// 홈 → '수술 후 상태 확인하기' → '4주보다 이전'. 사진은 한 장도 올리지 않은 경로다.
// 'postop' 표식이 남아 있으면 (1) 없는 사진을 두고 '인공수정체라서 판독 제외'라 말하고
// (2) effectiveCataractCode()가 'postop'을 내보내 서버가 술후 전용 프롬프트를 골라
// 12년 전 라식에게 '퇴원 지침을 따르세요'가 나간다(llm.py의 postop 분기).
test('the postoperative entry drops its marker when surgery turns out not to be recent',()=>{
 for(const lang of ['ko','en','es','fr','ja','zh'])for(const type of ['cataract','laser','other','unknown']){
  const c=setup('none',lang);
  Object.assign(c,{addMsg(){},setTimeout(){},resetScreeningState(){throw Error("'past'는 처음 화면으로 돌려보내면 안 된다")},nextStep(){}});
  Object.assign(c.state,{aiResultCode:'postop',aiResultData:null,riskAnswers:{},chatHistory:[],riskIdx:0,chatBusy:false,amslerResult:{}});
  vm.runInContext("handleAnswer('past','4주보다 이전')",c);
  c.state.riskAnswers.surgery_type=type;
  assert.equal(c.state.aiResultCode,'skipped');
  assert.equal(vm.runInContext('effectiveCataractCode()',c),'skipped');
  assert.equal(vm.runInContext('photoAssessmentExcluded()',c),false);
  const shown=vm.runInContext('formatCataractResult()',c);
  assert.equal(shown,vm.runInContext('translations[state.lang].photo_skipped',c));
  assert.ok(!shown.includes(vm.runInContext('translations[state.lang].photo_history_limit',c)));
  // 일반 검진 문항은 그대로 받아야 한다 — 오래된 수술 한 번으로 스크리닝이 사라지면 안 된다.
  assert.ok(vm.runInContext("activeRiskQuestions().some(q=>q.code==='diabetes')",c));
  assert.ok(vm.runInContext("activeSymptomQuestions().some(q=>q.code==='cat_glare')",c));
 }
});

// 한쪽 눈만 수술한 사람의 반대쪽(수술하지 않은) 눈은 판독을 살린다.
// 좌우 라벨(eyes[].side)은 사진 x좌표 기준이라 해부학적 좌우가 아니다 — 셀카는 거울상이다.
// 그래서 '두 눈 판정이 일치할 때만 살린다'는 좌우 무관 규칙을 쓴다.
function twoEyes(c, codeA, codeB, probability = 90) {
 c.state.aiResultCode = codeA === codeB ? codeA : 'risk';
 c.state.aiResultData = {code: c.state.aiResultCode, probability, twoEyes: true,
  eyes: [{side: 'left', probability, code: codeA}, {side: 'right', probability, code: codeB}]};
}
test('one operated eye keeps the fellow eye reading only when both eyes agree',()=>{
 for(const lang of ['ko','en','es','fr','ja','zh'])for(const [type,lensHistory] of [['cataract',undefined],['unknown','yes']])
 for(const verdict of ['risk','borderline','uncertain','normal']){
  const c=setup('past',lang);c.state.riskAnswers.surgery_type=type;
  if(lensHistory)c.state.riskAnswers.surgery_lens_history=lensHistory;
  // 두 눈 판정이 일치 + 한쪽만 수술 → 판독을 그대로 쓴다.
  twoEyes(c,verdict,verdict);c.state.riskAnswers.surgery_both='one';
  assert.equal(vm.runInContext('fellowEyeAssessable()',c),true);
  assert.equal(vm.runInContext('photoAssessmentExcluded()',c),false);
  assert.equal(vm.runInContext('effectiveCataractCode()',c),verdict);
  const shown=vm.runInContext('formatCataractResult()',c);
  assert.ok(shown.includes(vm.runInContext('translations[state.lang].photo_fellow_only',c)),lang);
  // 좌우 라벨을 신뢰하지 않는다 — '왼쪽/오른쪽 눈'별 점수를 붙이면 안 된다.
  assert.ok(!shown.includes(vm.runInContext('translations[state.lang].eye_left',c)),lang);
  assert.ok(!shown.includes('90/100'),lang);
  assert.ok(shown.length<=200);
  const findings=vm.runInContext('buildFindings()',c);
  assert.ok(findings.includes(vm.runInContext('translations[state.lang].find_cat_fellow',c)),lang);
  assert.ok(!findings.includes(vm.runInContext('translations[state.lang].photo_history_limit',c)),lang);
  // risk면 진료 시점이 실제로 올라가야 한다 — 이 기능의 요점이다.
  if(verdict==='risk')assert.equal(vm.runInContext("computeTriage({cataractCode:state.aiResultCode,redFlags:[]}).level",c),'now');

  // 양쪽 모두 수술 / 모르겠음 → 살릴 눈이 없다.
  for(const scope of ['both','unknown',undefined]){
   c.state.riskAnswers.surgery_both=scope;
   assert.equal(vm.runInContext('fellowEyeAssessable()',c),false,`${lang}/${scope}`);
   assert.equal(vm.runInContext('photoAssessmentExcluded()',c),true,`${lang}/${scope}`);
   assert.equal(vm.runInContext('effectiveCataractCode()',c),'excluded');
  }
 }
});
test('fellow-eye result does not expose the operated-eye maximum score',()=>{
 const c=setup('past','ko');
 c.state.riskAnswers.surgery_type='cataract';c.state.riskAnswers.surgery_both='one';
 c.state.aiResultCode='risk';
 c.state.aiResultData={code:'risk',probability:99,twoEyes:true,
  eyes:[{side:'left',probability:99,code:'risk'},{side:'right',probability:51,code:'risk'}]};
 const shown=vm.runInContext('formatCataractResult()',c);
 assert.ok(shown.includes(vm.runInContext('translations[state.lang].photo_fellow_only',c)));
 assert.ok(!shown.includes('99/100'));
});
test('a fellow-eye reading is refused when the two eyes disagree or only one eye was photographed',()=>{
 const c=setup('past');c.state.riskAnswers.surgery_type='cataract';c.state.riskAnswers.surgery_both='one';
 // 판정이 갈리면 위험 신호가 인공수정체 때문인지 진짜 혼탁인지 구분할 수 없다.
 twoEyes(c,'risk','normal');
 assert.equal(vm.runInContext('bothEyesAgree()',c),false);
 assert.equal(vm.runInContext('photoAssessmentExcluded()',c),true);
 assert.equal(vm.runInContext("activeRiskQuestions().some(q=>q.code==='surgery_both')",c),false,'답이 판정을 못 바꾸면 묻지 않는다');
 // 단안 클로즈업은 어느 눈을 찍었는지 알 수 없다.
 c.state.aiResultCode='risk';
 c.state.aiResultData={code:'risk',probability:90,twoEyes:false,eyes:[{side:'single',probability:90,code:'risk'}]};
 assert.equal(vm.runInContext('bothEyesAgree()',c),false);
 assert.equal(vm.runInContext('photoAssessmentExcluded()',c),true);
 // 라식 등 인공수정체가 아닌 이력은 애초에 제외 대상이 아니므로 이 문항을 묻지 않는다.
 twoEyes(c,'risk','risk');c.state.riskAnswers.surgery_type='laser';c.state.riskAnswers.surgery_lens_history='no';
 assert.equal(vm.runInContext("activeRiskQuestions().some(q=>q.code==='surgery_both')",c),false);
 assert.equal(vm.runInContext('photoAssessmentExcluded()',c),false);
 // 4주 이내 수술은 술후 확인 경로다 — 반대쪽 눈 판독을 끌어오지 않는다.
 const recent=setup('today');recent.state.riskAnswers.surgery_type='cataract';recent.state.riskAnswers.surgery_both='one';
 twoEyes(recent,'risk','risk');
 assert.equal(vm.runInContext('fellowEyeAssessable()',recent),false);
 assert.equal(vm.runInContext('photoAssessmentExcluded()',recent),true);
});
test('the fellow-eye question is asked and never contradicts the asymmetry finding',()=>{
 const c=setup('past');c.state.riskAnswers.surgery_type='cataract';twoEyes(c,'risk','risk');
 assert.equal(vm.runInContext("activeRiskQuestions().map(q=>q.code).join()",c),
  'surgery,surgery_type,surgery_both,age,diabetes,hypertension,family,smoking');
 // 두 눈 판정이 같을 때만 열리는 경로이므로 '한쪽 눈만 위험'(asymmetric)과 겹칠 수 없다.
 c.state.riskAnswers.surgery_both='one';c.state.asymmetric=true;
 const findings=vm.runInContext('buildFindings()',c);
 assert.ok(vm.runInContext("state.aiResultData.eyes[0].code===state.aiResultData.eyes[1].code",c));
 assert.ok(findings.includes(vm.runInContext('translations.ko.find_cat_fellow',c)));
});

// 'past'에서 수술한 쪽(surgery_eye)은 소견서·리포트·판정 어디에도 쓰이지 않는다.
test('remote surgery history asks only the question that changes the outcome',()=>{
 const c=setup('past');
 const asked=vm.runInContext('activeRiskQuestions().map(q=>q.code)',c);
 assert.ok(asked.includes('surgery_type'));
 assert.ok(!asked.includes('surgery_lens_history'));
 assert.ok(!asked.includes('surgery_eye'));
 assert.ok(!asked.includes('surgery_sym_eye'));
 c.state.riskAnswers.surgery_type='other';
 const otherAsked=vm.runInContext('activeRiskQuestions().map(q=>q.code)',c);
 assert.ok(otherAsked.includes('surgery_lens_history'));
 c.state.riskAnswers.surgery_lens_history='yes';
 assert.ok(vm.runInContext('buildFindings()',c).some(item=>item.includes(vm.runInContext('translations[state.lang].find_remote_context',c).split('{items}')[0])));
 assert.ok(vm.runInContext('buildOpinionSymptoms()',c).some(item=>item.includes('Reported remote surgery')));
 // 답 라벨만 나열하면('… · 없어요') 무엇에 대한 답인지 알 수 없다 — 항목 이름이 붙어야 한다.
 for(const lang of ['ko','en','es','fr','ja','zh']){
  c.state.lang=lang;c.state.riskAnswers={surgery:'past',surgery_type:'laser',surgery_lens_history:'no'};
  const t=vm.runInContext('translations[state.lang]',c);
  const line=vm.runInContext('buildFindings()',c).find(item=>item.startsWith(t.find_remote_context.split('{items}')[0]));
  assert.ok(line.includes(t.remote_lens_label+': '+t.surgery_lens_history_no),lang);
  assert.ok(line.includes(t.remote_type_label+': '+t.surgery_type_laser),lang);
  assert.ok(vm.runInContext('buildOpinionSymptoms()',c).includes('Reported remote surgery: '+t.remote_lens_label+': '+t.surgery_lens_history_no),lang);
 }
 c.state.lang='ko';
 // 4주 이내는 세 문항 모두 리포트의 '확인된 수술 정보'에 실리므로 그대로 묻는다.
 const recent=setup('today');
 assert.equal(vm.runInContext("activeRiskQuestions().map(q=>q.code).join()",recent),
  'surgery,surgery_type,surgery_eye,surgery_sym_eye');
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
   c.state.riskAnswers={surgery,surgery_type:type,surgery_eye:eye,surgery_sym_eye:symptomEye};
   if(surgery==='past' && type!=='cataract') c.state.riskAnswers.surgery_lens_history=type==='laser'?'no':'unknown';
   c.state.symptomAnswers={post_followup:true};
   c.state.aiResultCode=photo;c.state.aiResultData={code:photo,probability:90};c.state.amslerResult=ams==='none'?{}:{left:ams,right:false};c.state.hasAmsler=ams===true;
   c.ctx={cataractCode:photo,amslerAbnormal:ams===true,redFlags:['rf_sudden']};
   assert.equal(vm.runInContext('computeTriage(ctx).level',c),'urgent');
   c.ctx.redFlags=[];
   const tri=vm.runInContext('computeTriage(ctx)',c);
   if(ams===true)assert.equal(tri.level,'now');
   if(['today','recent'].includes(surgery)&&ams!==true)assert.equal(tri.level,'monitor');
   if(surgery==='past'&&type==='laser'&&photo==='risk')assert.equal(tri.level,'now');
   // '제외'는 버릴 판독이 실제로 있을 때만 성립한다. 사진을 한 장도 받지 않은 회차
   // ('skipped'·'postop')까지 제외로 묶으면 올린 적 없는 사진을 설명하게 된다.
   if(surgery==='past'&&type==='cataract')assert.equal(vm.runInContext("effectiveCataractCode()",c),
    photo==='postop'?'postop':photo==='skipped'?'skipped':'excluded');
   if(photo==='skipped'&&!['today','recent'].includes(surgery)){
    assert.equal(vm.runInContext('photoAssessmentExcluded()',c),false);
    assert.equal(vm.runInContext('formatCataractResult()',c),vm.runInContext('translations[state.lang].photo_skipped',c));
    assert.ok(vm.runInContext('buildFindings().includes(translations[state.lang].photo_skipped)',c));
   }
   // 권장 조치 카드 안에서 같은 문장을 두 번 찍지 않는다.
   assert.ok(!tri.note||tri.note!==tri.why);
   assert.ok(vm.runInContext('formatCataractResult().length',c)<=200);
   assert.ok(vm.runInContext('formatAmslerResult().length',c)<=100);
   count++;
  }
 }
 assert.equal(count,12960);
});
