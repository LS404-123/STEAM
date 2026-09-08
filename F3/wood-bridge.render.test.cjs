// 執行：node F3/wood-bridge.render.test.cjs
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync(__dirname+'/wood-bridge.html','utf8');
const scripts=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
const Bridge=new Function(scripts[0]+';return Bridge;')();
const elements=new Map();let layoutReads=0,canvasWidth=929;
// 記錄原生 Canvas 呼叫，驗證快取；實際外觀另用瀏覽器檢查。
function element() {
  const attributes=new Map(),calls={},e={textContent:'',innerHTML:'',value:'2',checked:false,
    addEventListener(){},classList:{toggle(){}},setAttribute(k,v){attributes.set(k,v);},getAttribute(k){return attributes.get(k);}};
  e.context=new Proxy(calls,{get(target,key){return target[key]??((...args)=>{target['count:'+key]=(target['count:'+key]||0)+1;});}});
  e.getContext=()=>e.context;e.width=300;e.height=150;
  Object.defineProperty(e,'clientWidth',{get(){layoutReads++;return canvasWidth;}});
  return e;
}
const document={getElementById(id){if(!elements.has(id)) elements.set(id,element());return elements.get(id);},createElement:element,addEventListener(){}};
const context={Bridge,document,window:{devicePixelRatio:1},ResizeObserver:class {observe(){}},requestAnimationFrame(){}};
vm.runInNewContext(scripts[1].replace('  update();draw();requestAnimationFrame(frame);','  globalThis.renderer={draw,model};update();draw();requestAnimationFrame(frame);'),context);
const canvas=elements.get('bridge'),calls=canvas.context;
let arcs=calls['count:arc'];
assert.ok(arcs>700,'首次繪製包含完整方格背景');
layoutReads=0;context.renderer.draw();
assert.ok(calls['count:arc']-arcs<100,'同尺寸重畫只繪製橋樑，不重畫數百個背景格點');
assert.equal(calls['count:drawImage'],1,'重畫沿用背景快取');
assert.equal(layoutReads,1,'每幀只讀取一次畫布寬度');
canvasWidth=349;arcs=calls['count:arc'];context.renderer.draw();
assert.equal(canvas.width,349);assert.ok(calls['count:arc']-arcs>700,'縮放後重建清晰的完整背景');
context.window.devicePixelRatio=2;arcs=calls['count:arc'];context.renderer.draw();
assert.equal(canvas.width,698);assert.ok(calls['count:arc']-arcs>700,'像素密度改變也須重建背景');
console.log('通過：背景快取、窄畫布／像素密度重建及布局讀取。');
