// 執行：node F3/wood-bridge.glue.test.cjs
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync(__dirname+'/wood-bridge.html','utf8').match(/<script id="bridge-model">([\s\S]*?)<\/script>/)[1];
const B=new Function(source+';return Bridge;')();
const add=(d,a,b)=>assert.equal(B.addBar(d,a,b,true),'');
for(const [a,b] of [[{x:10,y:4},{x:10,y:7}],[{x:8,y:4},{x:8,y:7}],[{x:8,y:2},{x:8,y:6}],[{x:10,y:4},{x:13,y:4}]]) {
  const d=B.empty();add(d,{x:6,y:4},{x:10,y:4});add(d,a,b);
  assert.equal(d.joints.length,1,'端點、T 字、交叉和共線接觸均自動膠合');
  assert.equal(d.joints[0].kind,'glue');assert.equal(d.joints[0].links.length,1);
  assert.ok(Number.isFinite(d.joints[0].angle));
  const sim=B.simulate(d);
  assert.equal(sim.constraints.filter(c=>c.kind==='angle' && c.compliance===0).length,1,'膠合必須加入相對角度約束');
  const before=JSON.stringify(d);assert.ok(B.addBar(d,b,a,true),'仍拒絕重複木桿');assert.equal(JSON.stringify(d),before);
}
const moved=B.empty();add(moved,{x:6,y:4},{x:10,y:4});add(moved,{x:8,y:6},{x:8,y:7});
assert.equal(B.moveNode(moved,2,{x:8,y:4},true),'');
assert.equal(moved.joints[0].kind,'glue','拖動至桿身也自動膠合');
moved.joints=[];add(moved,{x:14,y:3},{x:16,y:3});
assert.equal(B.moveNode(moved,5,{x:16,y:3.5},true),'');
assert.equal(moved.joints.length,0,'在別處新增或修改不重新黏上已解除的接點');

const zeroG=new Function(source.replace('9.81/UNIT*dt*dt','0')+';return Bridge;')();
const elbow=B.empty();add(elbow,{x:6,y:4},{x:10,y:4});add(elbow,{x:10,y:4},{x:10,y:7});
assert.notEqual(elbow.bars[0].b,elbow.bars[1].a,'接觸端點保持獨立，解除膠合後可以分離');
for(const glued of [true,false]) {
  const d=B.clone(elbow);if(!glued) d.joints[0].kind='pin';
  const sim=zeroG.simulate(d),first=sim.bars[0],second=sim.bars[1];
  first.path.forEach(i=>sim.nodes[i].baseMass=Infinity);
  for(const i of second.path) {const n=sim.nodes[i],x=n.x-10,y=n.y-4;n.x=10+x*Math.cos(.01)-y*Math.sin(.01);n.y=4+x*Math.sin(.01)+y*Math.cos(.01);}
  for(let i=0;i<12;i++) zeroG.step(sim);
  assert.ok(!sim.firstBreak && !sim.unstable);
  const [a,b]=second.path.slice(0,2).map(i=>sim.nodes[i]);
  const rotation=Math.atan2(b.y-a.y,b.x-a.x)-Math.PI/2;
  assert.ok(glued?Math.abs(rotation)<1e-6:Math.abs(rotation-.01)<1e-6,'膠合抵抗接點轉動，普通接合容許轉動');
}
const released=B.clone(elbow);released.joints=[];
const free=zeroG.simulate(released);free.bars[1].path.forEach(i=>free.nodes[i].vx=1);
zeroG.step(free);
assert.ok(free.nodes[free.bars[1].a].x>free.nodes[free.bars[0].b].x,'解除後木桿真正分離');

const hub=B.empty();
for(let i=0;i<16;i++) {const a=Math.PI*i/16,x=Math.cos(a),y=Math.sin(a);add(hub,{x:12-x,y:4-y},{x:12+x,y:4+y});}
assert.equal(hub.joints.length,15,'同點多桿只需一條膠合鏈，避免兩兩重複');
B.removeBar(hub,7);assert.equal(hub.joints.length,14);
assert.ok(hub.joints.every(j=>j.kind==='glue' && Number.isFinite(j.angle)),'移走其中一桿後保留其餘膠合角度');
const floating=zeroG.simulate(hub);for(let i=0;i<12;i++) zeroG.step(floating);
assert.ok(!floating.firstBreak && floating.nodes.every(n=>Math.hypot(n.vx,n.vy)<1e-5),'膠合鏈不產生假力或假斷裂');

const sample=B.sample(true);assert.ok(sample.joints.every(j=>j.kind==='glue'),'介面範例橋也採用膠合');
for(const load of [2,20]) {
  const d=B.clone(sample);d.nodes.find(n=>n.load).load=load;
  const sim=B.simulate(d);
  for(let i=0;i<(load===20?4:1)/B.DT;i++) B.step(sim);
  assert.ok(!sim.unstable && sim.nodes.every(n=>[n.x,n.y,n.vx,n.vy].every(Number.isFinite)),'膠合範例受載及斷裂保持有限解');
  assert.equal(!!sim.firstBreak,load===20);
}
console.log('通過：自動膠合、固定角度、端點／桿身／交叉、拖動、解除、刪除及膠合範例受載。');
