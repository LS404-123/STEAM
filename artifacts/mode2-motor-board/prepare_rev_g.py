"""從已交付 F 版的來源建立 G 版；不複製舊製板檔或檢查報告。"""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parent
old=root/'kicad-rev-f'
new=root/'kicad-rev-g'
new.mkdir(exist_ok=True)
for source in old.iterdir():
    if source.suffix in ('.py','.ps1') or source.name in ('README.md','BOM.csv'):
        shutil.copy2(source,new/source.name)
for folder in ('BoardF.pretty','models'):
    shutil.copytree(old/folder,new/folder,dirs_exist_ok=True)
for folder in ('exports','reports','fabrication'):
    (new/folder).mkdir(exist_ok=True)

def edit(name,a,b):
    path=new/name
    text=path.read_text(encoding='utf-8')
    assert a in text,(name,a)
    path.write_text(text.replace(a,b),encoding='utf-8')

edit('build_schematic.py','F 版','G 版')
edit('build_schematic.py','F 原型','G 原型')
edit('build_board.py','28×28mm','40×40mm')
path=new/'build_board.py'
text=path.read_text(encoding='utf-8')
a=text.index('positions={');z=text.index('\nfps={}',a)
text=text[:a]+'''positions={
 'S0':(10,5,0),'C4':(30,13,90),'P1':(36.6,5.3,90),
 'P4':(36.6,18,90),'P2':(6,36.5,0),'P3':(16,36.5,0),
 'U1':(7.5,20,0),'U2':(20,20,0),'U3':(31,20,180),
 'C1':(7.5,14.5,0),'C2':(20,14.5,0),'C3':(31,23,0),
 'R1':(6,29,0),'R2':(18,29,0),
 'R3':(12.5,18,90),'R4':(12.5,26,90),
 'C5':(12.5,15,90),'C6':(12.5,23,90),
 'R5':(24,33,90),'C7':(28,33,90),'D1':(27,28,0),
 'R6':(21,6,90),
}'''+text[z:]
text=text.replace('((0,0),(28,0)),((28,0),(28,28)),((28,28),(0,28)),((0,28),(0,0))','((0,0),(40,0)),((40,0),(40,40)),((40,40),(0,40)),((0,40),(0,0))')
a=text.index("text('MODE 2 / F'");z=text.index('b.BuildConnectivity()',a)
text=text[:a]+'''# 正面及背面均標示接口；元件位號放在附近空白區。
for layer in (p.F_SilkS,p.B_SilkS):
    text('MODE 2 / G',10,11,1,layer)
    text('ON',5.3,1,.85,layer);text('OFF',14.7,1,.85,layer)
    text('BAT 2xAA',34.8,8.4,.85,layer)
    text('+',32.6,5.3,1,layer);text('-',32.6,2.76,1,layer)
    text('MOTOR',36,21.1,.85,layer)
    text('M1',32.4,18,.8,layer);text('M2',32.4,15.46,.8,layer)
    text('SW1',7.27,32.7,1,layer);text('SW2',17.27,32.7,1,layer)
    for x in (6,16):
        text('NO',x,39.1,.8,layer);text('COM',x+2.54,39.1,.8,layer)
    text('40 x 40 mm',32,37,1,layer)
for ref,x,y in [('U1',7.5,25.1),('U2',20,25.1),('U3',28.4,20),
                ('C1',7.5,13.2),('C2',20,13.2),('C3',31,24.4),
                ('C4',30,9.5),('R1',6,27.6),('R2',18,27.6),
                ('R3',14.2,18),('R4',14.2,26),('C5',14.2,15),
                ('C6',14.2,23),('R5',24,30.8),('C7',28,30.8),
                ('D1',27,26.7),('R6',23.4,6),('S0',18,5)]:
    text(ref,x,y,.8,p.F_SilkS)
'''+text[z:]
path.write_text(text,encoding='utf-8')
edit('route_board.py','N=561','N=801')
path=new/'route_board.py'
text=path.read_text(encoding='utf-8')
a=text.index('for key,(net,xy) in escape.items():')
text=text[:a]+'''# 與 F 版保持同方向封裝，將引出線隨 U3 平移。
escape={key:(net,[(round(x+9.3,4),round(y+1,4)) for x,y in xy])
        for key,(net,xy) in escape.items()}
'''+text[a:]
text=text.replace("'SW1','SW2','GND']","'SW1','SW2']")
text=text.replace('width=.6 if net','width=1.0 if net')
text=text.replace('(27.65,.35),(27.65,27.65),(.35,27.65)','(39.65,.35),(39.65,39.65),(.35,39.65)')
# 接地過孔先放置，讓後續訊號佈線保留間距。
a=text.index('failed=[]')
text=text[:a]+'''for x,y in [(3,12),(16,12),(24,12),(27,21),(33,24.5),(5,25),(17.5,25),(30,34)]:
    t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(mm(.6));t.SetDrill(mm(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(*layers);t.SetNet(netobjects['GND']);b.Add(t)
    vias.append(('GND',x,y))

'''+text[a:]
path.write_text(text,encoding='utf-8')
edit('verify_design.py','dimensions==[28.0,28.0]','dimensions==[40.0,40.0]')
edit('export_and_check.ps1','原理圖-F.pdf','原理圖-G.pdf')
edit('package.py','rev-f.zip','rev-g.zip')
print(new)
