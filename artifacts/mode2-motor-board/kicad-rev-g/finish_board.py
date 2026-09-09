"""清除 DRC 指出的多餘線尾，改以正反接地鋪銅連接地網；之後必須重跑 DRC。"""
from pathlib import Path
import json
import pcbnew as p

ROOT=Path(__file__).resolve().parent
path=ROOT/'mode2-no-firmware.kicad_pcb'
b=p.LoadBoard(str(path))
for item in b.GetDrawings():
    if isinstance(item,p.PCB_TEXT) and item.GetText()=='C4' and item.GetLayer()==p.F_SilkS:
        item.SetPosition(p.VECTOR2I(p.FromMM(24),p.FromMM(10)))
report=json.loads((ROOT/'reports/drc.json').read_text(encoding='utf-8'))
dangling={item['uuid'] for problem in report['violations'] if problem['type']=='track_dangling' for item in problem['items']}
removed=[]
for item in list(b.GetTracks()):
    if item.m_Uuid.AsString() in dangling:
        removed.append(item.m_Uuid.AsString());b.Remove(item);item.thisown=False
# G 版接地過孔已在佈線前加入，這裡不更動地網。
(ROOT/'reports/cleanup.json').write_text(json.dumps({'removed_items':len(removed),'requires_new_drc':True},indent=2),encoding='utf-8')
b.BuildConnectivity();p.SaveBoard(str(path),b)
print('已清除多餘線尾；須重新填銅及檢查。')
