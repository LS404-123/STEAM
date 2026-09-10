"""H 版 PCB 配套原理圖；免韌體，保持無 Q1。"""
from pathlib import Path
import json
import uuid

ROOT = Path(__file__).resolve().parent
NAME = 'mode2-no-firmware'
q = lambda s: json.dumps(str(s), ensure_ascii=False)
uid = lambda s: str(uuid.uuid5(uuid.NAMESPACE_URL, 'mode2-hardware-f/'+str(s)))
SID = uid('sheet')
snap = lambda v: round(round(v/1.27)*1.27, 4)
items, defs, pins, expected, bom = [], {}, {}, {}, []


def effects(size=1.1, justify=''):
    return f'(effects(font(face "Microsoft JhengHei")(size {size} {size})){justify})'


def line(a, b):
    a, b = tuple(round(v, 4) for v in a), tuple(round(v, 4) for v in b)
    items.append(f'(wire(pts(xy {a[0]} {a[1]})(xy {b[0]} {b[1]}))(stroke(width 0)(type default))(uuid {uid((a,b))}))')


def label(net, x, y):
    items.append(f'(label {q(net)}(at {x} {y} 0){effects(1.0,"(justify left bottom)")}(uuid {uid((net,x,y))}))')


def note(text, x, y, size=1.3):
    items.append(f'(text {q(text)}(at {x} {y} 0){effects(size,"(justify left top)")}(uuid {uid((text,x,y))}))')


def poly(points):
    return '(polyline(pts'+''.join(f'(xy {x} {y})' for x,y in points)+')(stroke(width .254)(type default))(fill(type none)))'


def define(name, entries, w=20, h=30, graphic=None):
    entries = [(n,label_,snap(x),snap(y),angle,kind) for n,label_,x,y,angle,kind in entries]
    w,h = snap(w),snap(h)
    pins[name] = entries
    graphic = graphic or f'(rectangle(start {-w} {h})(end {w} {-h})(stroke(width .254)(type default))(fill(type background)))'
    ps = ''.join(f'(pin {kind} line(at {x} {y} {angle})(length 2.54)(name {q(label_)} {effects(1.0)})(number {q(n)} {effects(.9)}))' for n,label_,x,y,angle,kind in entries)
    defs[name] = f'(symbol {q(name)}(pin_names(offset .8))(in_bom yes)(on_board yes)(property "Reference" "U"(at 0 0 0){effects()})(property "Value" {q(name)}(at 0 0 0){effects()})(symbol {q(name+"_0_1")} {graphic})(symbol {q(name+"_1_1")} {ps}))'


def put(ref, typ, x, y, nets, value=None, footprint='', prop=None, board=True):
    if board:
        name = ('SOIC14' if ref in ('U1','U2') else 'WSON8' if ref=='U3' else
                'SS12D10G5' if ref=='S0' else 'KF128_2P' if ref.startswith('P') else
                'SOD323' if ref=='D1' else 'R1206' if ref=='R6' else
                'R0603' if ref.startswith('R') else 'CP5' if ref=='C4' else 'C0603')
        footprint='BoardF:'+name
    x,y = snap(x),snap(y)
    expected[ref] = {str(n):net for n,net in nets.items() if net is not None}
    value = value or typ
    rx, ry = prop or (x+6,y-2)
    items.append(f'''(symbol(lib_id {q('Hardware:'+typ)})(at {x} {y} 0)(unit 1)(in_bom {'yes' if board else 'no'})(on_board {'yes' if board else 'no'})(dnp no)(uuid {uid(ref)})
      (property "Reference" {q(ref)}(at {rx} {ry} 0){effects(1.2)})
      (property "Value" {q(value)}(at {rx} {ry+2.6} 0){effects(1.0)})
      (property "Footprint" {q(footprint)}(at {x} {y} 0)(effects(font(size 1 1))(hide yes)))
      (instances(project {q(NAME)}(path {q('/'+SID)}(reference {q(ref)})(unit 1)))))''')
    for n,_,px,py,angle,_ in pins[typ]:
        ax, ay = round(x+px,4),round(y-py,4)
        net = nets[str(n)]
        if net is None:
            items.append(f'(no_connect(at {ax} {ay})(uuid {uid((ref,n,"NC"))}))')
            continue
        dx,dy = {0:(-7.62,0),180:(7.62,0),90:(0,5.08),270:(0,-5.08)}[angle]
        bx,by = round(ax+dx,4),round(ay+dy,4)
        line((ax,ay),(bx,by))
        label(net,bx,by)
    if board:
        bom.append(dict(ref=ref,value=value,footprint=footprint,pins=expected[ref]))


