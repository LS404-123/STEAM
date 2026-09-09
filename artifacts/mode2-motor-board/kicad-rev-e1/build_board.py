"""以 KiCad 10 pcbnew 建立模式二原型；只寫入此專案目錄。"""
from pathlib import Path
import json
import math
import re
import shutil
import uuid
import pcbnew as p

ROOT = Path(__file__).resolve().parent
KICAD = Path(r'C:\Users\LS404\AppData\Local\Programs\KiCad\10.0\share\kicad')
NAME = 'mode2-motor'
LIB = ROOT / 'Mode2.pretty'
LIB.mkdir(exist_ok=True)
(ROOT/'models').mkdir(exist_ok=True)
(ROOT / 'reports').mkdir(exist_ok=True)
(ROOT / 'exports').mkdir(exist_ok=True)
q = lambda s: json.dumps(str(s), ensure_ascii=False)
uid = lambda s: str(uuid.uuid5(uuid.NAMESPACE_URL, 'mode2-motor-rev-e/' + s))
SCH_ID = uid('schematic')
mm = p.FromMM
v = lambda x, y: p.VECTOR2I(mm(x), mm(y))

# 所有接腳以原廠資料表為準；此表同時用於原理圖及 PCB。
PARTS = {
 'U1': ('ATtiny202-SSNR', 'SOIC8', {'1':'VBAT','2':'SW1','3':'SW2','4':'IN1','5':'IN2','6':'UPDI','7':'ISENSE','8':'GND'}),
 'U2': ('DRV8213DSGR', 'WSON8', {'1':'VBAT','2':'OUT1','3':'OUT2','4':'GND','5':'IN2','6':'IN1','7':'GND','8':'ISENSE','9':'GND'}),
 'R1': ('1.24k 1%', 'R0603', {'1':'ISENSE','2':'GND'}),
 'C1': ('100nF 16V', 'C0603', {'1':'VBAT','2':'GND'}),
 'C2': ('100nF 16V', 'C0603', {'1':'VBAT','2':'GND'}),
 'C3': ('100uF 6.3V', 'CP5', {'1':'VBAT','2':'GND'}),
 'S0': ('MSK12C02', 'MSK12C02', {'1':'BATT+','2':'GDRV','3':'GND','4':'GND'}),
 'Q1': ('DMP2035U-7', 'SOT23', {'1':'GATE','2':'BATT+','3':'VBAT'}),
 'R2': ('1k', 'R0603', {'1':'GDRV','2':'GATE'}),
 'R3': ('100k', 'R0603', {'1':'GATE','2':'BATT+'}),
 'P1': ('電池 KF128-2.54-2P', 'KF128_2P', {'1':'BATT+','2':'GND'}),
 'P2': ('SW1 KF128-2.54-2P', 'KF128_2P', {'1':'SW1','2':'GND'}),
 'P3': ('SW2 KF128-2.54-2P', 'KF128_2P', {'1':'SW2','2':'GND'}),
 'P4': ('馬達 KF128-2.54-2P', 'KF128_2P', {'1':'OUT1','2':'OUT2'}),
 'P5': ('UPDI 燒錄', 'Prog3', {'1':'VBAT','2':'UPDI','3':'GND'}),
}
STOCK = {
 'SOT23': 'Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod',
 'SOIC8': 'Package_SO.pretty/SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod',
 'WSON8': 'Package_SON.pretty/Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm_ThermalVias.kicad_mod',
 'R0603': 'Resistor_SMD.pretty/R_0603_1608Metric.kicad_mod',
 'C0603': 'Capacitor_SMD.pretty/C_0603_1608Metric.kicad_mod',
 'CP5': 'Capacitor_SMD.pretty/CP_Elec_5x5.8.kicad_mod',
}
for name, src in STOCK.items():
    text = (KICAD/'footprints'/src).read_text(encoding='utf-8')
    for model in re.findall(r'\$\{KICAD10_3DMODEL_DIR\}/([^\"]+)',text):
        source=KICAD/'3dmodels'/model
        if source.exists():
            if not (ROOT/'models'/source.name).exists():
                shutil.copyfile(source,ROOT/'models'/source.name)
            text=text.replace('${KICAD10_3DMODEL_DIR}/'+model,'${KIPRJMOD}/models/'+source.name)
    start = text.index('"')
    end = text.index('"', start+1)
    (LIB/(name+'.kicad_mod')).write_text(text[:start]+q(name)+text[end+1:], encoding='utf-8')

def custom_fp(name, pads, body=None, desc=''):
    s = f'(footprint {q(name)} (version 20241229) (generator "pcbnew") (layer "F.Cu") (descr {q(desc)}) (attr through_hole)'
    s += '(property "Reference" "REF**" (at 0 -2.5) (layer "F.SilkS") (effects (font (size 0.8 0.8)(thickness 0.12))))'
    s += f'(property "Value" {q(name)} (at 0 2.5) (layer "F.Fab") (effects (font (size 0.8 0.8)(thickness 0.12))))'
    for n,x,y,diam,drill in pads:
        shape = 'rect' if n == '1' else 'circle'
        s += f'(pad {q(n)} thru_hole {shape} (at {x} {y}) (size {diam} {diam}) (drill {drill}) (layers "*.Cu" "*.Mask"))'
    if body:
        w,h=body
        for layer,extra,width in [('F.Fab',0,.1),('F.SilkS',.12,.12),('F.CrtYd',.25,.05)]:
            s += f'(fp_rect (start {-w/2-extra} {-h/2-extra})(end {w/2+extra} {h/2+extra})(stroke(width {width})(type solid))(fill none)(layer {q(layer)}))'
    else:
        xs=[x for _,x,_,_,_ in pads];ys=[y for _,_,y,_,_ in pads]
        s += f'(fp_rect (start {min(xs)-1.1} {min(ys)-1.1})(end {max(xs)+1.1} {max(ys)+1.1})(stroke(width .05)(type solid))(fill none)(layer "F.CrtYd"))'
    (LIB/(name+'.kicad_mod')).write_text(s+')',encoding='utf-8')

