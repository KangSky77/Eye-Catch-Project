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

test('증상 문항에서 모르겠어요는 위험 신호로 세지 않는다',()=>{
 // handleSymptomAnswer의 판정식이 엄격 비교여야 'unknown'이 어느 쪽에도 걸리지 않는다.
 const src=fs.readFileSync(path.join(__dirname,'../static/app-chat.js'),'utf8');
 const fn=src.slice(src.indexOf('function handleSymptomAnswer'));
 assert.match(fn,/q\.invert \? \(yes === false\) : \(yes === true\)/,
  '느슨한 비교로 바뀌면 모른다가 위험 신호로 세어진다');
});