P='passive'; I='input'; O='output'; V='power_in'
define('HC14',[(1,'1A',-22.54,24,0,I),(2,'1Y',22.54,24,180,O),(3,'2A',-22.54,16,0,I),(4,'2Y',22.54,16,180,O),(5,'3A',-22.54,8,0,I),(6,'3Y',22.54,8,180,O),(9,'4A',-22.54,0,0,I),(8,'4Y',22.54,0,180,O),(11,'5A',-22.54,-8,0,I),(10,'5Y',22.54,-8,180,O),(13,'6A',-22.54,-16,0,I),(12,'6Y',22.54,-16,180,O),(14,'VCC',0,32.54,270,V),(7,'GND',0,-32.54,90,V)])
define('HC74',[(1,'1CLR_n',-22.54,28,0,I),(2,'1D',-22.54,20,0,I),(3,'1CLK',-22.54,12,0,I),(4,'1PRE_n',-22.54,4,0,I),(12,'2D',-22.54,-4,0,I),(11,'2CLK',-22.54,-12,0,I),(10,'2PRE_n',-22.54,-20,0,I),(13,'2CLR_n',-22.54,-28,0,I),(5,'1Q',22.54,20,180,O),(6,'1Q_n',22.54,12,180,O),(9,'2Q',22.54,-12,180,O),(8,'2Q_n',22.54,-20,180,O),(14,'VCC',0,38.54,270,V),(7,'GND',0,-38.54,90,V)],h=36)
define('DRV8212',[(6,'PH',-22.54,12,0,I),(5,'EN',-22.54,4,0,I),(7,'MODE',-22.54,-4,0,I),(8,'VCC',-22.54,-12,0,V),(1,'VM',0,24.54,270,V),(4,'GND',-5,-24.54,90,V),(9,'EP',5,-24.54,90,V),(2,'OUT1',22.54,8,180,O),(3,'OUT2',22.54,-4,180,O)],h=22)
define('R',[(1,'~',0,5.08,270,P),(2,'~',0,-5.08,90,P)],graphic='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))')
cg=poly([(-2.54,.762),(2.54,.762)])+poly([(-2.54,-.762),(2.54,-.762)])+poly([(0,2.54),(0,.762)])+poly([(0,-2.54),(0,-.762)])
define('C',[(1,'~',0,5.08,270,P),(2,'~',0,-5.08,90,P)],graphic=cg)
define('CP',[(1,'+',0,5.08,270,P),(2,'-',0,-5.08,90,P)],graphic=cg+poly([(-4,2.5),(-2.5,2.5)])+poly([(-3.25,1.75),(-3.25,3.25)]))
define('D',[(1,'K',5.08,0,180,P),(2,'A',-5.08,0,0,P)],graphic=poly([(-2.54,2.54),(-2.54,-2.54),(2.54,0),(-2.54,2.54)])+poly([(2.54,2.54),(2.54,-2.54)]))
define('Conn',[(1,'1',5.08,2.54,180,P),(2,'2',5.08,-2.54,180,P)],w=2.54,h=5.08)
define('SPDT',[(1,'ON',-7.62,5.08,0,P),(3,'OFF',-7.62,-5.08,0,P),(2,'COM',7.62,0,180,P)],graphic=poly([(-5.08,5.08),(-2.54,5.08)])+poly([(-5.08,-5.08),(-2.54,-5.08)])+poly([(5.08,0),(2.54,0),(-2,4)]))
define('SW',[(1,'NO',0,5.08,270,P),(2,'COM',0,-5.08,90,P)],graphic=poly([(0,2.54),(2,-2)]))
define('Motor',[(1,'M1',0,5.08,270,P),(2,'M2',0,-5.08,90,P)],graphic='(circle(center 0 0)(radius 2.54)(stroke(width .254)(type default))(fill(type none)))'+f'(text "M"(at 0 0 0){effects(2)})')
define('Flag',[(1,'PWR',0,2.54,270,'power_out')],graphic=poly([(-1.27,0),(0,1.27),(1.27,0),(-1.27,0)]))

