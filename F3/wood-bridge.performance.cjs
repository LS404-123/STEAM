// 執行：node F3/wood-bridge.performance.cjs [要比較的舊版 HTML]
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {performance}=require('node:perf_hooks');
const load=file=>new Function(fs.readFileSync(file,'utf8').match(/<script id="bridge-model">([\s\S]*?)<\/script>/)[1]+';return Bridge;')();
const current=load(__dirname+'/wood-bridge.html'),previous=process.argv[2]&&load(process.argv[2]);
const cases=[
  ['範例橋',B=>B.sample()],
  ['多層加固',B=>{const d=B.sample();for(let i=0;i<3;i++) assert.equal(B.reinforce(d,0),'');return d;}],
  ['超載斷裂',B=>{const d=B.sample();d.nodes.find(n=>n.load).load=20;return d;}]
];
const snapshot=s=>({nodes:s.nodes.map(n=>[n.x,n.y,n.vx,n.vy]),broken:s.bars.map(b=>b.broken),firstBreak:s.firstBreak});
function measure(B,design) {
  const times=[];let state;
  // 首輪預熱不計入；三次相同的 0.25 秒模擬取中位數。
  for(let trial=0;trial<4;trial++) {
    const sim=B.simulate(design),start=performance.now();
    for(let i=0;i<60;i++) B.step(sim);
    if(trial) times.push(performance.now()-start);
    state=snapshot(sim);
    assert.ok(state.nodes.flat().every(Number.isFinite),'效能測試不能產生非有限數值');
  }
  return {ms:times.sort((a,b)=>a-b)[1],state};
}
for(const [name,build] of cases) {
  const design=build(current),after=measure(current,design);
  if(previous) {
    const before=measure(previous,design);
    // 新求解器改善未收斂的方程；核對破壞事件並報告位置差，精度另由解析物理測試驗證。
    let reflected=false;
    if(JSON.stringify(after.state.firstBreak)!==JSON.stringify(before.state.firstBreak)) {
      assert.ok(before.state.firstBreak && after.state.firstBreak,'新舊版本都須發生首斷');
      // 對稱橋的捨入誤差可改變先斷哪一側；按實際幾何核對左右鏡像，不能只比較斷桿數量。
      const mirror=p=>({x:2*current.CENTER_X-p.x,y:p.y});
      const near=(a,b)=>current.distance(a,b)<1e-8;
      const mapping=design.bars.map(bar=>{
        const a=mirror(design.nodes[bar.a]),b=mirror(design.nodes[bar.b]);
        const index=design.bars.findIndex(other=>(near(a,design.nodes[other.a])&&near(b,design.nodes[other.b])) || (near(a,design.nodes[other.b])&&near(b,design.nodes[other.a])));
        assert.ok(index>=0,'只接受幾何上確實對稱的破壞');
        return {index,reversed:!near(a,design.nodes[design.bars[index].a])};
      });
      const first=before.state.firstBreak,mapped=mapping[first.bar];
      const mirroredFirst={...first,bar:mapped.index,position:mapped.reversed?1-first.position:first.position};
      assert.deepEqual(after.state.firstBreak,mirroredFirst,`${name} 的首斷截面及負重須對稱相等`);
      assert.ok(before.state.broken.every((broken,i)=>broken===after.state.broken[mapping[i].index]),'所有斷桿須符合鏡像');
      reflected=true;
    } else assert.deepEqual(after.state.broken,before.state.broken,`${name} 的斷裂木桿`);
    assert.equal(after.state.nodes.length,before.state.nodes.length);
    const difference=Math.max(...after.state.nodes.map((n,i)=>Math.hypot(n[0]-before.state.nodes[i][0],n[1]-before.state.nodes[i][1])))*current.UNIT*1000;
    const result=reflected?'斷裂事件為左右鏡像，不比較分裂後的節點索引':`節點最大位置差 ${difference.toFixed(4)} mm，斷裂事件一致`;
    console.log(`${name}（${design.bars.length} 條）：${before.ms.toFixed(1)} → ${after.ms.toFixed(1)} ms，減少 ${((1-after.ms/before.ms)*100).toFixed(1)}%；${result}`);
  } else console.log(`${name}（${design.bars.length} 條）：${after.ms.toFixed(1)} ms／模擬 0.25 秒`);
}
