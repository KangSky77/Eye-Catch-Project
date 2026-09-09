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
test('all surgery timings use dedicated questions without duplicate cataract glare',()=>{
 for(const timing of ['today','recent','past']) {
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
test('postoperative advice distinguishes stable symptoms, changes and emergency signs',()=>{
 const c=setup('today');
 c.state.symptomAnswers={post_glare:true,post_change:false,post_followup:true};
 const run=flags=>{c.flags=flags;return vm.runInContext("computeTriage({cataractCode:'postop',redFlags:flags})",c)};
 assert.equal(run([]).level,'monitor');
 c.state.symptomAnswers.post_change=true;
 assert.equal(run([]).level,'now');
 for(const code of ['post_pain','post_vision','post_redness','post_flashes']) assert.equal(run([code]).level,'urgent');
});
