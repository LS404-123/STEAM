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
assert.equal(single.sim.peakStress.bar,0);
close(single.sim.peakStress.t,.5,1e-8,'中央負重梁的最高應力位於跨中');
const peakMoment=.02*9.81/4+B.MATERIAL.density*B.AREA*9.81/8;
close(single.sim.peakStress.value,peakMoment*.003/B.INERTIA,.07,'最高應力符合梁的截面彎曲應力');
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
// 沒有空氣阻力時，不同密度／步長均須給出 g；水平平移不可被數值阻尼拖慢。
for(const dt of [B.DT,B.DT/2]) for(const density of [80,320]) {
  const sim=B.simulate(falling,{density}),duration=.2,steps=Math.round(duration/dt);
  sim.nodes.forEach(n=>n.vx=10);
  settle(B,sim,duration,dt);
  for(const n of sim.nodes) {
    close(n.vy*B.UNIT,9.81*duration,1e-9,'自由落體速度 v = gt');
    close(n.vx*B.UNIT,1,1e-9,'無水平外力時動量守恆');
    // 半隱式 Euler 的累積位置；誤差應隨 dt 減半，而非加入假的空氣阻力。
    close((n.y-3)*B.UNIT,9.81*dt*dt*steps*(steps+1)/2,1e-9,'自由落體位移符合已知積分誤差');
  }
}
const sliding=B.simulate({nodes:[{x:5,y:8,load:1}],bars:[],joints:[]});
sliding.nodes[0].vx=10;settle(B,sliding,.1);
close(sliding.nodes[0].vx*B.UNIT,1-.6*9.81*.1,1e-8,'滑動摩擦的減速度為 μg');
const cutModel=model(source.replace('return {UNIT,DT','return {cutAt(sim,index){breakBar(sim,sim.bars[index],2);rebuildConstraints(sim);},UNIT,DT'));
const splitting=cutModel.simulate(falling);
splitting.nodes.forEach(n=>{n.vx=3-(n.y-3)*2;n.vy=4+(n.x-12)*2;});
const conserved=sim=>sim.nodes.reduce((sum,n)=>{
  const m=n.baseMass+n.load;
  return [sum[0]+m,sum[1]+m*n.vx,sum[2]+m*n.vy,sum[3]+m*(n.x*n.vy-n.y*n.vx)];
},[0,0,0,0]);
const beforeCut=conserved(splitting);cutModel.cutAt(splitting,0);
conserved(splitting).forEach((value,i)=>close(value,beforeCut[i],1e-12,'切開瞬間保留質量、線動量與角動量'));
// 用真實斷橋碰撞觸發穩定處理；空中的獨立木桿仍須正常自由落體。
const independent=B.sample();independent.nodes.find(n=>n.load).load=20;
assert.equal(B.addBar(independent,{x:10,y:2},{x:14,y:2}),'');
const separate=B.simulate(independent),probe=separate.bars.at(-1);
probe.path.forEach(i=>separate.nodes[i].vx=1);
settle(B,separate,.45);
assert.ok(separate.firstBreak && !separate.unstable,'測試須經過斷裂後的碰撞');
for(const i of probe.path) {
  close(separate.nodes[i].vx,1,1e-7,'其他碎段碰撞不改變獨立木桿的水平動量');
  close(separate.nodes[i].vy*B.UNIT,9.81*.45,1e-7,'其他碎段碰撞不拖慢獨立木桿的下落');
}
assert.throws(()=>B.simulate(falling,{young:NaN}),/正數/,'拒絕無效材料數值');
// 涵蓋首次斷裂、撞河岸側面及落到底部；舊版約 0.34 s 後速度會發散。
for(const settled of [false,true]) {
const collapse=B.sample();if(!settled) collapse.nodes.find(n=>n.load).load=20;
const rubble=B.simulate(collapse),massBefore=rubble.nodes.reduce((sum,n)=>sum+n.baseMass,0);
if(settled) {settle(B,rubble,.5);rubble.nodes.find(n=>n.load).load=20;}
let peakSpeed=0;
for(let i=0;i<4/B.DT;i++) {
  B.step(rubble);
  assert.ok(!rubble.unstable,'20 kg 範例橋必須完成跌落，不能以暫停代替修正');
  assert.ok(rubble.nodes.every(n=>[n.x,n.y,n.vx,n.vy].every(Number.isFinite)),'斷裂和碰撞後保持有限解');
  peakSpeed=Math.max(peakSpeed,...rubble.nodes.map(n=>Math.hypot(n.vx,n.vy)*B.UNIT));
  assert.ok(peakSpeed<20,'碎段不能因碰撞修正而高速飛走');
}
assert.ok(rubble.firstBreak && rubble.fragments.length>=2,'重載須實際斷裂');
close(rubble.nodes.reduce((sum,n)=>sum+n.baseMass,0),massBefore,1e-10,'斷裂跌落保留木材質量');
assert.ok(rubble.nodes.find(n=>n.load===20).y>12.7,'重物須落到底部');
assert.ok(Math.max(...rubble.nodes.map(n=>Math.hypot(n.vx,n.vy)*B.UNIT))<1,'落地後速度應降低');
for(const c of rubble.constraints) if(c.kind==='pin') {
  const gap=Math.hypot(...['x','y'].map(axis=>c.terms.reduce((sum,[i,w])=>sum+rubble.nodes[i][axis]*w,0)));
  assert.ok(gap<1e-4,'跌落後存留接點保持相連');
}
}
console.log(results.join('\n'));
console.log('通過：SI 質量、梁下彎與應力、複合截面、地面反力、步長／網格收斂、材料閾值、Euler 挫曲、自由落體、滑動摩擦、斷裂動量及獨立物件互不影響。');
