// 執行：node F3/wood-bridge.physics.test.cjs
// 解析基準：USDA Wood Handbook 第 9 章，https://research.fs.usda.gov/treesearch/62251
const assert=require('node:assert/strict');
const fs=require('node:fs');
const html=fs.readFileSync(__dirname+'/wood-bridge.html','utf8');
const source=html.match(/<script id="bridge-model">([\s\S]*?)<\/script>/)[1];
const model=code=>new Function(code+';return Bridge;')();
const B=model(source),results=[];
const close=(actual,expected,tolerance,message)=>assert.ok(Math.abs(actual/expected-1)<tolerance,`${message}：${actual}，理論 ${expected}`);
function settle(api,sim,seconds=3,dt=api.DT) {
  for(let i=0;i<Math.round(seconds/dt);i++) api.step(sim,dt);
  assert.ok(sim.nodes.every(n=>[n.x,n.y,n.vx,n.vy].every(Number.isFinite)),'求解數值有限');
  return sim;
}
function beam(api,layers=1,weight=.02,t=.5,settings={},dt=api.DT) {
  const d=api.empty();api.addBar(d,{x:7,y:8},{x:17,y:8});
  for(let i=1;i<layers;i++) assert.equal(api.reinforce(d,0),'');
  api.placeLoad(d,null,0,t,weight);
  const sim=settle(api,api.simulate(d,settings),3,dt);
  assert.equal(sim.firstBreak,null,'小載荷彈性梁不應斷裂');
  const actual=(api.barPoint(sim,0,t).y-8)*api.UNIT;
  const EI=sim.EI*layers**3,q=sim.material.density*api.AREA*layers*9.81;
  const expected=weight*9.81*t*t*(1-t)**2/(3*EI)+q*t*(1-2*t*t+t**3)/(24*EI);
  close(actual,expected,.06,`${layers} 層、載荷位置 ${t} 的下彎`);
  close(sim.nodes.reduce((sum,n)=>sum+n.baseMass,0),layers*.006**2*sim.material.density,1e-10,'質量由截面、長度及密度決定');
  const upward=-sim.contacts.filter(c=>c.contact==='normal').reduce((sum,c)=>sum+c.lambda,0)/dt**2;
  close(upward,(weight+layers*api.AREA*sim.material.density)*9.81,.02,'地面總反力等於總重量');
  results.push(`${layers} 層／位置 ${t}：${(actual*1000).toFixed(3)} mm；理論 ${(expected*1000).toFixed(3)} mm`);
  return {actual,expected,sim};
}
close(B.AREA,3.6e-5,1e-12,'截面積');close(B.INERTIA,1.08e-10,1e-12,'截面二次矩');
assert.deepEqual(B.MATERIAL,{young:2e9,density:160,tension:25e6,compression:9e6,bending:16e6},'預設採用中密度輕木參考值');
for(const [key,value] of Object.entries(B.MATERIAL)) {
  const input=html.match(new RegExp(`<input id="mat-${key}"[^>]*value="([^"]+)"`));
  assert.equal(Number(input[1])*(key==='young'?1e9:key==='density'?1:1e6),value,'介面與求解器材料預設必須相同');
}
const single=beam(B),double=beam(B,2),triple=beam(B,3);
close(single.sim.nodes.reduce((sum,n)=>sum+n.baseMass,0),.00576,1e-12,'一米 6 × 6 mm 預設輕木的質量為 5.76 g');
beam(B,1,.02,.273);beam(B,1,0);
const stiff=beam(B,1,.02,.5,{young:B.MATERIAL.young*2});close(single.actual/stiff.actual,2,.025,'彈性模數加倍使下彎減半');
close(beam(B,2,.02,.5,{},B.DT/2).actual,double.actual,.01,'時間步减半不應改變靜態剛度');
const finer=model(source.replace('2*Math.ceil(bar.length/2)','4*Math.ceil(bar.length/2)'));
const refined=beam(finer,2);
assert.ok(Math.abs(refined.actual-refined.expected)<Math.abs(double.actual-double.expected),'細分加密應接近複合梁理論值');

// 重複的硬接合不會增加實物剛度；方程線性相依也須求得相同橋形。
const original=B.sample(),redundant=B.clone(original);
redundant.joints.push(...B.clone(original.joints.filter(j=>j.kind==='pin')));
const reference=settle(B,B.simulate(original),.05),duplicated=settle(B,B.simulate(redundant),.05);
assert.equal(duplicated.firstBreak,null,'重複接合不產生假斷裂');
reference.nodes.forEach((n,i)=>assert.ok(B.distance(n,duplicated.nodes[i])*B.UNIT<1e-9,'相依硬接合的解須保持一致'));
const stock=B.empty();B.addBar(stock,{x:7,y:8},{x:17,y:8});
for(let i=1;i<20;i++) assert.equal(B.reinforce(stock,0),'');
B.placeLoad(stock,null,0,.5,2);
assert.equal(B.totalLength(stock),20);
assert.equal(settle(B,B.simulate(stock),.05).firstBreak,null,'20 m 膠合組合保持有限解，不產生假斷裂');