note('模式二 H 版｜免燒錄硬體邏輯',15,13,3)
note('2 粒 AA · SW1 正轉 → SW2 反轉 → SW1 停止 · 取消 3 秒鎖定 · 無 LED／Q1／模式跳線',15,21,1.5)
note('① 電源、上電復位與去耦',15,31,1.7)
put('P1','Conn',22,46,{'1':'BATT+','2':'GND'},'電池螺絲端子',prop=(20,36))
put('S0','SPDT',73,47,{'1':'BATT+','2':'VCC','3':'DISCH'},'SS12D10G5',prop=(65,33))
put('R6','R',95,67,{'1':'DISCH','2':'GND'},'100R / 0.25W',prop=(105,64))
put('C4','CP',138,47,{'1':'VCC','2':'GND'},'100uF / 6.3V',prop=(149,44))
put('R5','R',189,47,{'1':'VCC','2':'POR_RC'},'100k',prop=(199,44))
put('C7','C',229,47,{'1':'POR_RC','2':'GND'},'100nF',prop=(239,44))
put('D1','D',200,72,{'1':'VCC','2':'POR_RC'},'BAT54WS',prop=(195,64))
for ref,x,near in [('C1',279,'U1'),('C2',325,'U2'),('C3',375,'U3')]:
    put(ref,'C',x,47,{'1':'VCC','2':'GND'},'100nF / 16V',prop=(x+10,44))
    note('靠近 '+near,x-4,63,1.0)
note('S0：1–2 開；2–3 關。SS12D10G5 直腳，腳距 4.8mm；商品標示 2A／125V AC。',15,83,1.1)
note('依使用者商品圖重繪；DC 馬達負載、實物腳距及撥向待驗證。R6 關機放電；D1 加快復位。',15,88,1.1)

note('② 消抖及復位整形',82,99,1.6)
put('U1','HC14',120,143,{'1':'DB1','2':'CLK1','3':'DB2','4':'CLK2','5':'POR_RC','6':'POR_INV','9':'POR_INV','8':'RESET_N','11':'GND','10':None,'13':'GND','12':None,'14':'VCC','7':'GND'},'SN74HC14DR',footprint='Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',prop=(109,104))
note('③ 記住運轉／方向',208,99,1.6)
put('U2','HC74',243,149,{'1':'RESET_N','2':'NOT_REV','3':'CLK1','4':'VCC','5':'RUN','6':None,'7':'GND','8':'NOT_REV','9':'REV','10':'VCC','11':'CLK2','12':'RUN','13':'RUN','14':'VCC'},'SN74HC74DR',footprint='Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',prop=(231,104))
note('④ 馬達驅動（PH/EN 模式）',313,99,1.6)
put('U3','DRV8212',348,139,{'1':'VCC','2':'M2','3':'M1','4':'GND','5':'RUN','6':'REV','7':'VCC','8':'VCC','9':'GND'},'DRV8212DSGR',footprint='Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm',prop=(337,106))
note('M1=OUT2；M2=OUT1。此接法令 REV=0 為正轉。\nMODE 固定接 VCC，不裝跳線。EP 必須接地。',310,179,1.1)

