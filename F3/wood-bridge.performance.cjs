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
    assert.deepEqual(after.state,before.state,`${name} 的物理結果須與優化前完全一致`);
    console.log(`${name}（${design.bars.length} 條）：${before.ms.toFixed(1)} → ${after.ms.toFixed(1)} ms，減少 ${((1-after.ms/before.ms)*100).toFixed(1)}%；物理結果一致`);
  } else console.log(`${name}（${design.bars.length} 條）：${after.ms.toFixed(1)} ms／模擬 0.25 秒`);
}
