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
uid = lambda s: str(uuid.uuid5(uuid.NAMESPACE_URL, 'mode2-motor-v1/' + s))
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
 'S0': ('500ASSP1M2QE', 'S0_500ASSP1M2QE', {'1':'BATT+','2':'VBAT','3':'S0_NC'}),
 'P1': ('電池 2xAA', 'Wire2', {'1':'BATT+','2':'GND'}),
 'P2': ('SW1 PH-2 插座', 'PH2', {'1':'SW1','2':'GND'}),
 'P3': ('SW2 PH-2 插座', 'PH2', {'1':'SW2','2':'GND'}),
 'P4': ('馬達接線', 'Wire2', {'1':'OUT1','2':'OUT2'}),
 'P5': ('UPDI 燒錄', 'Prog3', {'1':'VBAT','2':'UPDI','3':'GND'}),
}
STOCK = {
 'PH2': 'Connector_JST.pretty/JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical.kicad_mod',
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

custom_fp('S0_500ASSP1M2QE',[(str(i+1), (i-1)*2.54,0,1.9,1.1) for i in range(3)],(10.16,5.08),
          'E-Switch T551002 rev G: 3 holes 1.09 mm, pitch 2.54 mm; body 10.16 x 5.08 mm')
custom_fp('Wire2',[('1',0,0,1.7,.8),('2',2.5,0,1.7,.8)],desc='直接焊線孔；孔徑 0.8 mm，間距 2.5 mm')
custom_fp('Prog3',[('1',0,0,1.8,1),('2',2.54,0,1.8,1),('3',5.08,0,1.8,1)],desc='VBAT / UPDI / GND，2.54 mm 間距，可焊線或裝排針')
# 廠方提供的 S0 STEP；U2 缺少庫模型，使用依資料表尺寸製作的外形示意。
vrml=['#VRML V2.0 utf8']
def box(x,y,z,w,d,h,color):
    vrml.append(f'Transform {{ translation {x/2.54} {y/2.54} {z/2.54} children [ Shape {{ appearance Appearance {{ material Material {{ diffuseColor {color} }} }} geometry Box {{ size {w/2.54} {d/2.54} {h/2.54} }} }} ] }}')
box(0,0,.45,2,2,.8,'.09 .09 .10')
for x in [-.9,.9]:
    for y in [-.75,-.25,.25,.75]:box(x,y,.06,.6,.25,.12,'.65 .65 .65')
box(0,0,.025,.9,1.6,.05,'.65 .65 .65')
box(-.6,.6,.855,.18,.18,.01,'.75 .75 .75')
(ROOT/'models/WSON8-envelope.wrl').write_text('\n'.join(vrml),encoding='utf-8')
for fpname,model in [('S0_500ASSP1M2QE','500ASSPxM2xE.stp'),('WSON8','WSON8-envelope.wrl')]:
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
defs['Switch']=sym('Switch',sg,[pin('1','~',-5.08,0,0),pin('2','~',5.08,0,180),pin('3','~',-5.08,-5.08,0)],'S')
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
place('S0','Switch',55.88,30.48,prop=(55.88,22.86,55.88,25.4))
wire((30.48,30.48),(50.8,30.48));label('BATT+',33.02,30.48)
stub('GND',30.48,35.56,dy=20.32)
sch.append(f'(no_connect(at 50.8 35.56)(uuid {uid("ncS0")}))')
wire((60.96,30.48),(78.74,30.48));wire((78.74,30.48),(106.68,30.48));wire((106.68,30.48),(182.88,30.48));wire((182.88,30.48),(208.28,30.48));label('VBAT',198.12,30.48)
for ref,x in [('C3',78.74),('C1',106.68),('C2',182.88)]:
    place(ref,'CP' if ref=='C3' else 'C',x,43.18,prop=(x+8,41.91,x+8,44.45))
    wire((x,30.48),(x,38.1));dot(x,30.48);stub('GND',x,48.26,dy=5.08)
place('#FLG01','Flag',208.28,30.48,board=False,prop=(221,28,221,30))
place('#FLG02','Flag',208.28,53.34,board=False,prop=(221,50,221,53));label('GND',208.28,53.34)
note('C1 靠近 U1；C2、C3 靠近 U2。C3 正極接 VBAT。',116.84,52.07,1.15)
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
note('PH 2.0 mm 兩針插座，配 PHR-2 插頭。\n只接 COM、NO；NC 不接。\nU1 啟用內置上拉及軟件去彈跳。',20.32,113.03,1.15)
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
embedded=''.join(s.replace('(symbol '+q(k)+' ', '(symbol '+q('Mode2:'+k)+' ',1) for k,s in defs.items())
(ROOT/(NAME+'.kicad_sch')).write_text(f'''(kicad_sch(version 20250114)(generator "eeschema")(uuid {SCH_ID})(paper "A4")
 (title_block(title "模式二馬達控制板")(date "2026-09-09")(rev "B 原型")(company "STEAM"))
 (lib_symbols {embedded}) {''.join(sch)} (embedded_fonts no))''',encoding='utf-8')

# 雙面 22 x 20 mm，所有元件在正面；底面主要為接地平面。
b=p.BOARD();b.SetCopperLayerCount(2)
ds=b.GetDesignSettings();ds.SetBoardThickness(mm(1.6));ds.m_MinClearance=mm(.15);ds.m_TrackMinWidth=mm(.15);ds.m_MinThroughDrill=mm(.2);ds.m_CopperEdgeClearance=mm(.3)
netnames=sorted({net for _,_,pins in PARTS.values() for net in pins.values()})
nets={}
for name in netnames:
    canonical='unconnected-(S0-Pad3)' if name=='S0_NC' else '/'+name
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
fp('S0',7,3.5)
fp('C3',16.0,4.8,90)
fp('P1',20.5,1.8,270)
fp('U1',5.7,11.0)
fp('C1',4.0,7.4)
fp('U2',14.0,11.2,180)
fp('C2',16,13.5)
fp('R1',11.5,13.5,180)
fp('P4',20.5,10.0,270)
fp('P2',2.5,16.8)
fp('P3',9.6,16.8)
fp('P5',15.3,18.4)
# 插座蓋住正面位號；改由背面 SW1／SW2 絲印識別。
for ref in ('P2','P3'): fps[ref].Reference().SetVisible(False)
for a,z in [((0,0),(22,0)),((22,0),(22,20)),((22,20),(0,20)),((0,20),(0,0))]:
    e=p.PCB_SHAPE();e.SetShape(p.SHAPE_T_SEGMENT);e.SetStart(v(*a));e.SetEnd(v(*z));e.SetLayer(p.Edge_Cuts);e.SetWidth(mm(.05));b.Add(e)

def padpos(ref,n):
    pad=next(z for z in fps[ref].Pads() if z.GetNumber()==str(n));t=pad.GetPosition();return (round(p.ToMM(t.x),4),round(p.ToMM(t.y),4))
def track(net,points,width=.25,layer=p.F_Cu):
    for a,z in zip(points,points[1:]):
        if a==z:continue
        t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(nets[net]);b.Add(t)
def via(net,x,y):
    t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(mm(.6));t.SetDrill(mm(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(nets[net]);b.Add(t)
def text(s,x,y,size=.8,layer=p.F_SilkS):
    t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(mm(.12));t.SetLayer(layer)
    if any(ord(c)>127 for c in s): t.SetUnresolvedFontName('Microsoft JhengHei')
    if layer==p.B_SilkS:t.SetMirrored(True)
    b.Add(t)

# 佈線由下一節固定座標建立；初次輸出焊盤座標以便核對。
track('BATT+',[(20.5,1.8),(20.5,1.1),(4.46,1.1),(4.46,3.5)],.8,p.B_Cu)
track('VBAT',[(7,3.5),(7,5.6),(7.6,6.2),(18.2,6.2)],.8,p.B_Cu)
track('VBAT',[(16,7),(17,7),(18.2,6.2)],.8);via('VBAT',18.2,6.2)
track('VBAT',[(18.2,6.2),(18.2,8),(15.8,8),(15.3,8.5),(15.3,14.4),(15.225,14.4)],.8,p.B_Cu)
via('VBAT',15.225,14.4)
track('VBAT',[(15.225,14.4),(15.225,13.5)],.6)
track('VBAT',[(14.95,11.95),(15.5,11.95),(15.6,12.05),(15.6,12.25)],.2)
track('VBAT',[(15.6,12.25),(15.6,12.8),(15.225,13.175),(15.225,13.5)],.6)
track('VBAT',[(7,3.5),(7,5.2),(3.225,5.2),(3.225,7.4),(3.225,9.095)],.4)
track('VBAT',[(15.225,14.4),(15.3,14.475),(15.3,18.4)],.4,p.B_Cu)
track('SW1',[(3.225,10.365),(2,10.365),(1.3,11.065),(1.3,15.6),(2.5,16.8)],.25)
track('SW2',[(3.225,11.635),(2.6,11.635),(1.85,12.385),(1.85,14.55),(2,14.7)],.25);via('SW2',2,14.7)
track('SW2',[(2,14.7),(1.3,15.4),(1.3,18.3),(9.6,18.3),(9.6,16.8)],.25,p.B_Cu)
track('IN1',[(3.225,12.905),(3.225,14)],.25);via('IN1',3.225,14)
track('IN1',[(3.225,14),(10.4,14),(11.8,12.6),(11.8,11.2)],.25,p.B_Cu);via('IN1',11.8,11.2)
track('IN1',[(11.8,11.2),(12.3,11.2),(12.55,10.95),(13.05,10.95)],.2)
track('IN2',[(8.175,12.905),(9.8,12.905),(10.2,12.505),(10.2,10.45),(13.05,10.45)],.2)
track('UPDI',[(8.175,11.635),(9,11.635)],.25);via('UPDI',9,11.635)
track('UPDI',[(9,11.635),(4.9,11.635),(4.9,12.5)],.25,p.B_Cu);via('UPDI',4.9,12.5)
track('UPDI',[(4.9,12.5),(4.9,15.6),(17.84,15.6),(17.84,18.4)],.25)
track('ISENSE',[(8.175,10.365),(9.4,10.365)],.2);via('ISENSE',9.4,10.365)
track('ISENSE',[(9.4,10.365),(10.5,10.365),(10.5,8.8),(12.7,8.8),(12.7,12.4),(12.325,12.775),(12.325,14.4)],.2,p.B_Cu)
via('ISENSE',12.325,14.4)
track('ISENSE',[(13.05,11.95),(12.5,11.95),(12.325,12.125),(12.325,13.5),(12.325,14.4)],.2)
track('GND',[(13.05,11.45),(14,11.45)],.2)
track('GND',[(14.95,10.45),(14,10.45)],.2)
track('OUT1',[(14.95,11.45),(16,11.45)],.2)
track('OUT1',[(16,11.45),(16.2,11.45),(18.1,9.55),(20.5,9.55),(20.5,10)],.6)
track('OUT2',[(14.95,10.95),(15.5,10.95),(16.2,10.3)],.2);via('OUT2',16.2,10.3)
track('OUT2',[(16.2,10.3),(17,11.1),(17,12.5),(20.5,12.5)],.6,p.B_Cu)
track('GND',[(4.775,7.4),(5.5,7.4)],.4);via('GND',5.5,7.4)
track('GND',[(8.175,9.095),(9.1,9.095)],.4);via('GND',9.1,9.095)

# 正反面接地鋪銅；散熱焊盤與地層直接連接。
for layer in [p.F_Cu,p.B_Cu]:
    zone=p.ZONE(b);zone.SetLayer(layer);zone.SetNet(nets['GND']);zone.SetLocalClearance(mm(.2));zone.SetPadConnection(p.ZONE_CONNECTION_FULL);zone.SetMinThickness(mm(.2))
    outline=zone.Outline();outline.NewOutline()
    for x,y in [(.35,.35),(21.65,.35),(21.65,19.65),(.35,19.65)]:outline.Append(mm(x),mm(y))
    b.Add(zone)
for x,y in [(1,7.5),(11,7.2),(20.5,7.1),(11,14.6),(17.5,13.5),(6.5,9.3),(20.5,16)]:via('GND',x,y)

for ref,(x,y) in {'U1':(5.9,14.35),'U2':(14,13),'C1':(7,7),'C2':(17.9,14.7),'C3':(17.9,8.2),'R1':(11.4,12.3),'S0':(7,2),'P1':(20.4,5.9),'P2':(3.5,18.0),'P3':(10.6,18.0),'P4':(20.4,8.4),'P5':(18,16.8)}.items():
    fps[ref].Reference().SetPosition(v(x,y));fps[ref].Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
text('2xAA',16,1.2,.8,p.B_SilkS)
text('開',.8,3.5,.8);text('關',9.8,6.9,.8)
text('開',4.46,5.3,.8,p.B_SilkS);text('關',9.54,5.3,.8,p.B_SilkS)
text('模式二',10,9.5,.85,p.B_SilkS)
text('電池',20.2,6.1,.8,p.B_SilkS);text('+',18.8,1.8,.8,p.B_SilkS);text('-',18.8,4.3,.8,p.B_SilkS)
text('SW1',3.5,18.9,.85,p.B_SilkS);text('SW2',10.6,18.9,.85,p.B_SilkS)
text('馬達',18,11.25,.85,p.B_SilkS)
for n,mark in [('1','V'),('2','UPDI'),('3','G')]:
    x,_=padpos('P5',n)
    text(mark,x,16.4,.8,p.B_SilkS)
text('22 x 20 mm  B',10,8,.85,p.B_SilkS)
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
    assert PARTS['S0'][2]=={'1':'BATT+','2':'VBAT','3':'S0_NC'}
    assert 1.99 < .510/(205e-6*1240) < 2.02
    for ref,(_,_,pins) in PARTS.items():
        actual={x.GetNumber():('S0_NC' if x.GetNetname()=='unconnected-(S0-Pad3)' else x.GetNetname().removeprefix('/')) for x in fps[ref].Pads() if x.GetNumber()}
        assert actual==pins,(ref,actual,pins)
    print('接腳及限流計算檢查通過')
check_design()