# SHOU HAN C431540，2024-12-14 圖面：以俯視方向編號，1 腳在右。
switch_fp = '(footprint "MSK12C02" (version 20241229)(generator "pcbnew")(layer "F.Cu")(attr smd)'
switch_fp += '(property "Reference" "REF**" (at 0 3.6)(layer "F.SilkS")(effects(font(size .8 .8)(thickness .12))))'
switch_fp += '(property "Value" "MSK12C02" (at 0 4.8)(layer "F.Fab")(effects(font(size .8 .8)(thickness .12))))'
for n,x in [('3',-2.25),('2',-.75),('1',2.25)]:
    switch_fp += f'(pad "{n}" smd rect(at {x} 1.95)(size .6 1.3)(layers "F.Cu" "F.Paste" "F.Mask"))'
for x in [-3.675,3.675]:
    for y in [-1.1,1.1]:
        switch_fp += f'(pad "4" smd rect(at {x} {y})(size 1.05 .7)(layers "F.Cu" "F.Paste" "F.Mask"))'
for x in [-1.5,1.5]:
    switch_fp += f'(pad "" np_thru_hole circle(at {x} 0)(size .9 .9)(drill .9)(layers "*.Cu" "*.Mask"))'
switch_fp += '(fp_rect(start -3.35 -1.4)(end 3.35 1.4)(stroke(width .1)(type solid))(fill none)(layer "F.Fab"))'
switch_fp += '(fp_rect(start -1.45 -2.85)(end -.15 -1.4)(stroke(width .1)(type solid))(fill none)(layer "F.Fab"))'
switch_fp += '(fp_rect(start -4.45 -1.65)(end 4.45 2.85)(stroke(width .05)(type solid))(fill none)(layer "F.CrtYd"))'
(LIB/'MSK12C02.kicad_mod').write_text(switch_fp+')',encoding='utf-8')
custom_fp('Prog3',[('1',0,0,1.8,1),('2',2.54,0,1.8,1),('3',5.08,0,1.8,1)],desc='VBAT / UPDI / GND，2.54 mm 間距，可焊線或裝排針')
# KEFA 原廠 2021-03-13 圖：2.54 mm 腳距、1.30 mm 成品孔、5.08 x 6.30 mm 本體。
# 以 1 腳為原點，進線面朝 +Y（板邊）；courtyard 包含本體尺寸公差及 0.25 mm 餘量。
terminal_fp = '(footprint "KF128_2P" (version 20241229)(generator "pcbnew")(layer "F.Cu")(attr through_hole)'
terminal_fp += '(descr "KEFA KF128-2.54-2P C474920; 2021-03-13; wire entry +Y; height 8.8mm")'
terminal_fp += '(property "Reference" "REF**" (at 1.27 -4.3)(layer "F.SilkS")(effects(font(size .8 .8)(thickness .12))))'
terminal_fp += '(property "Value" "KF128-2.54-2P" (at 1.27 4)(layer "F.Fab")(effects(font(size .8 .8)(thickness .12))))'
for n,x in [('1',0),('2',2.54)]:
    shape='rect' if n=='1' else 'circle'
    terminal_fp += f'(pad "{n}" thru_hole {shape}(at {x} 0)(size 2.1 2.1)(drill 1.3)(layers "*.Cu" "*.Mask"))'
for layer,x1,y1,x2,y2,width in [('F.Fab',-1.27,-3.3,3.81,3,.1),('F.SilkS',-1.39,-3.42,3.93,3.12,.12),('F.CrtYd',-1.72,-3.85,4.26,3.55,.05)]:
    terminal_fp += f'(fp_rect(start {x1} {y1})(end {x2} {y2})(stroke(width {width})(type solid))(fill none)(layer "{layer}"))'
terminal_fp += '(fp_line(start -1.39 2.3)(end 3.93 2.3)(stroke(width .12)(type solid))(layer "F.SilkS"))'
(LIB/'KF128_2P.kicad_mod').write_text(terminal_fp+')',encoding='utf-8')
# S0、U2 的 3D 模型依尺寸製作，僅供外形示意。
vrml=['#VRML V2.0 utf8']
def box(x,y,z,w,d,h,color):
    vrml.append(f'Transform {{ translation {x/2.54} {y/2.54} {z/2.54} children [ Shape {{ appearance Appearance {{ material Material {{ diffuseColor {color} }} }} geometry Box {{ size {w/2.54} {d/2.54} {h/2.54} }} }} ] }}')
box(0,0,.45,2,2,.8,'.09 .09 .10')
for x in [-.9,.9]:
    for y in [-.75,-.25,.25,.75]:box(x,y,.06,.6,.25,.12,'.65 .65 .65')
box(0,0,.025,.9,1.6,.05,'.65 .65 .65')
box(-.6,.6,.855,.18,.18,.01,'.75 .75 .75')
(ROOT/'models/WSON8-envelope.wrl').write_text('\n'.join(vrml),encoding='utf-8')
vrml=['#VRML V2.0 utf8']
box(0,0,.7,6.7,2.8,1.4,'.65 .65 .65')
box(-.8,2.125,.7,1.3,1.45,1.15,'.9 .9 .85')
for x in [-3.675,3.675]:
    for y in [-1.1,1.1]:box(x,y,.075,1.05,.7,.15,'.7 .7 .7')