note('⑤ 微動開關接線及 RC 消抖',15,198,1.6)
for idx,x in [(1,30),(2,145)]:
    raw,db=f'SW{idx}',f'DB{idx}'
    put(f'P{idx+1}','Conn',x,222,{'1':raw,'2':'GND'},f'SW{idx} 螺絲端子',prop=(x-8,209))
    put(f'R{idx}','R',x+42,218,{'1':'VCC','2':raw},'100k',prop=(x+49,217))
    put(f'R{idx+2}','R',x+70,218,{'1':raw,'2':db},'1k',prop=(x+77,217))
    put(f'C{idx+4}','C',x+70,248,{'1':db,'2':'GND'},'220nF',prop=(x+77,247))
    put(f'S{idx}','SW',x+10,255,{'1':raw,'2':'GND'},f'SW{idx}（板外）',prop=(x+18,254),board=False)
note('每個微動開關接 COM、NO；NC 不接。按下接地，U1 輸出上升沿。',15,276,1.1)

put('P4','Conn',315,210,{'1':'M1','2':'M2'},'馬達螺絲端子',prop=(310,200))
put('M1','Motor',345,237,{'1':'M1','2':'M2'},'FA-130（板外）',prop=(314,237),board=False)
put('C8','C',390,237,{'1':'M1','2':'M2'},'100nF（板外）',prop=(365,251),board=False)
note('C8 直接跨接馬達兩端；不接地。',308,265,1.1)
note('停止時 RUN=0；按 SW1 → RUN=1、REV=0；按 SW2 → REV=1；再按 SW1 → RUN=REV=0。',15,283,1.15)
note('同名網絡標籤均相連；_N / NOT_ 表示反相信號。搭配 H 版 PCB；電路圖直角不代表銅線轉角。',15,288,1.05)
for ref,net,x in [('#FLG01','VCC',285),('#FLG02','GND',285),('#FLG03','BATT+',285)]:
    y={'VCC':219,'GND':239,'BATT+':259}[net]
    put(ref,'Flag',x,y,{'1':net},'PWR_FLAG',prop=(x-5,y+4),board=False)

embedded=''.join(s.replace('(symbol '+q(k),'(symbol '+q('Hardware:'+k),1) for k,s in defs.items())
(ROOT/(NAME+'.kicad_sch')).write_text(f'(kicad_sch(version 20250114)(generator "eeschema")(uuid {SID})(paper "A3")(title_block(title "免韌體模式二原理圖")(date "2026-09-10")(rev "H 原型"))(lib_symbols {embedded})'+''.join(items)+'(embedded_fonts no))',encoding='utf-8')
(ROOT/(NAME+'.kicad_pro')).write_text(json.dumps({'meta':{'filename':NAME+'.kicad_pro'},'schematic':{'page_layout_descr_file':'${KIPRJMOD}/blank.kicad_wks'}}),encoding='utf-8')
(ROOT/'blank.kicad_wks').write_text('(kicad_wks (version 20231118)(generator "pl_editor")(setup(textsize 1.5 1.5)(linewidth .15)(textlinewidth .15)(left_margin 10)(right_margin 10)(top_margin 10)(bottom_margin 10)))',encoding='utf-8')
(ROOT/'Hardware.kicad_sym').write_text('(kicad_symbol_lib(version 20241209)(generator "eeschema")'+''.join(defs.values())+')',encoding='utf-8')
(ROOT/'sym-lib-table').write_text('(sym_lib_table\n (version 7)\n (lib (name "Hardware") (type "KiCad") (uri "${KIPRJMOD}/Hardware.kicad_sym") (options "") (descr "免程式候選原理圖"))\n)\n',encoding='utf-8')
(ROOT/'expected-nets.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'parts.json').write_text(json.dumps(bom,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Created {NAME}.kicad_sch; {len(bom)} board components; no PCB created.')
