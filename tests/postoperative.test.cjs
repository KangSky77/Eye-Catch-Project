const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
test('all six languages cover postoperative copy and granular younger ages',()=>{
 const c=setup('none');
 const result=vm.runInContext(`Object.keys(translations).map(lang=>({lang,
  missing:Object.keys(surgeryCopy.en).filter(key=>!translations[lang][key]),
  limit:translations[lang].post_limit.length,
  ages:riskQuestions.find(q=>q.code==='age').options.map(o=>({value:o.v,label:translations[lang][o.key],score:o.score}))
 }))`,c);
 assert.equal(result.length,6);
 for(const r of result){
  assert.equal(r.missing.length,0,r.lang);
  assert.ok(r.limit<=200,r.lang);
  assert.deepEqual(Array.from(r.ages.slice(0,4),a=>a.value),['under10','10s','20s','30s']);
  assert.ok(r.ages.every(a=>a.label),r.lang);
  assert.ok(r.ages.slice(0,4).every(a=>a.score===0));
 }
});
function setup(surgery) {
 const c=vm.createContext({state:{lang:'ko',riskAnswers:{surgery},symptomAnswers:{}},window:{addEventListener(){}},console});
 for(const file of ['data.js','app-report-text.js','app-safety-copy.js','app-surgery.js','app-chat.js','app-assess.js'])
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../static',file),'utf8'),c);
 return c;
}
test('recent surgery uses dedicated questions without duplicate cataract glare',()=>{
 for(const timing of ['today','recent']) {
  const c=setup(timing);
  const codes=vm.runInContext('activeSymptomQuestions().map(q=>q.code)',c);
  assert.ok(codes.includes('post_glare'));
  assert.ok(!codes.includes('cat_glare'));
  assert.equal(vm.runInContext('activeRiskQuestions().length',c),4);
  for(const code of codes) assert.ok(vm.runInContext('translations.ko.sym_'+code,c));
 }
 const c=setup('none');
 assert.ok(vm.runInContext("activeSymptomQuestions().some(q=>q.code==='cat_glare')",c));
});

test('old surgery history keeps the full screening and only adds red flags',()=>{
 // 10년 전 라식 한 번으로 백내장 스크리닝이 통째로 사라지면 안 된다.
 // 나이·당뇨·가족력 배점과 급성 녹내장 적신호가 살아 있어야 한다.
 const past=setup('past'), none=setup('none');
 const risk=c=>vm.runInContext("activeRiskQuestions().map(q=>q.code).join(',')",c);
 const sym=c=>vm.runInContext('activeSymptomQuestions().map(q=>q.code)',c);
 assert.ok(risk(none).split(',').every(code=>risk(past).split(',').includes(code)),'일반 위험요인 문진은 유지돼야 한다');
 for(const code of ['rf_acute','rf_sudden','cat_glare','gla_field','chk_recent'])
  assert.ok(sym(past).includes(code),code+' 문항이 사라졌다');
 // 술후 적신호는 일반 문진에 없는 것만 얹는다. 나머지는 이름만 '수술 후'일 뿐 같은 질문이다:
 //   통증 → rf_pain(4주 초과에서는 q_remote_pain 문구) / 갑작스러운 시력저하 → rf_sudden
 //   서서히 흐려짐 → cat_foggy / 눈부심 → cat_glare
 for(const code of ['rf_pain','rf_sudden','cat_foggy','surgery_redness'])
  assert.ok(sym(past).includes(code),code+' 문항이 없다');
 for(const code of ['surgery_pain','surgery_vision','surgery_glare'])
  assert.ok(!sym(past).includes(code),code+'를 두 번 묻고 있다');
 // 리포트에 i18n 키가 그대로 노출되지 않도록 라벨이 6개 언어에 다 있어야 한다
 for(const lang of vm.runInContext('Object.keys(translations)',past))
  for(const code of ['surgery_pain','surgery_vision','surgery_redness'])
   assert.ok(vm.runInContext(`translations.${lang}.sym_${code}`,past),lang+'/'+code);
 // 트리아지도 일반 판정을 그대로 쓴다
 const tri=vm.runInContext("computeTriage({cataractCode:'risk',amslerAbnormal:true,riskScore:11,symptomCodes:['cataract'],redFlags:[]})",past);
 assert.equal(tri.label,vm.runInContext("computeTriage({cataractCode:'risk',amslerAbnormal:true,riskScore:11,symptomCodes:['cataract'],redFlags:[]})",none).label);
});
test('postoperative advice distinguishes stable symptoms, changes and emergency signs',()=>{
 const c=setup('recent');
 c.state.symptomAnswers={post_glare:true,post_worse:false,post_followup:true};
 const run=flags=>{c.flags=flags;return vm.runInContext("computeTriage({cataractCode:'postop',redFlags:flags})",c)};
 assert.equal(run([]).level,'monitor');
 c.state.symptomAnswers.post_worse=true;
 assert.equal(run([]).level,'now');
 for(const code of ['post_pain','post_vision','post_redness','post_flashes']) assert.equal(run([code]).level,'urgent');
});