for x in [-2.25,-.75,2.25]:box(x,-1.95,.075,.4,1.3,.15,'.7 .7 .7')
(ROOT/'models/MSK12C02-envelope.wrl').write_text('\n'.join(vrml),encoding='utf-8')
vrml=['#VRML V2.0 utf8']
# 分層外形示意；端子進線口朝模型 -Y，螺絲槽在頂面。
box(1.27,.15,2.6,5.08,6.3,5.2,'.03 .42 .20')
box(1.27,.55,6.95,5.08,3.2,3.5,'.03 .42 .20')
for x in [0,2.54]:
    box(x,0,-1.75,.8,.5,3.5,'.7 .7 .7')
    box(x,-3.005,2.2,1.65,.02,2.0,'.06 .08 .06')
    vertices=[((x+.9*math.cos(i*math.pi/12))/2.54,(.55+.9*math.sin(i*math.pi/12))/2.54,z/2.54) for z in [8.5,8.8] for i in range(24)]
    faces=[list(range(23,-1,-1)),list(range(24,48))]+[[i,(i+1)%24,(i+1)%24+24,i+24] for i in range(24)]
    points=', '.join(' '.join(str(c) for c in point) for point in vertices)
    indices=', '.join(' '.join(str(i) for i in face)+' -1' for face in faces)
    vrml.append(f'Shape {{ appearance Appearance {{ material Material {{ diffuseColor .7 .7 .7 }} }} geometry IndexedFaceSet {{ solid FALSE coord Coordinate {{ point [ {points} ] }} coordIndex [ {indices} ] }} }}')
    box(x,.55,8.81,1.6,.22,.02,'.12 .12 .12')
(ROOT/'models/KF128-2.54-2P-envelope.wrl').write_text('\n'.join(vrml),encoding='utf-8')
for fpname,model in [('MSK12C02','MSK12C02-envelope.wrl'),('WSON8','WSON8-envelope.wrl'),('KF128_2P','KF128-2.54-2P-envelope.wrl')]:
    f=p.FootprintLoad(str(LIB),fpname)
    f.Models().clear()
    m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/models/'+model;f.Add3DModel(m)
    p.FootprintSave(str(LIB),f)
(ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7)(lib (name "Mode2")(type "KiCad")(uri "${KIPRJMOD}/Mode2.pretty")(options "")(descr "此專案的封裝")))',encoding='utf-8')

# 自含式原理圖符號：圖上的位置依功能排列，腳號對應實際封裝。
def effects(size=1.27, justify=''):
    return f'(effects (font (face "Microsoft JhengHei") (size {size} {size})) {justify})'

def pin(n, name, x, y, angle, kind='passive', length=2.54):
    return f'(pin {kind} line (at {x} {y} {angle})(length {length})(name {q(name)} {effects(1.0)})(number {q(n)} {effects(1.0)}))'

def poly(points):
    return '(polyline (pts '+''.join(f'(xy {x} {y})' for x,y in points)+')(stroke(width .254)(type default))(fill(type none)))'

def sym(name, graphics, pins, ref='U', power=False):
    return f'''(symbol {q(name)} {'(power)' if power else ''} (pin_names (offset .8)) (in_bom yes)(on_board yes)
      (property "Reference" {q(ref)} (at 0 17.78 0) {effects()})
      (property "Value" {q(name)} (at 0 15.24 0) {effects()})
      (symbol {q(name+'_0_1')} {graphics}) (symbol {q(name+'_1_1')} {''.join(pins)}))'''

rect=lambda w,h:f'(rectangle (start {-w} {-h})(end {w} {h})(stroke(width .254)(type default))(fill(type background)))'
defs={}
fetlib=(KICAD/'symbols/Transistor_FET.kicad_sym').read_text(encoding='utf-8')
start=fetlib.index('\n\t(symbol "Q_PMOS_GSD"')
end=fetlib.find('\n\t(symbol "',start+1)
defs['PMOS']=fetlib[start:end].strip().replace('Q_PMOS_GSD','PMOS')
defs['MCU']=sym('MCU',rect(12.7,12.7),[
 pin('1','VDD',0,15.24,270,'power_in'),pin('8','GND',0,-15.24,90,'power_in'),
 pin('2','PA6 / SW1',-15.24,5.08,0,'input'),pin('3','PA7 / SW2',-15.24,0,0,'input'),
 pin('6','PA0 / UPDI',-15.24,-7.62,0,'bidirectional'),pin('4','PA1 / IN1',15.24,5.08,180,'output'),
 pin('5','PA2 / IN2',15.24,0,180,'output'),pin('7','PA3 / ADC',15.24,-7.62,180,'input')])
defs['Driver']=sym('Driver',rect(10.16,12.7),[
 pin('1','VM',0,15.24,270,'power_in'),pin('4','GND',0,-15.24,90,'power_in'),pin('9','EP',5.08,-15.24,90,'power_in'),
 pin('6','IN1',-12.7,5.08,0,'input'),pin('5','IN2',-12.7,0,0,'input'),pin('8','IPROPI',-12.7,-7.62,0,'output'),
 pin('2','OUT1',12.7,5.08,180,'output'),pin('3','OUT2',12.7,0,180,'output'),pin('7','GAINSEL',12.7,-7.62,180,'input')])
