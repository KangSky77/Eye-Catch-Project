// 탭 이동과 외부 지도 링크 — 둘 다 2026-09-17에 지적받은 곳이다.
//
//  1) 재촬영 안내창(<dialog>)은 탭과 무관한 최상위 레이어라, 탭을 옮겨도 닫아주지
//     않으면 다른 탭 위에 그대로 남는다.
//  2) '전체 지도'는 window.open으로 열었는데, 팝업이 차단되면 반환값이 null이라
//     아무 일도 일어나지 않았다. 사용자가 직접 누르는 <a>는 차단되지 않는다.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');

function slice(from,to){
 const src=fs.readFileSync(path.join(__dirname,'../static/app-core.js'),'utf8');
 const start=src.indexOf(from);assert.notEqual(start,-1,from);
 const end=to?src.indexOf(to,start):src.length;assert.notEqual(end,-1,to);
 return src.slice(start,end);
}

function setup({diseaseOpen=false}={}){
 const closed=[];
 const mapLink={href:''};
 const node={classList:{add(){},remove(){},toggle(){}},focus(){},setAttribute(){},removeAttribute(){},getAttribute:()=>null};
 const c=vm.createContext({
  state:{lang:'ko'},
  closePhotoCheck:()=>closed.push('photo-check'),
  isDiseaseModalOpen:()=>diseaseOpen,
  closeDisease:()=>closed.push('disease-modal'),
  showVisionSim(){}, ensureMap(){}, updateReportGate(){},
  window:{scrollTo(){}},
  document:{
   getElementById:id=>(id==='map-full-btn'?mapLink:node),
   querySelector:()=>node, querySelectorAll:()=>[],
  },
 });
 vm.runInContext(slice('function showTab(','// 검사 흐름의 사용자 관점 단계'),c);
 vm.runInContext(slice('function openMap()','function createAiLoader('),c);
 return {c,closed,mapLink,run:s=>vm.runInContext(s,c)};
}

test('탭을 옮기면 열려 있던 재촬영 안내창을 닫는다',()=>{
 const x=setup();
 x.run("showTab('tab-simulator')");
 assert.deepEqual(x.closed,['photo-check'],'안내창을 닫지 않아 다른 탭 위에 남는다');
});

// 질환 상세는 배경 스크롤까지 잠근다(body.modal-open). 탭을 옮겨도 남으면
// 모달이 화면을 덮는 데다 새 탭이 스크롤조차 되지 않는다.
test('탭을 옮기면 열려 있던 질환 상세 모달도 닫는다',()=>{
 const x=setup({diseaseOpen:true});
 x.run("showTab('tab-map')");
 assert.ok(x.closed.includes('disease-modal'),'질환 모달이 다른 탭 위에 남는다');
});

test('닫혀 있는 모달을 괜히 다시 닫지 않는다',()=>{
 const x=setup({diseaseOpen:false});
 x.run("showTab('tab-map')");
 assert.ok(!x.closed.includes('disease-modal'));
});

test('전체 지도는 팝업이 아니라 링크이며 주소가 언어를 따라간다',()=>{
 const x=setup();
 x.run('openMap()');
 assert.match(x.mapLink.href,/map\.kakao\.com/,'한국어는 카카오맵');
 x.run("state.lang='en'; openMap()");
 assert.match(x.mapLink.href,/google\.com\/maps/,'그 외 언어는 구글 지도');

 const html=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
 const tag=html.match(/<a[^>]*id="map-full-btn"[^>]*>/);
 assert.ok(tag,'전체 지도는 <a>여야 한다 — window.open은 팝업 차단에 막힌다');
 assert.match(tag[0],/target="_blank"/);
 assert.match(tag[0],/rel="[^"]*noopener/);
});
