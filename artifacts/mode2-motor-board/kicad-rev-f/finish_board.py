"""清除 DRC 指出的多餘線尾，改以正反接地鋪銅連接地網；之後必須重跑 DRC。"""
from pathlib import Path
import json
import pcbnew as p

ROOT=Path(__file__).resolve().parent
path=ROOT/'mode2-no-firmware.kicad_pcb'
b=p.LoadBoard(str(path))
report=json.loads((ROOT/'reports/drc.json').read_text(encoding='utf-8'))
dangling={item['uuid'] for problem in report['violations'] if problem['type']=='track_dangling' for item in problem['items']}
removed=[]
for item in list(b.GetTracks()):
    if item.m_Uuid.AsString() in dangling or item.GetNetname()=='/GND':
        removed.append(item.m_Uuid.AsString());b.Remove(item);item.thisown=False
# 此位置連接被訊號線包圍的 U2／C2 地銅區，其餘地網由鋪銅和穿孔焊盤相連。
t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(p.FromMM(15.3),p.FromMM(8.95)));t.SetWidth(p.FromMM(.6));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu)
t.SetNet(b.FindNet('/GND'));b.Add(t)
(ROOT/'reports/cleanup.json').write_text(json.dumps({'removed_items':len(removed),'ground_stitch_vias':1,'requires_new_drc':True},indent=2),encoding='utf-8')
b.BuildConnectivity();p.SaveBoard(str(path),b)
print('已整理地網，保留一個接地過孔；須重新填銅及檢查。')
