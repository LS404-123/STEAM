from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from hashlib import sha256
import json
from pypdf import PdfReader

root=Path(__file__).parent
board=root.parent/'kicad-rev-e'
pdf=root/'模式二控制板E版使用與原理說明.pdf'
r=PdfReader(pdf)
assert len(r.pages)==11
assert all(len(p.extract_text().strip())>100 for p in r.pages)
check=json.loads((root/'qa/validation.json').read_text(encoding='utf-8'))
for name,digest in check['source_sha256'].items():
    assert sha256((board/name).read_bytes()).hexdigest()==digest
files={
    'PCB正面銅線.png':root/'assets/pcb-front-copper.png',
    'PCB背面銅線.png':root/'assets/pcb-back-copper.png',
    'PCB正面銅線.svg':root/'assets/pcb-front-copper.svg',
    'PCB背面銅線.svg':root/'assets/pcb-back-copper.svg',
    'PCB元件正面.png':board/'exports/pcb-top.png',
    'PCB三維預覽.png':board/'exports/pcb-3d.png',
    '完整原理圖.png':board/'exports/schematic-preview.png',
    '完整原理圖.pdf':board/'exports/mode2-schematic.pdf',
}
with ZipFile(root/'E版電路板高清圖包.zip','w',ZIP_DEFLATED) as z:
    for name,path in files.items():z.write(path,name)
    z.writestr('圖面說明.txt','E 版，25 × 24 mm，2026-09-09。\n圖面是 KiCad 輸出與 3D 渲染，不是實物照片。\n紅色是正面銅，藍色是背面銅；大片色塊包括 GND 鋪銅，白色是隔離區。\n背面圖已鏡像為從背面觀看，電池端子出現在左上。\n3D 模型部分細節為外形示意，不用作精密外殼干涉檢查。\n原理圖 PDF 可放大閱讀。這個圖包不能代替製造 Gerber。\n尚未製造、燒錄或實機驗證。\n')
check.update(pdf_pages=11,visual_review='已逐頁檢視 11 頁，無空白頁、孤立尾頁、文字或表格截斷；原理圖另附向量 PDF。',renderer='Word 原生 PDF 匯出及 Poppler PNG；內建 render_docx 因未提供 LibreOffice 無法執行。')
(root/'qa/validation.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
for path in [pdf,root/'模式二控制板E版使用與原理說明.docx',root/'E版電路板高清圖包.zip']:
    print(path.name,path.stat().st_size)