test('same-day surgery is not asked about progress, so normal glare stays monitor',()=>{
 // 실사용 제보: 오늘 수술한 사람은 눈부심이 당연히 있는데 '병원에 문의하세요'가 떴다.
 // 옛 q_post_change가 '수술 전에는 없었나'(당일엔 항상 참) + '좋아지지 않나'를 한 문장에
 // 묶어놨던 탓이다. 좋아질 시간이 없었던 당일에는 경과를 묻지 않는다.
 //
 // 당일인지는 시작 화면의 시기 선택지가 아니라 술후 문진 첫 문항(post_day1)이 묻는다 —
 // '오늘'과 '최근 4주 이내'는 서로 배타적이지 않아 선택지로 둘 수 없었다(오늘도 4주 이내다).
 const today=setup('recent'), recent=setup('recent');
 const codes=c=>vm.runInContext('activeSymptomQuestions().map(q=>q.code)',c);
 assert.ok(codes(today).includes('post_day1'),'수술 당일 여부를 묻지 않는다');
 assert.equal(vm.runInContext('activeSymptomQuestions()[0].code',today),'post_day1','경과 문항보다 먼저 물어야 한다');
 today.state.symptomAnswers={post_day1:false};     // 아니오 = 아직 수술 당일
 recent.state.symptomAnswers={post_day1:true};
 assert.ok(!codes(today).includes('post_worse'),'수술 당일에 경과를 묻고 있다');
 assert.ok(codes(recent).includes('post_worse'),'하루가 지났으면 경과를 물어야 한다');
 assert.ok(codes(today).includes('post_glare'));

 // 통증·시력저하·충혈 없이 눈부심만 있는 당일 환자 → 예정된 진료를 따르라는 안내
 today.state.symptomAnswers={post_day1:false,post_pain:false,post_vision:false,post_redness:false,
  post_flashes:false,post_glare:true,post_followup:true};
 const tri=vm.runInContext("computeTriage({cataractCode:'postop',redFlags:[]})",today);
 assert.equal(tri.level,'monitor');
 // 적신호가 있으면 당일이라도 그대로 응급이다
 assert.equal(vm.runInContext("computeTriage({cataractCode:'postop',redFlags:['post_pain']})",today).level,'urgent');
});

test('postoperative triage ignores a stale photo risk result',()=>{
 const c=setup('today');
 c.state.symptomAnswers={post_glare:true,post_followup:true};
 const tri=vm.runInContext("computeTriage({cataractCode:'risk',redFlags:[]})",c);
 assert.equal(tri.level,'monitor');
});

