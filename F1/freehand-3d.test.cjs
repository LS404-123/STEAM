const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const html = fs.readFileSync(__dirname + '/freehand-3d.html', 'utf8');
const worksheetCube = fs.readFileSync(__dirname + '/worksheet-dotted-cube.png');
assert.equal(worksheetCube.readUInt32BE(16), 524);
assert.equal(worksheetCube.readUInt32BE(20), 611);
for (let i = 1; i <= 10; i++) {
  const source = fs.readFileSync(__dirname + `/worksheet-model-${String(i).padStart(2, '0')}.png`);
  assert.equal(source.readUInt32BE(16), i === 1 ? 543 : 458);
  assert.equal(source.readUInt32BE(20), i === 1 ? 591 : 528);
}
assert.doesNotMatch(html, /background-image:/);
assert.doesNotMatch(html.match(/<input id="pointsToggle"[^>]*>/)[0], /\bchecked\b/);
assert.match(html, /\.demo-point \{[^}]*pointPulse/);
assert.match(html, /\.transfer-line \{[^}]*animation:transfer [^;]* both/);
assert.match(html, /100% \{ opacity:0; stroke-dashoffset:0; \}/);
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements = new Map();
function element() {
  return {
    children: [], checked: true, innerHTML: '', attributes: {}, listeners: {},
    append(child) { this.children.push(child); },
    setAttribute(key, value) { this.attributes[key] = value; },
    addEventListener(key, callback) { this.listeners[key] = callback; },
    getBoundingClientRect() { return this.rect || {left:0, top:0, width:500, height:500}; },
    setPointerCapture() {},
  };
}
const document = {
  getElementById(id) { if (!elements.has(id)) elements.set(id, element()); return elements.get(id); },
  createElement: element,
};
document.getElementById('pointsToggle').checked = false;
document.getElementById('views').rect = {left:0, top:0, width:1000, height:500};
document.getElementById('projection').rect = {left:500, top:0, width:500, height:500};
const window = {listeners:{}, addEventListener(name, callback) { this.listeners[name] = callback; }};
vm.runInNewContext(script + `
  const assert = globalThis.testAssert;
  function assertProjectedPoints(distance=500) {
    const left = new Set([...model.innerHTML.matchAll(/class="fixed-point" cx="([0-9.]+)" cy="([0-9.]+)"/g)].map(([,x,y]) => x + ',' + y));
    const right = [...projection.innerHTML.matchAll(/class="demo-point" cx="([0-9.]+)" cy="([0-9.]+)"/g)];
    assert.ok(right.length > 0);
    for (const [,x,y] of right) assert.ok(left.has(x + ',' + y));
    const lines = [...transfer.innerHTML.matchAll(/class="transfer-line" x1="([0-9.]+)" y1="([0-9.]+)" x2="([0-9.]+)" y2="([0-9.]+)"/g)];
    assert.equal(lines.length, right.length);
    for (const [,x1,y1,x2,y2] of lines) {
      assert.ok(Math.abs(Number(x2) - Number(x1) - distance) < .2);
      assert.equal(y2, y1);
    }
  }
  function assertRedLinesJoinMarkers() {
    const markers = new Set([...projection.innerHTML.matchAll(/class="marked-point" cx="([0-9.]+)" cy="([0-9.]+)"/g)].map(([,x,y]) => x + ',' + y));
    const lines = [...projection.innerHTML.matchAll(/<line[^>]*x1="([0-9.]+)" y1="([0-9.]+)" x2="([0-9.]+)" y2="([0-9.]+)" stroke="#d82432"/g)];
    assert.ok(lines.length > 0);
    for (const [,x1,y1,x2,y2] of lines) {
      assert.ok(markers.has(x1 + ',' + y1), '圖 ' + (selected + 1) + ' 步驟 ' + demoStep + ' 紅線起點沒有紫點：' + x1 + ',' + y1);
      assert.ok(markers.has(x2 + ',' + y2), '圖 ' + (selected + 1) + ' 步驟 ' + demoStep + ' 紅線終點沒有紫點：' + x2 + ',' + y2);
    }
    return lines;
  }
  function assertSequentialLines() {
    const times = [...projection.innerHTML.matchAll(/class="trace-line" style="--length:[0-9]+;--delay:([0-9.]+)s"/g)].map(([,time]) => Number(time));
    assert.ok(times.length > 0, '圖 ' + (selected + 1) + ' 步驟 ' + demoStep + ' 沒有描線');
    for (let i = 1; i < times.length; i++) assert.ok(times[i] > times[i - 1]);
  }
  assert.doesNotMatch(model.innerHTML, /fixed-point/);
  assert.match(model.innerHTML, /worksheet-model-01\.png/);
  assert.match(projection.innerHTML,/worksheet-dotted-cube\.png/);
  const cubeImage=projection.innerHTML.match(/<image href="worksheet-dotted-cube.png" x="([0-9.]+)" y="([0-9.]+)" width="([0-9.]+)" height="([0-9.]+)"/);
  const sourceToScreen=([x,y])=>[Number(cubeImage[1])+x*Number(cubeImage[3])/524,Number(cubeImage[2])+y*Number(cubeImage[4])/611];
  for(const [source,vertex] of [[[263,17],[3,3,3]],[[263,583],[0,0,0]],[[18,159],[3,0,3]]]) {
    const actual=sourceToScreen(source), expected=frame()(projected(vertex));
    assert.ok(Math.hypot(actual[0]-expected[0],actual[1]-expected[1])<1);
  }
  assert.equal((model.innerHTML.match(/class="cube-node"/g)||[]).length,64);
  toggle.checked=false;
  render();
  assert.match(model.innerHTML, /worksheet-model-01\.png/);
  assert.doesNotMatch(model.innerHTML, /worksheet-dotted-cube\.png|class="cube-node"/);
  toggle.checked=true;
  render();
  assert.notEqual(demoButton.disabled, true);
  assert.equal(nextButton.disabled, true);
  const ordinary = projection.innerHTML;
  nextButton.listeners.click();
  assert.equal(projection.innerHTML, ordinary);
  demoButton.listeners.click();
  assert.equal(demoStep, 1);
  assert.equal(pointsToggle.checked, false);
  assert.equal(nextButton.disabled, false);
  assert.match(projection.innerHTML, /construction-enter/);
  assert.match(projection.innerHTML, /worksheet-dotted-cube\.png/);
  assert.doesNotMatch(projection.innerHTML, /<circle|<polygon|trace-line/);
  assert.equal(transfer.innerHTML, '');
  nextButton.listeners.click();
  assert.equal(demoStep, 2);
  assert.equal(pointsToggle.checked, true);
  assert.match(model.innerHTML, /animation:pointPulse/);
  assert.match(projection.innerHTML, /class="demo-point"[^>]*r="6.5"[^>]*fill="#6941c6"/);
  assert.doesNotMatch(projection.innerHTML, /class="trace-line"|<polygon/);
  assertProjectedPoints();
  const markerCount = (projection.innerHTML.match(/class="demo-point"/g) || []).length;
  projection.rect.left = 600;
  views.rect.width = 1100;
  window.listeners.resize();
  assertProjectedPoints(600);
  projection.rect.left = 500;
  views.rect.width = 1000;
  nextButton.listeners.click();
  assert.equal(demoStep, 3);
  assert.match(projection.innerHTML, /class="trace-line"/);
  assert.match(projection.innerHTML, /<polygon[^>]*fill="#fff" stroke="none"/);
  assert.equal(transfer.innerHTML, '');
  assert.equal((projection.innerHTML.match(/class="marked-point"/g) || []).length, markerCount);
  assert.ok(projection.innerHTML.lastIndexOf('worksheet-dotted-cube.png') > projection.innerHTML.lastIndexOf('stroke="#d82432"'));
  assertRedLinesJoinMarkers();
  assertSequentialLines();
  const firstEdges = (projection.innerHTML.match(/<line[^>]*stroke="#d82432"/g) || []).length;
  nextButton.listeners.click();
  assert.equal(demoStep, 4);
  assert.equal(nextButton.disabled, true);
  assert.ok((projection.innerHTML.match(/<line[^>]*stroke="#d82432"/g) || []).length > firstEdges);
  assert.doesNotMatch(projection.innerHTML, /class="demo-point"/);
  assert.equal((projection.innerHTML.match(/class="marked-point"/g) || []).length, markerCount);
  assert.ok(assertRedLinesJoinMarkers().some(([,x1,y1,x2,y2]) => Math.hypot(x2-x1,y2-y1) > 100));
  assertSequentialLines();
  const completed = projection.innerHTML;
  nextButton.listeners.click();
  assert.equal(projection.innerHTML, completed);
  demoButton.listeners.click();
  assert.equal(demoStep, 1);
  assert.equal(pointsToggle.checked, false);
  assert.doesNotMatch(model.innerHTML, /fixed-point/);
  picker.children[1].listeners.click();
  assert.doesNotMatch(projection.innerHTML, /class="trace-line"/);
  demoButton.listeners.click();
  assert.equal(demoStep, 1);
  nextButton.listeners.click();
  assertProjectedPoints();
  nextButton.listeners.click();
  assert.match(projection.innerHTML, /class="trace-line"/);
  const alignedCount = (projection.innerHTML.match(/class="trace-line"/g) || []).length;
  nextButton.listeners.click();
  assert.ok((projection.innerHTML.match(/class="trace-line"/g) || []).length > 0);
  assert.ok((projection.innerHTML.match(/<line[^>]*stroke="#d82432"/g) || []).length > alignedCount);
  assertRedLinesJoinMarkers();
  assertSequentialLines();
  for (let i = 2; i < shapes.length; i++) {
    picker.children[i].listeners.click();
    assert.equal(nextButton.disabled, true);
    demoButton.listeners.click();
    assert.equal(demoStep, 1);
    nextButton.listeners.click();
    assertProjectedPoints();
    nextButton.listeners.click();
    if(i!==9) assertRedLinesJoinMarkers();
    const cubeEdges = (projection.innerHTML.match(/<line[^>]*stroke="#d82432"/g) || []).length;
    nextButton.listeners.click();
    if(i!==9) assertRedLinesJoinMarkers();
    assert.ok((projection.innerHTML.match(/<line[^>]*stroke="#d82432"/g) || []).length > cubeEdges, '圖 ' + (i + 1) + ' 第四步沒有補畫線');
    assert.equal(nextButton.disabled, true);
  }
  picker.children[9].listeners.click();
  pointsToggle.checked=true;
  render();
  const hidden=frame()(projected([1,1,1])).map(num);
  assert.doesNotMatch(model.innerHTML,new RegExp('class="fixed-point" cx="'+hidden[0]+'" cy="'+hidden[1]+'"'));
  demoButton.listeners.click();
  nextButton.listeners.click();
  assert.equal((projection.innerHTML.match(/class="demo-point"/g)||[]).length,23);
  assert.doesNotMatch(projection.innerHTML,new RegExp('class="demo-point" cx="'+hidden[0]+'" cy="'+hidden[1]+'"'));
  picker.children[0].listeners.click();
  pointsToggle.checked = true;
  render();
  assert.equal(shapes.length, 10);
  assert.equal(shapes[0].blocks.length, 15);
  const expectedLayers = [
    ['000','003','223'], ['310','111','011'], ['001','002','123'],
    ['113','113','223'], ['011','111','123'], ['112','222','233'], ['313','111','313']
  ];
  for (let i = 3; i < shapes.length; i++) {
    const rows = Array.from({length:3},(_,y)=>Array.from({length:3},(_,x)=>
      shapes[i].blocks.filter(([bx,by])=>bx===x&&by===y).length).join(''));
    assert.deepEqual(rows, expectedLayers[i-3], '圖 ' + (i + 1) + ' 方塊位置與工作紙不符');
  }
  assert.deepEqual(shapes[4].blocks.map(p=>p.join(',')).sort(), [
    '0,0,0','0,0,1','0,0,2','1,0,2','0,1,2','1,1,2','2,1,2','1,2,2','2,2,2'
  ].sort());
  assert.ok(!projectionEdges(cubeFaces(shapes[0].blocks)).has(edgeKey([1,0,1],[1,1,1])));
  assert.ok(!projectionEdges(rampFaces(shapes[1].profile)).has(edgeKey([0,1,2],[3,1,2])));
  assert.ok(rampFaces(shapes[1].profile).every(face => Math.hypot(...normal(face.points)) > 0));
  assert.equal(rampFaces(shapes[2].profile).filter(face => dot(normal(face.points.map(rotate)),view) > 0).length, 5);
  assert.equal(rotate([1.5, 1.5, 3])[2], 1.5);
  const origin=projected([1.5,1.5,1.5]);
  const axes=[[2.5,1.5,1.5],[1.5,2.5,1.5],[1.5,1.5,2.5]]
    .map(point=>projected(point).slice(0,2).map((v,i)=>v-origin[i]));
  assert.ok(Math.abs(Math.abs(axes[0][1]/axes[0][0])-1/Math.sqrt(3))<1e-12);
  assert.ok(axes.every(axis=>Math.abs(Math.hypot(...axis)-Math.hypot(...axes[0]))<1e-12));
  assert.equal((cage(frame()).join('').match(/<line /g) || []).length, 36);
  assert.equal((cage(frame()).join('').match(/<circle /g) || []).length, 64);
  assert.equal((cage(frame()).join('').match(/stroke-dasharray="4 9"/g) || []).length, 2);
  assert.doesNotMatch(cage(frame()).join(''), /<line[^>]*stroke-dasharray/);
  const cubeDots = new Set([...cage(frame()).join('').matchAll(/<circle cx="([0-9.]+)" cy="([0-9.]+)"/g)].map(([,x,y]) => x + ',' + y));
  for (let i = 0; i < shapes.length; i++) {
    selected = i;
    render();
    assert.ok(model.innerHTML.includes('worksheet-model-' + String(i + 1).padStart(2, '0') + '.png'));
    assert.doesNotMatch(model.innerHTML, /<polygon/);
    assert.match(projection.innerHTML, /<polygon/);
    if (shapes[i].blocks) for (const cell of shapes[i].blocks) for (const n of cell) assert.ok(n >= 0 && n < 3);
    const faces = shapes[i].profile ? rampFaces(shapes[i].profile) : cubeFaces(shapes[i].blocks);
    const vertices = modelVertices(faces);
    assert.ok(vertices.size > 0);
    for (const key of vertices) for (const n of key.split(',').map(Number)) assert.ok(Number.isInteger(n) && n >= 0 && n <= 3);
    assert.equal((model.innerHTML.match(/class="cube-node"/g)||[]).length,64);
    assert.match(projection.innerHTML,/worksheet-dotted-cube\.png/);
  }
  selected = 0;
  pointsToggle.checked = false;
  render();
  const nodeTarget=key=>({getAttribute(name){return name==='data-node'?key:null}});
  model.listeners.pointerdown({pointerId:7,clientX:20,clientY:20,target:nodeTarget('0,0,0')});
  model.listeners.pointerup({pointerId:7});
  assert.equal(pointsToggle.checked,true);
  assert.ok(chosen[0].has('0,0,0'));
  const chosenScreen=frame()(projected([0,0,0])).map(num);
  assert.ok(cubeDots.has(chosenScreen.join(',')));
  assert.match(model.innerHTML,/class="fixed-point manual-point" data-node="0,0,0"/);
  assert.ok(projection.innerHTML.includes('class="marked-point" cx="'+chosenScreen[0]+'" cy="'+chosenScreen[1]+'"'));
  assert.equal((projection.innerHTML.match(/class="marked-point"/g)||[]).length,1);
  model.listeners.pointerdown({pointerId:7,clientX:20,clientY:20,target:nodeTarget('0,0,0')});
  model.listeners.pointerup({pointerId:7});
  assert.equal(chosen[0].size,0);
  assert.doesNotMatch(projection.innerHTML,/class="marked-point"/);
  model.listeners.keydown({key:'Enter',target:nodeTarget('3,3,3'),preventDefault(){}});
  assert.ok(chosen[0].has('3,3,3'));
  assert.equal((projection.innerHTML.match(/class="marked-point"/g)||[]).length,1);
  picker.children[1].listeners.click();
  assert.doesNotMatch(projection.innerHTML,/class="marked-point"/);
  picker.children[0].listeners.click();
  assert.match(projection.innerHTML,/class="marked-point"/);
  const markerBeforeDrag=projection.innerHTML.match(/class="marked-point" cx="[0-9.]+" cy="[0-9.]+"/)[0];
  const yawBeforeNodeDrag=yaw;
  model.listeners.pointerdown({pointerId:8,clientX:20,clientY:20,target:nodeTarget('1,1,1')});
  model.listeners.pointermove({pointerId:8,clientX:40,clientY:40});
  model.listeners.pointerup({pointerId:8});
  assert.equal(chosen[0].size,1);
  assert.notEqual(yaw,yawBeforeNodeDrag);
  assert.notEqual(projection.innerHTML.match(/class="marked-point" cx="[0-9.]+" cy="[0-9.]+"/)[0],markerBeforeDrag);
  toggle.checked = false;
  render();
  assert.match(model.innerHTML, /class="fixed-point manual-point"/);
  assert.doesNotMatch(model.innerHTML, /worksheet-model-01\.png/);
  assert.doesNotMatch(model.innerHTML, /worksheet-dotted-cube\.png/);
  assert.doesNotMatch(model.innerHTML, /<line/);
  assert.match(projection.innerHTML,/stroke-dasharray="4 9"/);
  pointsToggle.checked = false;
  render();
  assert.doesNotMatch(model.innerHTML, /<circle/);
  assert.doesNotMatch(projection.innerHTML,/class="marked-point"/);
  assert.match(projection.innerHTML,/stroke-dasharray="4 9"/);
  const before = projection.innerHTML;
  const size = frame()([1, 0])[0] - frame()([0, 0])[0];
  const initialYaw = yaw;
  model.listeners.pointerdown({pointerId: 1, clientX: 10, clientY: 10});
  model.listeners.pointermove({pointerId: 1, clientX: 10, clientY: 100});
  assert.notEqual(projection.innerHTML, before);
  assert.equal(yaw, initialYaw);
  assert.notEqual(pitch, 0);
  const vertical = projection.innerHTML;
  const initialPitch = pitch;
  model.listeners.pointermove({pointerId: 1, clientX: 50, clientY: 100});
  assert.notEqual(projection.innerHTML, vertical);
  assert.equal(pitch, initialPitch);
  assert.equal(frame()([1, 0])[0] - frame()([0, 0])[0], size);
  model.listeners.pointerup();
  const keyView = projection.innerHTML;
  model.listeners.keydown({key:'ArrowUp', preventDefault() {}});
  assert.notEqual(projection.innerHTML, keyView);
  pitch = Math.PI;
  toggle.checked = true;
  pointsToggle.checked = true;
  for (let i = 0; i < shapes.length; i++) {
    selected = i;
    render();
    assert.match(model.innerHTML, /<polygon/);
    assert.match(model.innerHTML, /<line/);
    assert.match(projection.innerHTML, /<polygon/);
  }
  document.getElementById('reset').listeners.click();
  assert.equal(pitch, 0);
  assert.equal(yaw, 0);
  assert.ok(Math.abs(Math.abs((projected([2.5,1.5,1.5])[1]-origin[1])/(projected([2.5,1.5,1.5])[0]-origin[0]))-1/Math.sqrt(3))<1e-12);
  picker.children[0].listeners.click();
  model.listeners.keydown({key:'ArrowRight',preventDefault(){}});
  assert.notEqual(yaw,0);
  modeButton.listeners.click();
  assert.equal(sandbox,true);
  assert.equal(yaw,0);
  assert.equal(pitch,0);
  assert.equal(demoStep,0);
  assert.equal(rightTitle.textContent,'練習畫布');
  assert.match(model.innerHTML,/worksheet-model-01\.png/);
  assert.match(projection.innerHTML,/worksheet-dotted-cube\.png/);
  assert.doesNotMatch(projection.innerHTML,/<polygon/);
  assert.match(projection.innerHTML,/class="marked-point"/);
  const beforeSandboxPoints=chosen[0].size;
  model.listeners.pointerdown({pointerId:14,clientX:20,clientY:20,target:nodeTarget('0,0,0')});
  model.listeners.pointerup({pointerId:14});
  assert.equal(chosen[0].size,beforeSandboxPoints+1);
  assert.equal((projection.innerHTML.match(/class="marked-point"/g)||[]).length,beforeSandboxPoints+1);
  const guide=transfer.innerHTML.match(/class="transfer-line sandbox-guide" x1="([0-9.]+)" y1="([0-9.]+)" x2="([0-9.]+)" y2="([0-9.]+)"/);
  assert.ok(guide);
  const aligned=sandboxNodes.get('0,0,0').map(num);
  assert.equal(guide[1],aligned[0]);
  assert.equal(guide[2],aligned[1]);
  assert.ok(Math.abs(Number(guide[3])-Number(guide[1])-500)<.2);
  assert.equal(guide[4],aligned[1]);
  model.listeners.pointerdown({pointerId:14,clientX:20,clientY:20,target:nodeTarget('0,0,0')});
  model.listeners.pointerup({pointerId:14});
  assert.equal(transfer.innerHTML,'');
  model.listeners.pointerdown({pointerId:14,clientX:20,clientY:20,target:nodeTarget('0,0,0')});
  model.listeners.pointerup({pointerId:14});
  const [a,b]=sandboxLines[0], along=t=>[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t];
  const [sx,sy]=along(.2), [ex,ey]=along(.8);
  projection.listeners.pointerdown({pointerId:11,clientX:500+sx,clientY:sy});
  projection.listeners.pointermove({pointerId:11,clientX:500+ex,clientY:ey});
  const [mx,my]=along(.5);
  projection.listeners.pointermove({pointerId:11,clientX:500+mx,clientY:my});
  projection.listeners.pointerup({pointerId:11,clientX:500+mx,clientY:my});
  assert.equal(strokes[0].length,1);
  assert.ok(strokes[0][0].end-strokes[0][0].start>.55);
  assert.match(projection.innerHTML,/class="sandbox-stroke"/);
  const drawn=projection.innerHTML.match(/class="sandbox-stroke" x1="([0-9.]+)" y1="([0-9.]+)" x2="([0-9.]+)" y2="([0-9.]+)"/);
  assert.ok(nearestOnLine(sandboxLines[strokes[0][0].line],[Number(drawn[1]),Number(drawn[2])]).distance<.2);
  assert.ok(nearestOnLine(sandboxLines[strokes[0][0].line],[Number(drawn[3]),Number(drawn[4])]).distance<.2);
  projection.listeners.pointerdown({pointerId:12,clientX:990,clientY:490});
  projection.listeners.pointermove({pointerId:12,clientX:970,clientY:470});
  projection.listeners.pointerup({pointerId:12,clientX:970,clientY:470});
  assert.equal(strokes[0].length,1);
  projection.listeners.pointerdown({pointerId:13,clientX:500+ex,clientY:ey});
  projection.listeners.pointermove({pointerId:13,clientX:500+sx,clientY:sy});
  projection.listeners.pointerup({pointerId:13,clientX:500+sx,clientY:sy});
  assert.equal(strokes[0].length,2);
  assert.ok(strokes[0][1].end-strokes[0][1].start>.55);
  const practice=projection.innerHTML;
  const frozenModel=model.innerHTML;
  model.listeners.keydown({key:'ArrowRight',preventDefault(){}});
  model.listeners.pointerdown({pointerId:15,clientX:30,clientY:30});
  model.listeners.pointermove({pointerId:15,clientX:90,clientY:90});
  model.listeners.pointerup({pointerId:15});
  assert.equal(yaw,0);
  assert.equal(model.innerHTML,frozenModel);
  assert.equal(projection.innerHTML,practice);
  picker.children[1].listeners.click();
  assert.doesNotMatch(projection.innerHTML,/class="sandbox-stroke"/);
  assert.equal(transfer.innerHTML,'');
  picker.children[0].listeners.click();
  assert.match(projection.innerHTML,/class="sandbox-stroke"/);
  modeButton.listeners.click();
  assert.equal(sandbox,false);
  assert.match(projection.innerHTML,/<polygon/);
  assert.match(projection.innerHTML,/worksheet-dotted-cube\.png/);
  modeButton.listeners.click();
  assert.match(projection.innerHTML,/class="sandbox-stroke"/);
  undoStroke.listeners.click();
  assert.equal(strokes[0].length,1);
  undoStroke.listeners.click();
  assert.equal(strokes[0].length,0);
  assert.doesNotMatch(projection.innerHTML,/class="sandbox-stroke"/);
  demoButton.listeners.click();
  assert.equal(sandbox,false);
  assert.equal(demoStep,1);
  assert.match(projection.innerHTML,/worksheet-dotted-cube\.png/);
`, { document, window, testAssert: assert });
console.log('圖 1–10 原工作紙虛線格、練習模式固定鏡頭與吸附畫線檢查通過');
