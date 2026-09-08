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
  const attributes=new Map(),calls={},e={textContent:'',innerHTML:'',value:'2',checked:false,listeners:{},
    addEventListener(name,fn){this.listeners[name]=fn;},checkValidity(){return true;},classList:{toggle(){}},setAttribute(k,v){attributes.set(k,v);},getAttribute(k){return attributes.get(k);}};
  e.context=new Proxy(calls,{get(target,key){return target[key]??((...args)=>{target['count:'+key]=(target['count:'+key]||0)+1;});}});
  e.getContext=()=>e.context;e.width=300;e.height=150;
  Object.defineProperty(e,'clientWidth',{get(){layoutReads++;return canvasWidth;}});
  return e;
}
const document={hidden:false,listeners:{},getElementById(id){if(!elements.has(id)) elements.set(id,element());return elements.get(id);},createElement:element,addEventListener(name,fn){this.listeners[name]=fn;}};
const frames=new Map();let nextFrame=0,cpuTime=0,steps=0;
const step=Bridge.step;
Bridge.step=(sim,dt)=>{steps++;cpuTime+=5;step(sim,dt);};
const context={Bridge,document,window:{devicePixelRatio:1},ResizeObserver:class {observe(){}},performance:{now:()=>cpuTime},
  requestAnimationFrame(fn){const id=++nextFrame;frames.set(id,fn);return id;},cancelAnimationFrame(id){frames.delete(id);}};
vm.runInNewContext(scripts[1].replace('  update();draw();\n})();','  globalThis.renderer={draw,model};update();draw();\n})();'),context);
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
assert.equal(frames.size,0,'建造閒置時沒有動畫循環');
for(const [key,value] of Object.entries(Bridge.MATERIAL)) elements.get('mat-'+key).value=value/(key==='young'?1e9:key==='density'?1:1e6);
const click=id=>elements.get(id).listeners.click();
function frame(time) {assert.equal(frames.size,1,'最多只排一個動畫幀');const [id,fn]=frames.entries().next().value;frames.delete(id);fn(time);}
click('test');frame(1000);assert.equal(steps,0);
frame(1050);assert.equal(steps,2,'每步耗 5 ms 時，8 ms 預算只容許兩步，不一次追算 12 步');
click('auto-load');frame(1100);
const weight=context.renderer.model().nodes.find(n=>n.load).load;
frame(1150);assert.equal(steps,4);
assert.ok(Math.abs(context.renderer.model().nodes.find(n=>n.load).load-weight-2*Bridge.DT*.5)<1e-12,'加重跟隨完成的物理步數，不按丟棄的積欠時間跳升');
click('test');assert.equal(frames.size,0,'暫停立即取消動畫');
click('test');document.hidden=true;document.listeners.visibilitychange();assert.equal(frames.size,0,'背景分頁不繼續運算');
document.hidden=false;document.listeners.visibilitychange();frame(9000);assert.equal(steps,4,'返回分頁不追算離開期間');
frame(9050);assert.equal(steps,6);
click('reset');assert.equal(frames.size,0,'返回建造停止動畫循環');
console.log('通過：背景快取、縮放、布局讀取、閒置／暫停／背景停止、單一動畫排程、每幀預算及加重時間。');