defs['R']=sym('R',rect(1.016,2.54),[pin('1','~',0,5.08,270),pin('2','~',0,-5.08,90)],'R')
cg=poly([(-2.54,.762),(2.54,.762)])+poly([(-2.54,-.762),(2.54,-.762)])+poly([(0,2.54),(0,.762)])+poly([(0,-2.54),(0,-.762)])
defs['C']=sym('C',cg,[pin('1','~',0,5.08,270),pin('2','~',0,-5.08,90)],'C')
defs['CP']=sym('CP',cg+poly([(-3.5,2.5),(-1.8,2.5)])+poly([(-2.65,1.65),(-2.65,3.35)]),[pin('1','+',0,5.08,270),pin('2','-',0,-5.08,90)],'C')
sg=poly([(2.54,0),(-1.8,-.8)])+''.join(f'(circle(center {x} {y})(radius .3)(stroke(width .15)(type default))(fill(type none)))' for x,y in [(-2.54,0),(-2.54,-5.08),(2.54,0)])
defs['Switch']=sym('Switch',sg,[pin('1','~',-5.08,0,0),pin('2','~',5.08,0,180),pin('3','~',-5.08,-5.08,0),pin('4','CASE',5.08,-5.08,180)],'S')
for name,n,left in [('Conn2',2,False),('Conn2L',2,True),('Conn3',3,False)]:
    ys=[(n-1)*2.54-i*5.08 for i in range(n)]
    defs[name]=sym(name,rect(2.54,n*2.54),[pin(str(i+1),str(i+1),-5.08 if left else 5.08,y,0 if left else 180) for i,y in enumerate(ys)],'P')
defs['Flag']=sym('Flag',poly([(0,0),(0,2.54),(-1.27,2.54),(0,3.81),(1.27,2.54),(0,2.54)]),[pin('1','pwr',0,0,90,'power_out',0)],'#FLG',True)
defs['ExternalSW']=sym('ExternalSW',poly([(0,2.54),(2.0,-1.4)]),[pin('1','~',0,5.08,270),pin('2','~',0,-5.08,90)],'S')
defs['Motor']=sym('Motor','(circle(center 0 0)(radius 3.0)(stroke(width .254)(type default))(fill(type none)))'+f'(text "M"(at 0 0 0){effects(2)})',[pin('1','~',0,5.08,270),pin('2','~',0,-5.08,90)],'M')
(ROOT/'Mode2.kicad_sym').write_text('(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")'+''.join(defs.values())+')',encoding='utf-8')
(ROOT/'sym-lib-table').write_text('(sym_lib_table\n (version 7)\n (lib (name "Mode2") (type "KiCad") (uri "${KIPRJMOD}/Mode2.kicad_sym") (options "") (descr "此專案符號；接腳依原廠資料表"))\n)\n',encoding='utf-8')

sch=[]
def wire(a,b):
    a=tuple(round(x,4) for x in a);b=tuple(round(x,4) for x in b)
    assert a[0]==b[0] or a[1]==b[1],(a,b)
    sch.append(f'(wire(pts(xy {a[0]} {a[1]})(xy {b[0]} {b[1]}))(stroke(width 0)(type default))(uuid {uid("w"+str(a)+str(b))}))')
def label(name,x,y):
    sch.append(f'(label {q(name)} (at {x} {y} 0) {effects(1.0,"(justify left bottom)")}(uuid {uid("l"+name+str(x)+str(y))}))')
def stub(net,x,y,dx=0,dy=5.08):
    wire((x,y),(round(x+dx,4),round(y+dy,4)));label(net,round(x+dx,4),round(y+dy,4))
def dot(x,y):
    sch.append(f'(junction(at {x} {y})(diameter 0)(color 0 0 0 0)(uuid {uid("j"+str(x)+str(y))}))')
def note(text,x,y,size=1.4):
    sch.append(f'(text {q(text)} (at {x} {y} 0) {effects(size,"(justify left top)")}(uuid {uid("t"+text)}))')
def place(ref,typ,x,y,value=None,board=True,prop=None):
    if ref in PARTS:
        val,fp,_=PARTS[ref]
    else: val,fp=value or typ,''
    fp='Mode2:'+fp if fp else ''
    if prop is None: prop=(x,y-20.32,x,y-17.78) if typ in ('MCU','Driver') else (x+4.0,y-1.27,x+4.0,y+1.27)
    rx,ry,vx,vy=prop
    sch.append(f'''(symbol(lib_id {q('Mode2:'+typ)})(at {x} {y} 0)(unit 1)(in_bom {'yes' if board else 'no'})(on_board {'yes' if board else 'no'})(dnp no)(uuid {uid(ref)})
    (property "Reference" {q(ref)}(at {rx} {ry} 0){effects(1.27)})
    (property "Value" {q(val)}(at {vx} {vy} 0){effects(1.1)})
    (property "Footprint" {q(fp)}(at {x} {y} 0)(effects(font(size 1 1))(hide yes)))
    (instances(project {q(NAME)}(path {q('/'+SCH_ID)}(reference {q(ref)})(unit 1)))))''')

