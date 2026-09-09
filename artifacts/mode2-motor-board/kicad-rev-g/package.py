"""只封裝已檢查的成品，排除未佈線板、試驗板和過期報告。"""
from pathlib import Path
import json, re, zipfile

ROOT=Path(__file__).resolve().parent
NAME='mode2-no-firmware'
report=json.loads((ROOT/'verification.json').read_text(encoding='utf-8'))
assert all(report[k]==0 for k in ('pcb_violations','unconnected_items','schematic_parity','right_angle_bends','back_components'))
files=[ROOT/(NAME+ext) for ext in ('.kicad_pro','.kicad_sch','.kicad_pcb')]
files += [ROOT/name for name in ('README.md','BOM.csv','Hardware.kicad_sym','fp-lib-table','sym-lib-table','blank.kicad_wks','parts.json','expected-nets.json','netlist.xml','erc.json','verification.json','export_and_check.ps1')]
files += list(ROOT.glob('*.py'))
files += list((ROOT/'BoardF.pretty').glob('*.kicad_mod'))
models=set(re.findall(r'\$\{KIPRJMOD\}/(models/[^\"]+)',(ROOT/(NAME+'.kicad_pcb')).read_text(encoding='utf-8')))
files += [ROOT/name for name in sorted(models)]
files += [ROOT/'reports'/name for name in ('drc.json','angles.json','drill-report.txt')]
files += [path for path in (ROOT/'exports').iterdir() if path.is_file() and path.name!='placement.png']
fabrication=sorted((ROOT/'fabrication').glob('*'))
files+=fabrication
assert len(files)==len(set(files))
for filename,entries,prefix in [('mode2-kicad-rev-g.zip',files,ROOT),('mode2-gerbers-rev-g.zip',fabrication,ROOT/'fabrication')]:
    destination=ROOT.parent/filename
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in entries:
            assert path.is_file(),path
            archive.write(path,path.relative_to(prefix).as_posix())
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        for path in entries:
            assert archive.read(path.relative_to(prefix).as_posix())==path.read_bytes()
    print(filename,destination.stat().st_size,'bytes;',len(entries),'files; verified')
