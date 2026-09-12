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
 for(const file of ['data.js','app-report-text.js','app-surgery.js','app-chat.js','app-assess.js'])
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
 // 술후 적신호는 얹되, 눈부심은 cat_glare가 이미 물으므로 중복시키지 않는다
 for(const code of ['surgery_pain','surgery_vision','surgery_redness'])
  assert.ok(sym(past).includes(code),code+' 문항이 없다');
 assert.ok(!sym(past).includes('surgery_glare'));
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
 const today=setup('today'), recent=setup('recent');
 const codes=c=>vm.runInContext('activeSymptomQuestions().map(q=>q.code)',c);
 assert.ok(!codes(today).includes('post_worse'),'수술 당일에 경과를 묻고 있다');
 assert.ok(codes(recent).includes('post_worse'),'4주 이내에는 경과를 물어야 한다');
 assert.ok(codes(today).includes('post_glare'));

 // 통증·시력저하·충혈 없이 눈부심만 있는 당일 환자 → 예정된 진료를 따르라는 안내
 today.state.symptomAnswers={post_pain:false,post_vision:false,post_redness:false,
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

test('a photo verdict is not shown to someone who had surgery within 4 weeks',()=>{
 // 사진을 먼저 올린 뒤 문진에서 '오늘 수술했습니다'를 고른 경로에서, 백내장 수술 당일
 // 눈을 찍은 사진에 '백내장 위험'이 그대로 뜨던 구멍을 막는다.
 const core=fs.readFileSync(path.join(__dirname,'../static/app-core.js'),'utf8');
 const fn=core.slice(core.indexOf('function formatCataractResult()'),
                     core.indexOf('function amslerComplete()'));
 for(const [surgery,expectVerdict] of [['today',false],['recent',false],['past',true],['none',true]]){
  const c=setup(surgery);
  vm.runInContext(fn,c);
  c.state.aiResultCode='risk';
  c.state.aiResultData={code:'risk',score:87,twoEyes:false};
  const shown=vm.runInContext('formatCataractResult()',c);
  const limit=vm.runInContext('translations[state.lang].post_limit',c);
  assert.equal(shown!==limit,expectVerdict,surgery+' → '+shown);
 }
});