note('模式二固定版｜2 粒 AA · 板上電源開關 · 無 LED／模式跳線',17.78,17.78,2.0)
note('電源及去耦',17.78,22.86)
place('P1','Conn2',25.4,33.02,prop=(23,42,23,44.5))
stub('BATT+',30.48,30.48,dx=7.62,dy=0);stub('GND',30.48,35.56,dy=15.24)
place('S0','Switch',50.8,33.02,prop=(50.8,24.13,50.8,26.67))
stub('BATT+',45.72,33.02,dx=-5.08,dy=0)
stub('GND',45.72,38.1,dy=10.16);stub('GND',55.88,38.1,dy=5.08)
wire((55.88,33.02),(60.96,33.02));wire((60.96,33.02),(60.96,38.1));label('GDRV',60.96,33.02)
place('R2','R',60.96,43.18,prop=(66,40.64,66,43.18))
wire((60.96,48.26),(68.58,48.26));wire((68.58,48.26),(78.74,48.26));wire((78.74,48.26),(78.74,40.64));label('GATE',71.12,48.26)
place('R3','R',68.58,55.88,prop=(75,54.61,75,57.15))
wire((68.58,48.26),(68.58,50.8));dot(68.58,48.26);stub('BATT+',68.58,60.96,dy=2.54)
place('Q1','PMOS',83.82,40.64,prop=(100,38.1,100,40.64))
stub('BATT+',86.36,45.72,dy=5.08)
wire((86.36,35.56),(86.36,30.48));wire((86.36,30.48),(116.84,30.48));wire((116.84,30.48),(149.86,30.48));wire((149.86,30.48),(182.88,30.48));wire((182.88,30.48),(208.28,30.48));label('VBAT',198.12,30.48)
for ref,x in [('C3',116.84),('C1',149.86),('C2',182.88)]:
    place(ref,'CP' if ref=='C3' else 'C',x,43.18,prop=(x+8,41.91,x+8,44.45))
    wire((x,30.48),(x,38.1));dot(x,30.48);stub('GND',x,48.26,dy=5.08)
note('S0：1-2 關機；2-3 開機。\nQ1 承受馬達電流，S0 只控制閘極。',20.32,54.61,1.1)
place('#FLG01','Flag',208.28,30.48,board=False,prop=(221,28,221,30))
place('#FLG02','Flag',208.28,53.34,board=False,prop=(221,50,221,53));label('GND',208.28,53.34)
note('C1 靠近 U1；C2、C3 靠近 U2。C3 正極接 VBAT。',116.84,56.0,1.15)
place('U1','MCU',106.68,81.28,prop=(91.44,60.96,91.44,63.5))
place('U2','Driver',182.88,81.28,prop=(165.1,60.96,165.1,63.5))
for x in [106.68,182.88]: stub('VBAT',x,66.04,dy=-5.08);stub('GND',x,96.52,dy=5.08)
stub('GND',187.96,96.52,dy=10.16)
for net,y in [('IN1',76.2),('IN2',81.28)]:
    wire((121.92,y),(170.18,y));label(net,139.7,y)
wire((121.92,88.9),(152.4,88.9));wire((152.4,88.9),(170.18,88.9));label('ISENSE',137.16,88.9);dot(152.4,88.9)
place('R1','R',152.4,106.68,prop=(162,105.41,162,107.95));wire((152.4,88.9),(152.4,101.6));stub('GND',152.4,111.76,dy=5.08)
stub('GND',195.58,88.9,dx=10.16,dy=0)
note('GAINSEL、EP（9 腳）接地。\n限流約 2 A（原型初值）。',165.1,114.3,1.15)
for net,y in [('SW1',76.2),('SW2',81.28),('UPDI',88.9)]:stub(net,91.44,y,dx=-10.16,dy=0)
for ref,net,y in [('P2','SW1',76.2),('P3','SW2',99.06)]:
    place(ref,'Conn2',38.1,y,prop=(35.56,y-11,35.56,y-8.5))
    stub(net,43.18,y-2.54,dx=12.7,dy=0);stub('GND',43.18,y+2.54,dx=12.7,dy=0)
note('2.54 mm 兩位螺絲端子，直接鎖裸線。\n只接 COM、NO；NC 不接。\nU1 啟用內置上拉及軟件去彈跳。',20.32,113.03,1.15)
place('P4','Conn2L',228.6,78.74,prop=(231.14,68.58,231.14,71.12))
for net,y in [('OUT1',76.2),('OUT2',81.28)]:wire((195.58,y),(223.52,y));label(net,208.28,y)
place('P5','Conn3',93.98,124.46,prop=(83.82,123.19,83.82,125.73))
for net,y in [('VBAT',119.38),('UPDI',124.46),('GND',129.54)]:stub(net,99.06,y,dx=10.16,dy=0)
note('P5：焊孔間距 2.54 mm。燒錄時只用一個供電來源。',119.38,127.0,1.15)
note('板外接線（以下元件不裝在 PCB）',20.32,134.62,1.4)
for ref,net,x in [('S1','SW1',35.56),('S2','SW2',99.06)]:
    place(ref,'ExternalSW',x,149.86,value=net+' 微動開關',board=False,prop=(x+15,148.59,x+15,151.13))
    stub(net,x,144.78,dy=-5.08);stub('GND',x,154.94,dy=5.08)
place('M1','Motor',203.2,149.86,value='FA-130 馬達',board=False,prop=(188,148.59,188,151.13))
place('C4','C',233.68,149.86,value='100nF 陶瓷',board=False,prop=(247,148.59,247,151.13))
for net,y in [('OUT1',139.7),('OUT2',160.02)]:
    wire((203.2,y),(233.68,y));label(net,213.36,y)
for x in [203.2,233.68]:wire((x,139.7),(x,144.78));wire((x,154.94),(x,160.02))
note('C4 直接焊在馬達兩端，使用無極性陶瓷電容。',177.8,162.56,1.15)
note('同名標籤代表電氣相連；#FLG 是電氣檢查標記，不是實體元件。',20.32,170.18,1.15)
note('需要另行燒錄韌體：SW1 → 正轉；SW2 → 反轉；SW1 → 停止／鎖定 3 秒。\n僅適用 2 粒 AA；不接 3 粒 AA。此為待實機驗證原型，限流不等於堵轉自動停機。',20.32,184.15,1.1)
embedded=''.join(s.replace('(symbol '+q(k), '(symbol '+q('Mode2:'+k),1) for k,s in defs.items())
(ROOT/(NAME+'.kicad_sch')).write_text(f'''(kicad_sch(version 20250114)(generator "eeschema")(uuid {SCH_ID})(paper "A4")
 (title_block(title "模式二馬達控制板")(date "2026-09-09")(rev "E 原型")(company "STEAM"))
 (lib_symbols {embedded}) {''.join(sch)} (embedded_fonts no))''',encoding='utf-8')