test('postoperative advice preserves abnormal Amsler across languages and surgery timings',()=>{
 for(const timing of ['today','recent']) for(const lang of ['ko','en','es','fr','ja','zh']) {
  const c=setup(timing); c.state.lang=lang;
  c.state.symptomAnswers={post_glare:true,post_followup:true};
  for(const photo of ['normal','risk','uncertain','postop']) {
   c.photo=photo;
   assert.equal(vm.runInContext('computeTriage({cataractCode:photo,amslerAbnormal:true,redFlags:[]}).level',c),'now');
   assert.equal(vm.runInContext("computeTriage({cataractCode:photo,amslerAbnormal:true,redFlags:['post_pain']}).level",c),'urgent');
  }
 }
});

test('the photo verdict follows the lens, not the fact of surgery',()=>{
 // 왜 '수술 여부'가 아니라 '수정체'인가: 모델은 자연 수정체로 학습했다. 인공수정체가
 // 들어간 눈에서는 판독이 뒤집히지만(2026-09-13 실측), 라식·라섹은 각막만 깎으므로
 // 판독 근거가 그대로 남는다. 예전에는 수술 이력 하나로 전부 막아, 12년 전 라식을 받은
 // 사람의 백내장 스크리닝까지 사라졌다.
 const core=fs.readFileSync(path.join(__dirname,'../static/app-core.js'),'utf8');
 const fn=core.slice(core.indexOf('function formatCataractResult()'),
                     core.indexOf('function amslerComplete()'));
 const cases=[
  // [수술 시기, 수술 종류, 인공수정체 이력, 판정을 보여주는가]
  ['none',  undefined,  undefined, true],
  ['today', 'cataract', undefined, false],   // 인공수정체 → 판독 버림
  ['recent','cataract', undefined, false],
  ['past',  'cataract', undefined, false],
  ['today', 'laser',    'no',      true],    // 수정체 그대로 → 판독 유지
  ['recent','laser',    'no',      true],
  ['past',  'laser',    'no',      true],
  ['today', 'laser',    undefined, false],   // 아직 안 물었다 → 확정 전에는 보여주지 않는다
  ['today', 'unknown',  'unknown', false],   // 모르면 버린다
  ['recent','other',    'no',      true],    // 망막·녹내장이라도 인공수정체가 없으면 판독한다
 ];
 for(const [surgery,type,lens,expectVerdict] of cases){
  const c=setup(surgery);
  vm.runInContext(fn,c);
  c.state.riskAnswers={surgery,surgery_type:type,surgery_lens_history:lens};
  c.state.aiResultCode='risk';
  c.state.aiResultData={code:'risk',probability:87,twoEyes:false};
  const shown=vm.runInContext('formatCataractResult()',c);
  const t=vm.runInContext('translations[state.lang]',c);
  const label=`${surgery}/${type}/${lens} → ${shown}`;
  assert.equal(shown.includes(t.ai_risk),expectVerdict,label);
  assert.equal(vm.runInContext('photoAssessmentExcluded()',c),!expectVerdict,label);
  // 버릴 때는 '수술해서'가 아니라 '수정체를 바꿔서'라고 이유를 말해야 한다(교수 질문).
  if(!expectVerdict) assert.equal(shown,t.photo_history_limit,label);
 }
});

test('사진을 한 장도 받지 않은 회차는 판독 제외가 아니라 판독 없음이다',()=>{
 const core=fs.readFileSync(path.join(__dirname,'../static/app-core.js'),'utf8');
 const fn=core.slice(core.indexOf('function formatCataractResult()'),
                     core.indexOf('function amslerComplete()'));
 const c=setup('today');
 vm.runInContext(fn,c);
 c.state.riskAnswers={surgery:'today',surgery_type:'cataract'};
 c.state.aiResultCode='postop';c.state.aiResultData=null;
 assert.equal(vm.runInContext('formatCataractResult()',c),vm.runInContext('translations.ko.post_limit',c));
 assert.equal(vm.runInContext('photoAssessmentExcluded()',c),false,'올린 적 없는 사진을 제외라고 말했다');
 assert.equal(vm.runInContext('effectiveCataractCode()',c),'postop');
});
