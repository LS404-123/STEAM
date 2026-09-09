"""讀取實際 KiCad 網表，再檢查接腳、狀態轉移及指定按鍵彈跳情境。"""
from pathlib import Path
from itertools import product
import json
import math
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
tree=ET.parse(ROOT/'netlist.xml')
actual={}
for net in tree.findall('./nets/net'):
    for node in net.findall('node'):
        actual[node.attrib['ref'],node.attrib['pin']]=net.attrib['name'].removeprefix('/')
expected=json.loads((ROOT/'expected-nets.json').read_text(encoding='utf-8'))
for ref, pins in expected.items():
    if ref.startswith('#'):
        continue
    for pin, name in pins.items():
        assert actual[ref,pin]==name,(ref,pin,name,actual.get((ref,pin)))

# 依資料表手工列出的 IC 接腳；獨立於原理圖產生器。
reference={
 'U1':{'1':'DB1','2':'CLK1','3':'DB2','4':'CLK2','5':'POR_RC','6':'POR_INV','9':'POR_INV','8':'RESET_N','11':'GND','13':'GND','14':'VCC','7':'GND'},
 'U2':{'1':'RESET_N','2':'NOT_REV','3':'CLK1','4':'VCC','5':'RUN','7':'GND','8':'NOT_REV','9':'REV','10':'VCC','11':'CLK2','12':'RUN','13':'RUN','14':'VCC'},
 'U3':{'1':'VCC','2':'M2','3':'M1','4':'GND','5':'RUN','6':'REV','7':'VCC','8':'VCC','9':'GND'},
 'S0':{'1':'BATT+','2':'VCC','3':'DISCH'},'R6':{'1':'DISCH','2':'GND'},
 'D1':{'1':'VCC','2':'POR_RC'},
}
for ref,pins in reference.items():
    assert {p:actual[ref,p] for p in pins}==pins

def edge(state, switch):
    run,rev=state
    signals={'RUN':run,'REV':rev,'NOT_REV':1-rev}
    clock_net=actual['U1','2' if switch==1 else '4']
    if clock_net==actual['U2','3']:
        run=signals[actual['U2','2']]
    if clock_net==actual['U2','11']:
        rev=signals[actual['U2','12']]
    if not run:  # U2.13 由 RUN 非同步清零。
        rev=0
    return run,rev

truth={((0,0),1):(1,0),((0,0),2):(0,0),((1,0),1):(1,0),((1,0),2):(1,1),((1,1),1):(0,0),((1,1),2):(1,1)}
for sequence in product((1,2),repeat=10):
    state=reference_state=(0,0)
    for switch in sequence:
        state=edge(state,switch)
        reference_state=truth[reference_state,switch]
        assert state==reference_state,(sequence,state,reference_state)

# U3 表 8-4：EN=1/PH=0 時 OUT2 高；本圖 M1=OUT2。
for state,result in [((0,0),'stop'),((1,0),'forward'),((1,1),'reverse')]:
    run,rev=state
    result_actual='stop' if not run else ('reverse' if rev else 'forward')
    assert result_actual==result

# 固定 2V、施密特有效門檻組合、R/C 容差角點；只檢查此 5ms 彈跳波形。
def bounce_edges(vp,vn,rscale,cscale):
    voltage,output,count=2.0,0,0
    waveform=[(1,.001),(0,.005),(1,.002),(0,.005),(1,.050),
              (0,.003),(1,.002),(0,.050)]
    for closed,duration in waveform:
        tau=(1000 if closed else 101000)*rscale*220e-9*cscale
        target=0 if closed else 2
        voltage=target+(voltage-target)*math.exp(-duration/tau)
        next_output=1 if voltage<=vn else (0 if voltage>=vp else output)
        count+=output==0 and next_output==1
        output=next_output
    return count,output

rc_checks=0
for vp,vn in product((.7,1.2,1.5),(.3,.6,1.0)):
    if not .2-1e-9<=vp-vn<=1.2+1e-9:
        continue
    for rs,cs in product((.99,1.01),(.9,1.1)):
        assert bounce_edges(vp,vn,rs,cs)==(1,0),(vp,vn,rs,cs)
        rc_checks+=1

