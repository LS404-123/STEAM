"""從 G 版建立使用者指定 SS12D10G5 的 H 版；保留舊版檔案。"""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
src, dst = ROOT/'kicad-rev-g', ROOT/'kicad-rev-h'
assert not dst.exists(), 'H 版已存在，請直接修改 H 版，勿覆蓋。'
dst.mkdir()
for pattern in ('*.py', '*.ps1', '*.csv', '*.md', '*-lib-table'):
    for path in src.glob(pattern):
        shutil.copy2(path, dst/path.name)
for name in ('BoardF.pretty', 'models'):
    shutil.copytree(src/name, dst/name)
for name in ('exports', 'reports', 'fabrication', 'sources'):
    (dst/name).mkdir()
shutil.copy2(Path('C:/Users/LS404/AppData/Local/Temp/codex-clipboard-ea2dcc9e-f2b2-4242-838c-9075a54c3eee.png'), dst/'sources/S0-SS12D10G5-user.png')

for path in dst.iterdir():
    if path.suffix not in ('.py', '.ps1', '.csv', '.md'):
        continue
    s = path.read_text(encoding='utf-8-sig')
    for old, new in [('G 版','H 版'), ('G版','H版'), ('/ G','/ H'), ('原理圖-G','原理圖-H'),
                     ('schematic-g','schematic-h'), ('rev-g','rev-h'), ('G 原型','H 原型'),
                     ('2026-09-09','2026-09-10'), ('CK1101','SS12D10G5'), ('1101M2S3CQE2','SS12D10G5')]:
        s = s.replace(old, new)
    path.write_text(s, encoding='utf-8')

def edit(name, replacements):
    path = dst/name
    s = path.read_text(encoding='utf-8')
    for old, new in replacements:
        assert old in s, (name, old)
        s = s.replace(old, new)
    path.write_text(s, encoding='utf-8')

edit('build_board.py', [
    ('# C&K 原廠 1000 系列：C 型直插、4.70mm 腳距、1.85mm 成品孔。', '# 使用者指定商品圖：4.8mm 腳距、1.3×0.8mm 接腳；1.85mm 成品孔。\n# 商品圖明示手量誤差，實物腳距及接點方向仍須樣品確認。'),
    ('C&K SS12D10G5; body 12.70x6.60; pitch 4.70; drill 1.85; 6A 28VDC silver contacts', 'SS12D10G5 straight pin; user drawing 12.7x6.7; pitch 4.8; drill 1.85; marked 2A 125VAC; DC load unverified'),
    ("('1',-4.7),('2',0),('3',4.7)", "('1',-4.8),('2',0),('3',4.8)"),
    ('{-3.3-dx}', '{-3.35-dx}'), ('{3.3+dx}', '{3.35+dx}'),
    ("box(0,0,1,12.7,6.6,2,'.55 .12 .10')", "box(0,0,.8,12.7,6.7,1.6,'.08 .08 .08')"),
    ("box(0,0,4.175,12.7,6.6,4.35,'.65 .67 .69')", "box(0,0,3.95,12.7,6.7,4.7,'.65 .67 .69')"),
    ("box(-1.205,0,8.89,3.86,3.86,5.08,'.08 .08 .08')", "box(-1.1,0,8.8,3.9,3.9,5,'.08 .08 .08')"),
    ("for x in (-4.7,0,4.7): box(x,0,-2.175,1.27,.76,6.35,'.72 .67 .42')", "for x in (-4.8,0,4.8): box(x,0,-3.45,1.3,.8,6.9,'.72 .72 .74')"),
    ("text('ON',5.3", "text('ON',5.2"), ("text('OFF',14.7", "text('OFF',14.8"),
])
edit('build_schematic.py', [
    ('S0：1–2 開；2–3 關。C&K SS12D10G5，銀接點 6A／28V DC，PCB 直插。', 'S0：1–2 開；2–3 關。SS12D10G5 直腳，腳距 4.8mm；商品標示 2A／125V AC。'),
    ('不能沿用 E1 的 50mA MSK12C02。R6 在關機時放掉電源電容電荷；D1 加快復位。', '依使用者商品圖重繪；DC 馬達負載、實物腳距及撥向待驗證。R6 關機放電；D1 加快復位。'),
])
edit('verify_design.py', [
    ("switchpads[0].GetPosition().x),4.7)", "switchpads[0].GetPosition().x),4.8)\nassert math.isclose(p.ToMM(switchpads[2].GetPosition().x-switchpads[1].GetPosition().x),4.8)\nassert fps['S0'].GetValue()=='SS12D10G5'"),
    ('尚未實機測試。商品圖片不代表即時庫存。', '尚未實機測試；S0 依使用者商品圖，標示 2A/125VAC；DC 馬達負載、腳距及撥向待樣品驗證。商品圖片不代表即時庫存。'),
])
edit('BOM.csv', [('S0,1,C&K SS12D10G5,直插 SPDT；腳距4.70mm；孔徑1.85mm,正面,銀接點6A／28V DC；不得混用焊耳 Z 或直角 A 版本', 'S0,1,SS12D10G5 直腳（使用者指定）,直插 SPDT；腳距4.80mm；孔徑1.85mm,正面,商品標示2A／125V AC；DC負載及實物腳距待驗證；非D06彎腳')])
edit('build_manual.py', [
    ('S0：C&K SS12D10G5，PCB 直插型、4.70mm 腳距。', 'S0：SS12D10G5 直腳型，依商品图採用 4.80mm 腳距、1.85mm 孔徑。'),
    ('S0 使用大電流開關，沒有 Q1；本版沒有降低它的採購成本。替代開關必須先核對尺寸、腳位及 DC 電流額定。商品圖片不能保證庫存。', 'S0 改用使用者指定款，商品標示 2A／125V AC；未驗證 DC 馬達負載。商品圖註明手量誤差，量產前須實測腳距及 ON／OFF 接點方向。'),
    ('<link href="https://www.ckswitches.com/media/1429/1000.pdf" color="#007F82">S0 圖面</link>', 'S0：使用者提供商品圖（隨包 sources/）'),
    ('商品图', '商品圖'),
])
edit('package.py', [("files+=fabrication", "files+=fabrication\nfiles+=list((ROOT/'sources').glob('*'))")])

# 新版只附實際使用的開關封裝；舊 G 版完全保留。
(dst/'BoardF.pretty/CK1101.kicad_mod').unlink()
print(dst)