# 雙面 25 x 24 mm，所有元件在正面；底面主要為接地平面。
b=p.BOARD();b.SetCopperLayerCount(2)
ds=b.GetDesignSettings();ds.SetBoardThickness(mm(1.6));ds.m_MinClearance=mm(.15);ds.m_TrackMinWidth=mm(.15);ds.m_MinThroughDrill=mm(.2);ds.m_CopperEdgeClearance=mm(.3)
netnames=sorted({net for _,_,pins in PARTS.values() for net in pins.values()})
nets={}
for name in netnames:
    canonical='/'+name
    n=p.NETINFO_ITEM(b,canonical);b.Add(n);nets[name]=n
fps={}
def fp(ref,x,y,angle=0):
    value,name,pins=PARTS[ref]
    f=p.FootprintLoad(str(LIB),name);f.SetReference(ref);f.SetValue(value);f.SetFPID(p.LIB_ID('Mode2',name));f.SetPosition(v(x,y));f.SetOrientationDegrees(angle)
    f.SetPath(p.KIID_PATH('/'+SCH_ID+'/'+uid(ref)))
    for pad in f.Pads():
        if pad.GetNumber():pad.SetNet(nets[pins[pad.GetNumber()]])
    f.Reference().SetTextSize(v(.8,.8));f.Reference().SetTextThickness(mm(.12));f.Value().SetVisible(False)
    b.Add(f);fps[ref]=f
    return f
fp('S0',5.1,1.8)
fp('Q1',7.5,6.8,90)
fp('R2',3.7,6.0)
fp('R3',1.3,6.5,90)
fp('C3',13,4.1,90)
fp('P1',21.1,5.94,90)
fp('U1',5.7,13.0)
fp('C1',4.0,9.4)
fp('U2',14.0,13.2,180)
fp('C2',15.6,15.7)
fp('R1',11.5,15.5,180)
fp('P4',21.1,14.54,90)
fp('P2',2.5,20.3)
fp('P3',9.6,20.3)
fp('P5',15.3,20.4)
# 插座蓋住正面位號；改由背面 SW1／SW2 絲印識別。
for ref in ('P1','P2','P3','P4'): fps[ref].Reference().SetVisible(False)
for a,z in [((0,0),(25,0)),((25,0),(25,24)),((25,24),(0,24)),((0,24),(0,0))]:
    e=p.PCB_SHAPE();e.SetShape(p.SHAPE_T_SEGMENT);e.SetStart(v(*a));e.SetEnd(v(*z));e.SetLayer(p.Edge_Cuts);e.SetWidth(mm(.05));b.Add(e)

def padpos(ref,n):
    pad=next(z for z in fps[ref].Pads() if z.GetNumber()==str(n));t=pad.GetPosition();return (round(p.ToMM(t.x),4),round(p.ToMM(t.y),4))
def track(net,points,width=.25,layer=p.F_Cu):
    # 直角切成兩次 45° 轉彎；兩端保持原位，避免改變焊盤及過孔接線。
    original = points
    points = [original[0]]
    for a, corner, z in zip(original, original[1:], original[2:]):
        u = (a[0]-corner[0], a[1]-corner[1])
        w = (z[0]-corner[0], z[1]-corner[1])
        lu, lw = math.hypot(*u), math.hypot(*w)
        if lu and lw and abs(u[0]*w[0]+u[1]*w[1])/(lu*lw) < 1e-7:
            cut = min(max(.35, width), lu*.4, lw*.4)
            points.extend([(corner[0]+u[0]*cut/lu, corner[1]+u[1]*cut/lu),
                           (corner[0]+w[0]*cut/lw, corner[1]+w[1]*cut/lw)])
        else:
            points.append(corner)
    points.append(original[-1])
    for a,z in zip(points,points[1:]):
        if a==z:continue
        t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(nets[net]);b.Add(t)
def via(net,x,y):
    t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(mm(.6));t.SetDrill(mm(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(nets[net]);b.Add(t)
def text(s,x,y,size=.8,layer=p.F_SilkS,angle=0):
    t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(mm(.12));t.SetLayer(layer)
    if any(ord(c)>127 for c in s): t.SetUnresolvedFontName('Microsoft JhengHei')
    t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T))
    if layer==p.B_SilkS:t.SetMirrored(True)
    b.Add(t)