// 固定兩端的實驗夾具只存在此測試，產品中的岸面依然沒有固定鉸點。
// 移除重力以隔離軸向材料試驗及 Euler 挫曲；其餘使用同一求解器。
const zeroG=model(source.replace('9.81/UNIT*dt*dt','0'));
// 夾具固定所有試樣節點，隔離拉斷、壓潰與純彎曲；長桿挫曲另於下方驗證。
for(const mode of ['tension','compression','bending']) for(const ratio of [.99,1.01]) {
  const d=zeroG.empty();zeroG.addBar(d,{x:7,y:6},{x:7.5,y:6});
  const sim=zeroG.simulate(d),bar=sim.bars[0],strain=ratio*sim.material[mode]/sim.material.young;
  for(const n of sim.nodes) n.baseMass=Infinity;
  if(mode==='bending') {
    const half=bar.length*zeroG.UNIT/2,angle=strain*half/(.006/2),mid=sim.nodes[bar.path[1]];
    for(const [i,sign] of [[bar.a,-1],[bar.b,1]]) {
      sim.nodes[i].x=mid.x+sign*half*Math.cos(angle/2)/zeroG.UNIT;
      sim.nodes[i].y=mid.y+half*Math.sin(angle/2)/zeroG.UNIT;
    }
  } else for(const n of sim.nodes) n.x=7+(n.x-7)*(1+(mode==='tension'?strain:-strain));
  zeroG.step(sim);
  close(bar.stress,ratio,1e-7,`${mode} 應使用其材料強度計算失效比例`);
  assert.equal(bar.broken,ratio>1,`${mode} 超過材料強度才斷裂`);
}
const specimen=zeroG.empty();zeroG.addBar(specimen,{x:7,y:6},{x:17,y:6});
const axial=zeroG.simulate(specimen),extension=1e-5;
for(const n of axial.nodes) n.x=7+(n.x-7)*(1+extension);
axial.nodes[0].baseMass=Infinity;axial.nodes[1].baseMass=Infinity;
settle(zeroG,axial,.1);
for(const c of axial.bars[0].axial) close(-c.lambda/zeroG.DT**2,axial.EA*extension,1e-4,'軸向反力符合 EA ΔL/L');
for(const multiple of [.8,1.2]) {
  const sim=zeroG.simulate(specimen),path=sim.bars[0].path,P=Math.PI**2*sim.EI*multiple;
  for(let i=0;i<path.length;i++) {const n=sim.nodes[path[i]],t=i/(path.length-1);n.x=7+10*(1-P/sim.EA)*t;n.y=6+.00001*Math.sin(Math.PI*t);}
  sim.nodes[0].baseMass=Infinity;sim.nodes[1].baseMass=Infinity;
  settle(zeroG,sim,2);
  const bow=Math.abs(zeroG.barPoint(sim,0,.5).y-6);
  assert.ok(multiple<1?bow<.00001:bow>.001,`${multiple} 倍 Euler 臨界荷載時，初始微小彎曲應${multiple<1?'衰減':'增長'}`);
}

// 自由落體不應產生彈性應力；旋轉整個膠合組合亦不應出現假力矩。
for(const angle of [0,.7,2.4]) {
  const d=zeroG.empty();zeroG.addBar(d,{x:7,y:5},{x:15,y:5});zeroG.reinforce(d,0);
  for(const n of d.nodes) {const x=n.x-11,y=n.y-5;n.x=11+x*Math.cos(angle)-y*Math.sin(angle);n.y=5+x*Math.sin(angle)+y*Math.cos(angle);}
  const sim=settle(zeroG,zeroG.simulate(d),.1);
  assert.ok(sim.nodes.every(n=>Math.hypot(n.vx,n.vy)<1e-5),'剛體轉動不產生內力或移動');
}
const falling=B.empty();B.addBar(falling,{x:9,y:3},{x:15,y:3});
const free=settle(B,B.simulate(falling),.1);
assert.ok(free.bars[0].stress<1e-6,'共同自由落體不把重力錯算成彎曲');
assert.throws(()=>B.simulate(falling,{young:NaN}),/正數/,'拒絕無效材料數值');
console.log(results.join('\n'));
console.log('通過：輕木預設與介面一致、SI 質量、梁下彎、複合截面、非中央負重、地面反力、步長／網格收斂、拉壓彎曲斷裂閾值、軸向剛度、Euler 挫曲及剛體不變性。');
