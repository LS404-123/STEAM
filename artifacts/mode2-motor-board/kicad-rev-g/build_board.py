"""以本專案原理圖資料建立 40×40mm 正面裝配 PCB；封裝沿用已核對的 E1 庫。"""
from pathlib import Path
import json, re, shutil, uuid
import pcbnew as p

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'kicad-rev-e1'
KICAD=Path(r'C:/Users/LS404/AppData/Local/Programs/KiCad/10.0/share/kicad')
NAME='mode2-no-firmware'
LIB=ROOT/'BoardF.pretty'
for folder in (LIB,ROOT/'models',ROOT/'exports',ROOT/'reports',ROOT/'fabrication'):
    folder.mkdir(exist_ok=True)
mm=p.FromMM
v=lambda x,y:p.VECTOR2I(mm(x),mm(y))
q=lambda s:json.dumps(str(s),ensure_ascii=False)
uid=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'mode2-hardware-f/'+str(s)))

for name in ('R0603','C0603','CP5','KF128_2P','WSON8'):
    if not (LIB/(name+'.kicad_mod')).exists():
        shutil.copyfile(OLD/'Mode2.pretty'/(name+'.kicad_mod'),LIB/(name+'.kicad_mod'))
if (OLD/'models').exists():
    for source in (OLD/'models').iterdir():
        if source.is_file() and not (ROOT/'models'/source.name).exists():
            shutil.copyfile(source,ROOT/'models'/source.name)
for name,path in {
    'SOIC14':'Package_SO.pretty/SOIC-14_3.9x8.7mm_P1.27mm.kicad_mod',
    'SOD323':'Diode_SMD.pretty/D_SOD-323.kicad_mod',
    'R1206':'Resistor_SMD.pretty/R_1206_3216Metric.kicad_mod',
}.items():
    s=(KICAD/'footprints'/path).read_text(encoding='utf-8')
    for model in re.findall(r'\$\{KICAD10_3DMODEL_DIR\}/([^\"]+)',s):
        source=KICAD/'3dmodels'/model
        assert source.exists(),source
        shutil.copyfile(source,ROOT/'models'/source.name)
        s=s.replace('${KICAD10_3DMODEL_DIR}/'+model,'${KIPRJMOD}/models/'+source.name)
    s=re.sub(r'^\(footprint "[^"]+"','(footprint '+q(name),s,count=1)
    (LIB/(name+'.kicad_mod')).write_text(s,encoding='utf-8')

# C&K 原廠 1000 系列：C 型直插、4.70mm 腳距、1.85mm 成品孔。
s='(footprint "CK1101"(version 20241229)(generator "pcbnew")(layer "F.Cu")(attr through_hole)'
s+='(descr "C&K 1101M2S3CQE2; body 12.70x6.60; pitch 4.70; drill 1.85; 6A 28VDC silver contacts")'
for prop,val,y,layer in [('Reference','REF**',-4.3,'F.SilkS'),('Value','1101M2S3CQE2',4.3,'F.Fab')]:
    s+=f'(property "{prop}" "{val}"(at 0 {y})(layer "{layer}")(effects(font(size .8 .8)(thickness .12))))'
for n,x in [('1',-4.7),('2',0),('3',4.7)]:
    shape='rect' if n=='1' else 'circle'
    s+=f'(pad "{n}" thru_hole {shape}(at {x} 0)(size 2.6 2.6)(drill 1.85)(layers "*.Cu" "*.Mask"))'
for layer,dx,width in [('F.Fab',0,.1),('F.SilkS',.12,.12),('F.CrtYd',.3,.05)]:
    s+=f'(fp_rect(start {-6.35-dx} {-3.3-dx})(end {6.35+dx} {3.3+dx})(stroke(width {width})(type solid))(fill none)(layer "{layer}"))'
s+='(model "${KIPRJMOD}/models/CK1101-envelope.wrl"(offset(xyz 0 0 0))(scale(xyz 1 1 1))(rotate(xyz 0 0 0))))'
(LIB/'CK1101.kicad_mod').write_text(s,encoding='utf-8')
model=['#VRML V2.0 utf8']
def box(x,y,z,w,d,h,color):
    model.append(f'Transform {{ translation {x/2.54} {y/2.54} {z/2.54} children [Shape {{ appearance Appearance {{material Material {{diffuseColor {color}}}}} geometry Box {{size {w/2.54} {d/2.54} {h/2.54}}} }}] }}')
box(0,0,1,12.7,6.6,2,'.55 .12 .10')
box(0,0,4.175,12.7,6.6,4.35,'.65 .67 .69')
box(-1.205,0,8.89,3.86,3.86,5.08,'.08 .08 .08')
for x in (-4.7,0,4.7): box(x,0,-2.175,1.27,.76,6.35,'.72 .67 .42')
(ROOT/'models/CK1101-envelope.wrl').write_text('\n'.join(model),encoding='utf-8')
(ROOT/'fp-lib-table').write_text('(fp_lib_table\n  (version 7)\n  (lib (name "BoardF") (type "KiCad") (uri "${KIPRJMOD}/BoardF.pretty") (options "") (descr "F 版封裝"))\n)\n',encoding='utf-8')

parts=json.loads((ROOT/'parts.json').read_text(encoding='utf-8'))
b=p.BOARD(); b.SetCopperLayerCount(2)
ds=b.GetDesignSettings();ds.SetBoardThickness(mm(1.6))
ds.m_MinClearance=mm(.15);ds.m_TrackMinWidth=mm(.15)
ds.m_MinThroughDrill=mm(.2);ds.m_CopperEdgeClearance=mm(.3)
nets={}
for name in sorted({n for part in parts for n in part['pins'].values()}):
    n=p.NETINFO_ITEM(b,'/'+name);b.Add(n);nets[name]=n