# 佈線由下一節固定座標建立；初次輸出焊盤座標以便核對。
# Q1 source 接電池、drain 接 VBAT；小開關不經過馬達電流。
track('BATT+',[padpos('P1',1),(17,5.94),(17,2),(9.7,2),(9.7,7.7),(9.3,7.7)],.8,p.B_Cu);via('BATT+',9.3,7.7)
track('BATT+',[(9.3,7.7),padpos('Q1',2)],.6)
track('BATT+',[(9.7,4.6),(7.35,4.6)],.4,p.B_Cu);via('BATT+',7.35,4.6)
track('BATT+',[(7.35,4.6),padpos('S0',1)],.4)
track('BATT+',[padpos('R3',2),(.8,4.8)],.25);via('BATT+',.8,4.8)
track('BATT+',[(.8,4.8),(.8,3.8),(6.55,3.8),(7.35,4.6)],.3,p.B_Cu)
track('GDRV',[padpos('S0',2),(4.35,4.8),(2.875,4.8),padpos('R2',1)],.25)
track('GATE',[padpos('R2',2),(5.3,6),(5.3,7.7375),padpos('Q1',1)],.25)
track('GATE',[padpos('R3',1),(1.3,7.4),(3.9,7.4),(4.525,6.775),padpos('R2',2)],.25)
track('VBAT',[padpos('Q1',3),(8.5,5.8625),(10.5,6.3),padpos('C3',1)],.6)
via('VBAT',7.5,5.6)
track('VBAT',[padpos('Q1',3),(7.5,5.6)],.4)
track('VBAT',[(7.5,5.6),(5.8,5.6),(5.8,8.7),(3.225,8.7)],.4,p.B_Cu);via('VBAT',3.225,8.7)
track('VBAT',[(3.225,8.7),padpos('C1',1),(3.225,11.095)],.4)
track('VBAT',[padpos('C3',1),(14,6.3),(15.3,7.6),(15.3,8.6)],.8);via('VBAT',15.3,8.6)
track('VBAT',[(15.3,8.6),(15.3,16.325),(15.225,16.4)],.8,p.B_Cu);via('VBAT',15.225,16.4)
track('VBAT',[(15.225,16.4),padpos('C2',1)],.6)
track('VBAT',[(14.95,13.95),(15.5,13.95),(15.6,14.05),(15.6,14.25)],.2)
track('VBAT',[(15.6,14.25),(15.6,14.8),(15.225,15.175),padpos('C2',1)],.6)
track('VBAT',[(15.225,16.4),(15.225,16.8),(15.3,16.875),padpos('P5',1)],.4,p.B_Cu)
# 延用 B 版已驗證的控制區佈線，整區下移 2 mm。
def core_track(net,points,width=.25,layer=p.F_Cu):track(net,[(x,y+2) for x,y in points],width,layer)
def core_via(net,x,y):via(net,x,y+2)
core_track('SW1',[(3.225,10.365),(2,10.365),(1.3,11.065),(1.3,15.6),(2.5,16.8)],.25)
track('SW1',[(2.5,18.8),padpos('P2',1)],.25)
core_track('SW2',[(3.225,11.635),(2.6,11.635),(1.85,12.385),(1.85,14.55),(2,14.7)],.25);core_via('SW2',2,14.7)
track('SW2',[(2,16.7),(1,17.7),(1,22),(8,22),padpos('P3',1)],.25,p.B_Cu)
core_track('IN1',[(3.225,12.905),(3.225,14)],.25);core_via('IN1',3.225,14)
core_track('IN1',[(3.225,14),(10.4,14),(11.8,12.6),(11.8,11.2)],.25,p.B_Cu);core_via('IN1',11.8,11.2)
core_track('IN1',[(11.8,11.2),(12.3,11.2),(12.55,10.95),(13.05,10.95)],.2)
core_track('IN2',[(8.175,12.905),(9.8,12.905),(10.2,12.505),(10.2,10.45),(13.05,10.45)],.2)
core_track('UPDI',[(8.175,11.635),(9,11.635)],.25);core_via('UPDI',9,11.635)
core_track('UPDI',[(9,11.635),(4.9,11.635),(4.9,12.5)],.25,p.B_Cu);core_via('UPDI',4.9,12.5)
core_track('UPDI',[(4.9,12.5),(4.9,15.6),(17.84,15.6),(17.84,18.4)],.25)
core_track('ISENSE',[(8.175,10.365),(9.4,10.365)],.2);core_via('ISENSE',9.4,10.365)
core_track('ISENSE',[(9.4,10.365),(10.5,10.365),(10.5,8.8),(12.7,8.8),(12.7,12.4),(12.325,12.775),(12.325,14.4)],.2,p.B_Cu)
core_via('ISENSE',12.325,14.4)
core_track('ISENSE',[(13.05,11.95),(12.5,11.95),(12.325,12.125),(12.325,13.5),(12.325,14.4)],.2)
core_track('GND',[(13.05,11.45),(14,11.45)],.2)
core_track('GND',[(14.95,10.45),(14,10.45)],.2)
core_track('OUT1',[(14.95,11.45),(16,11.45)],.2)
track('OUT1',[(16,13.45),(16.2,13.45),(18.1,15.35),(20.29,15.35),padpos('P4',1)],.6)
core_track('OUT2',[(14.95,10.95),(15.5,10.95),(16.2,10.3)],.2);core_via('OUT2',16.2,10.3)
track('OUT2',[(16.2,12.3),(17,13.1),(18.1,12),padpos('P4',2)],.6,p.B_Cu)
core_track('GND',[(4.775,7.4),(5.5,7.4)],.4);core_via('GND',5.5,7.4)
core_track('GND',[(8.175,9.095),(9.1,9.095)],.4);core_via('GND',9.1,9.095)

# 正反面接地鋪銅；散熱焊盤與地層直接連接。

for layer in [p.F_Cu,p.B_Cu]:
    zone=p.ZONE(b);zone.SetLayer(layer);zone.SetNet(nets['GND']);zone.SetLocalClearance(mm(.2));zone.SetPadConnection(p.ZONE_CONNECTION_FULL);zone.SetMinThickness(mm(.2))
    outline=zone.Outline();outline.NewOutline()
    for x,y in [(.35,.35),(24.65,.35),(24.65,23.65),(.35,23.65)]:outline.Append(mm(x),mm(y))
    b.Add(zone)
for x,y in [(1,9.5),(11,9.2),(21,9),(11,16.6),(18.5,17),(6.5,11.3),(22.7,18)]:via('GND',x,y)

