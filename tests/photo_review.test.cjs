const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
function setup(){
 const nodes=Object.fromEntries(['photo-review','photo-review-image','photo-review-confirm','photo-review-retake'].map(id=>[id,{disabled:false,removeAttribute(){},focus(){},showModal(){this.open=true},close(){this.open=false}}]));
 const revoked=[], errors=[];
 const c=vm.createContext({translations:Object.fromEntries(['ko','en','es','fr','ja','zh'].map(l=>[l,{}])),document:{getElementById:id=>nodes[id]},URL:{createObjectURL:()=> 'blob:fixture',revokeObjectURL:u=>revoked.push(u)},showUploadError:e=>errors.push(e),uploadErrorMessage:e=>e.code});
 vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/app-photo-review.js'),'utf8'),c);
 return {nodes,revoked,errors,run:s=>vm.runInContext(s,c)};
}
test('photo confirmation waits for decoding and cancels without approval',async()=>{
 const x=setup(),p=x.run('reviewPhoto({})');
 assert.equal(x.nodes['photo-review-confirm'].disabled,true);
 x.nodes['photo-review-retake'].onclick();assert.equal(await p,false);
 assert.equal(x.revoked.length,1);assert.equal(x.nodes['photo-review'].open,false);
});
test('photo confirmation accepts decoded image and releases blob',async()=>{
 const x=setup(),p=x.run('reviewPhoto({})');
 x.nodes['photo-review-image'].onload();x.nodes['photo-review-confirm'].onclick();
 assert.equal(await p,true);assert.equal(x.revoked.length,1);
});
test('new photo, navigation cancellation and decode failures settle old previews',async()=>{
 const x=setup(),old=x.run('reviewPhoto({})'),next=x.run('reviewPhoto({})');
 assert.equal(await old,false);x.run('cancelPhotoReview()');assert.equal(await next,false);
 const broken=x.run('reviewPhoto({})');x.nodes['photo-review-image'].onerror();
 assert.equal(await broken,false);assert.deepEqual(x.errors,['IMAGE_INVALID']);
});