erc=json.loads((ROOT/'erc.json').read_text(encoding='utf-8'))
assert not [v for sheet in erc['sheets'] for v in sheet['violations']], 'ERC violations remain'
report={'checked_pin_connections':sum(len(p) for r,p in expected.items() if not r.startswith('#')),
        'button_sequences':1024,'length_per_sequence':10,'rc_scenarios_2V':rc_checks,
        'erc_violations':0,'limits':'邏輯及指定 RC 波形模型；非 SPICE、非馬達瞬態／EMI／實機驗證；淘寶庫存未核實。'}
(ROOT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))

# 從實際 PCB 讀取，不以產生器預期值代替成品檢查。
import pcbnew as p
from check_angles import audit
board=p.LoadBoard(str(ROOT/'mode2-no-firmware.kicad_pcb'))
parts=json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))
fps={fp.GetReference():fp for fp in board.GetFootprints()}
assert set(fps)=={part['ref'] for part in parts}
assert len(fps)==22 and 'Q1' not in fps
assert board.GetCopperLayerCount()==2
assert all(fp.GetLayer()==p.F_Cu for fp in fps.values())
for part in parts:
    fp=fps[part['ref']]
    assert fp.GetValue()==part['value']
    for pad in fp.Pads():
        number=pad.GetNumber()
        if number in part['pins']:
            assert pad.GetNetname().removeprefix('/')==part['pins'][number],(part['ref'],number)
        elif number:
            assert pad.GetNetname().startswith('unconnected-')
    assert len(fp.Models())>0,part['ref']
    for model in fp.Models():
        assert Path(model.m_Filename.replace('${KIPRJMOD}',str(ROOT))).is_file(),model.m_Filename
for ref in ('P1','P2','P3','P4'):
    terminals=list(fps[ref].Pads())
    a,z=(pad.GetPosition() for pad in terminals)
    assert math.isclose(p.ToMM(math.hypot(a.x-z.x,a.y-z.y)),2.54,abs_tol=1e-6)
    assert all(math.isclose(p.ToMM(pad.GetDrillSize().x),1.3) for pad in terminals)
switchpads=sorted(fps['S0'].Pads(),key=lambda pad:pad.GetNumber())
assert all(math.isclose(p.ToMM(pad.GetDrillSize().x),1.85) for pad in switchpads)
assert math.isclose(p.ToMM(switchpads[1].GetPosition().x-switchpads[0].GetPosition().x),4.7)
edgepoints=[xy for shape in board.GetDrawings() if shape.GetLayer()==p.Edge_Cuts for xy in (shape.GetStart(),shape.GetEnd())]
dimensions=[p.ToMM(max(getattr(xy,k) for xy in edgepoints)-min(getattr(xy,k) for xy in edgepoints)) for k in ('x','y')]
assert dimensions==[40.0,40.0]
for net in ('/BATT+','/VCC','/M1','/M2'):
    widths=[p.ToMM(item.GetWidth()) for item in board.GetTracks()
            if type(item)==p.PCB_TRACK and item.GetNetname()==net]
    assert widths and math.isclose(max(widths),1.0),(net,widths)
drc=json.loads((ROOT/'reports/drc.json').read_text(encoding='utf-8'))
assert all(not drc[key] for key in ('violations','unconnected_items','schematic_parity'))
angles=audit(ROOT/'mode2-no-firmware.kicad_pcb')
assert not angles['right_angle_bends']
(ROOT/'reports/angles.json').write_text(json.dumps(angles,ensure_ascii=False,indent=2),encoding='utf-8')
report.update(board_mm=dimensions,board_components=len(fps),copper_layers=2,back_components=0,
              pcb_violations=0,unconnected_items=0,schematic_parity=0,right_angle_bends=0,
              vias=sum(type(item)==p.PCB_VIA for item in board.GetTracks()),
              tracks=sum(type(item)==p.PCB_TRACK for item in board.GetTracks()),
              limits='原理圖／PCB／指定邏輯與 RC 模型檢查；尚未實機測試。商品圖片不代表即時庫存。')
(ROOT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