nc={('U1','10'):'unconnected-(U1-5Y-Pad10)',('U1','12'):'unconnected-(U1-6Y-Pad12)',('U2','6'):'unconnected-(U2-1Q_n-Pad6)'}
for name in nc.values():
    n=p.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
positions={
 'S0':(10,5,0),'C4':(28,10,90),'P1':(36.6,5.3,90),
 'P4':(36.6,18,90),'P2':(6,36.5,0),'P3':(16,36.5,0),
 'U1':(7.5,20,0),'U2':(20,20,0),'U3':(31,20,180),
 'C1':(7.5,14.5,0),'C2':(20,14.5,0),'C3':(31,23,0),
 'R1':(6,29,0),'R2':(18,29,0),
 'R3':(12.5,18,90),'R4':(12.5,26,90),
 'C5':(12.5,15,90),'C6':(12.5,23,90),
 'R5':(24,33,90),'C7':(28,33,90),'D1':(27,28,0),
 'R6':(21,6,90),
}
fps={}
for part in parts:
    ref=part['ref'];name=part['footprint'].split(':')[1]
    f=p.FootprintLoad(str(LIB),name); assert f is not None,name
    f.SetReference(ref);f.SetValue(part['value']);f.SetFPID(p.LIB_ID('BoardF',name))
    x,y,angle=positions[ref];f.SetPosition(v(x,y));f.SetOrientationDegrees(angle)
    f.SetPath(p.KIID_PATH('/'+uid('sheet')+'/'+uid(ref)))
    for pad in f.Pads():
        n=part['pins'].get(pad.GetNumber(),nc.get((ref,pad.GetNumber())))
        if n:pad.SetNet(nets[n])
    f.Reference().SetVisible(False);f.Value().SetVisible(False)
    b.Add(f);fps[ref]=f
for a,z in [((0,0),(40,0)),((40,0),(40,40)),((40,40),(0,40)),((0,40),(0,0))]:
    e=p.PCB_SHAPE();e.SetShape(p.SHAPE_T_SEGMENT);e.SetStart(v(*a));e.SetEnd(v(*z));e.SetLayer(p.Edge_Cuts);e.SetWidth(mm(.05));b.Add(e)

# 絲印稍後依佈線、焊盤和實物可見位置安排；背面位號方便維修。
def text(s,x,y,size=.75,layer=p.B_SilkS,angle=0):
    size=max(size,.8)
    t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(mm(.12));t.SetLayer(layer)
    t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T))
    if layer==p.B_SilkS:t.SetMirrored(True)
    b.Add(t)
for ref,(x,y,_) in positions.items():
    if not ref.startswith('P') and ref!='S0':text(ref,x,y,.65)
# 正面及背面均標示接口；元件位號放在附近空白區。
for layer in (p.F_SilkS,p.B_SilkS):
    text('MODE 2 / G',10,11,1,layer)
    text('ON',5.3,1,.85,layer);text('OFF',14.7,1,.85,layer)
    text('BAT 2xAA',34.8,8.4,.85,layer)
    text('+',32.6,5.3,1,layer);text('-',32.6,2.76,1,layer)
    text('MOTOR',36,21.1,.85,layer)
    text('M1',31.8,18,.8,layer);text('M2',31.8,15.46,.8,layer)
    text('SW1',7.27,30.6,1,layer);text('SW2',17.27,30.6,1,layer)
    for x in (6,16):
        text('NO',x,32.2,.8,layer);text('COM',x+2.54,32.2,.8,layer)
    text('40 x 40 mm',32,37,1,layer)
for ref,x,y in [('U1',7.5,25.1),('U2',20,25.1),('U3',28.4,20),
                ('C1',7.5,13.2),('C2',20,13.2),('C3',31,24.4),
                ('C4',24,10),('R1',6,27.6),('R2',18,27.6),
                ('R3',14.2,18),('R4',14.2,26),('C5',14.2,15),
                ('C6',14.2,23),('R5',24,30.8),('C7',28,30.8),
                ('D1',27,26.2),('R6',23.4,6),('S0',18,5)]:
    text(ref,x,y,.8,p.F_SilkS)
b.BuildConnectivity()
p.SaveBoard(str(ROOT/'unrouted.kicad_pcb'),b)

project=json.loads((KICAD/'template/kicad.kicad_pro').read_text(encoding='utf-8'))
project['meta']['filename']=NAME+'.kicad_pro'
project['schematic']={'page_layout_descr_file':'${KIPRJMOD}/blank.kicad_wks'}
project['board']['design_settings']['rules']['min_hole_clearance']=.25
project['board']['design_settings']['rules']['min_clearance']=.2
project['net_settings']['classes']=[{'name':'Default','clearance':.2,'track_width':.25,'via_diameter':.6,'via_drill':.3,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':.2,'diff_pair_gap':.25,'diff_pair_via_gap':.25,'bus_width':12,'wire_width':6,'line_style':0}]
(ROOT/(NAME+'.kicad_pro')).write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'pad-positions.json').write_text(json.dumps({f.GetReference():[
 {'pin':a.GetNumber(),'net':a.GetNetname(),'xy':[round(p.ToMM(a.GetPosition().x),4),round(p.ToMM(a.GetPosition().y),4)],
  'size':[p.ToMM(a.GetSize().x),p.ToMM(a.GetSize().y)],'angle':a.GetOrientationDegrees()}
 for a in f.Pads()] for f in b.GetFootprints()},indent=2),encoding='utf-8')
print('已建立 40×40mm、22 零件的未佈線板。')