for ref,(x,y) in {'U1':(6,13),'U2':(13.4,15),'C1':(6,9.3),'C2':(16,17.4),'C3':(13,8.4),'R1':(11.4,14.3),'S0':(5.1,.8),'Q1':(9.1,5.0),'R2':(3.7,8.0),'R3':(1.2,8.5),'P5':(16.7,18.6)}.items():
    fps[ref].Reference().SetPosition(v(x,y));fps[ref].Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
text('電池',21,.9,.8,p.F_SilkS)
text('馬達',17,13.5,.8,p.F_SilkS,90)
text('SW1',.5,20.3,.8,p.F_SilkS,90)
text('SW2',7.5,20.3,.8,p.F_SilkS,90)
text('2xAA',19,1.2,.8,p.B_SilkS)
text('關',3.8,2.9,.8,p.B_SilkS);text('開',6.1,2.9,.8,p.B_SilkS)
text('電池',21.1,7.8,.8,p.B_SilkS)
for n,mark in [('1','+'),('2','-')]:
    _,y=padpos('P1',n)
    text(mark,23.2,y,.9,p.B_SilkS)
    text(mark,16.8,y,.8,p.F_SilkS)
text('SW1',3.77,17.3,.85,p.B_SilkS);text('SW2',10.87,17.3,.85,p.B_SilkS)
for ref in ['P2','P3']:
    for n,mark in [('1','NO'),('2','COM')]:
        x,_=padpos(ref,n)
        text(mark,x,23.0,.8,p.B_SilkS)
text('馬達',21.1,16.5,.85,p.B_SilkS)
for n,mark in [('1','M1'),('2','M2')]:
    _,y=padpos('P4',n)
    text(mark,23.5,y,.8,p.B_SilkS)
for n,mark in [('1','V'),('2','UPDI'),('3','G')]:
    x,_=padpos('P5',n)
    text(mark,x,18.4,.8,p.B_SilkS)
text('模式二 E1',8,10,.85,p.B_SilkS)
b.BuildConnectivity()
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),b)
template=json.loads((KICAD/'template/kicad.kicad_pro').read_text(encoding='utf-8'))
template['meta']['filename']=NAME+'.kicad_pro'
template['board']['design_settings']['rules'].update({'min_clearance':.15,'min_track_width':.15,'min_through_hole_diameter':.2,'min_copper_edge_clearance':.3,'min_via_diameter':.5,'min_via_annular_width':.1})
template['net_settings']['classes']=[{'name':'Default','clearance':.15,'track_width':.25,'via_diameter':.6,'via_drill':.3,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':.2,'diff_pair_gap':.25,'diff_pair_via_gap':.25,'bus_width':12,'wire_width':6,'line_style':0,'pcb_color':'rgba(0, 0, 0, 0.000)','schematic_color':'rgba(0, 0, 0, 0.000)'}]
(ROOT/(NAME+'.kicad_pro')).write_text(json.dumps(template,indent=2,ensure_ascii=False),encoding='utf-8')
(ROOT/'expected-nets.json').write_text(json.dumps({ref:pins for ref,(_,_,pins) in PARTS.items()},indent=2),encoding='utf-8')

def check_design():
    """獨立查核關鍵腳號與電流門檻，避免功能被錯接或數值誤植。"""
    assert PARTS['U1'][2]['4']=='IN1' and PARTS['U2'][2]['6']=='IN1'
    assert PARTS['U1'][2]['5']=='IN2' and PARTS['U2'][2]['5']=='IN2'
    assert PARTS['U2'][2]['7']==PARTS['U2'][2]['9']=='GND'
    assert PARTS['S0'][2]=={'1':'BATT+','2':'GDRV','3':'GND','4':'GND'}
    assert PARTS['Q1'][2]=={'1':'GATE','2':'BATT+','3':'VBAT'}
    assert PARTS['R2'][2]=={'1':'GDRV','2':'GATE'}
    assert PARTS['R3'][2]=={'1':'GATE','2':'BATT+'}
    for ref,net in [('P2','SW1'),('P3','SW2')]:
        assert PARTS[ref][1]=='KF128_2P' and PARTS[ref][2]=={'1':net,'2':'GND'}
        assert math.isclose(padpos(ref,2)[0]-padpos(ref,1)[0],2.54,abs_tol=1e-6)
        assert all(math.isclose(p.ToMM(pad.GetDrillSize().x),1.3,abs_tol=1e-6) for pad in fps[ref].Pads())
    for ref,pins in [('P1',{'1':'BATT+','2':'GND'}),('P4',{'1':'OUT1','2':'OUT2'})]:
        assert PARTS[ref][1]=='KF128_2P' and PARTS[ref][2]==pins
        assert math.isclose(padpos(ref,1)[1]-padpos(ref,2)[1],2.54,abs_tol=1e-6)
        assert fps[ref].GetOrientationDegrees()==90  # 進線朝右方板外
        assert all(math.isclose(p.ToMM(pad.GetDrillSize().x),1.3,abs_tol=1e-6) for pad in fps[ref].Pads())
    assert 3.3/1000 < .050  # 最大閘極充電電流低於 S0 的 50mA 額定值
    assert 2.0*100000/101000 > 1.8  # 電池2V時仍符合Q1導通規格的VGS測試點
    assert 1.99 < .510/(205e-6*1240) < 2.02
    for ref,(_,_,pins) in PARTS.items():
        actual={x.GetNumber():('S0_NC' if x.GetNetname()=='unconnected-(S0-Pad3)' else x.GetNetname().removeprefix('/')) for x in fps[ref].Pads() if x.GetNumber()}
        assert actual==pins,(ref,actual,pins)
    print('接腳及限流計算檢查通過')
check_design()
