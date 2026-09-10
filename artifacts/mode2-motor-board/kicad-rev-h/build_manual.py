"""從 H 版原生 KiCad 圖像及檢查結果輸出使用手冊；無 R/C 計算。"""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader, PdfWriter

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'exports'
QA=ROOT/'reports/manual-qa'
QA.mkdir(exist_ok=True)
report=json.loads((ROOT/'verification.json').read_text(encoding='utf-8'))
assert report['board_mm']==[40.0,40.0]
assert not any(report[k] for k in ('pcb_violations','unconnected_items','schematic_parity','right_angle_bends'))
pdfmetrics.registerFont(TTFont('JH','C:/Windows/Fonts/msjh.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('JHB','C:/Windows/Fonts/msjhbd.ttc',subfontIndex=0))
pdfmetrics.registerFontFamily('JH',normal='JH',bold='JHB')
NAVY=colors.HexColor('#183047');TEAL=colors.HexColor('#007F82')
GRAY=colors.HexColor('#596B78');PALE=colors.HexColor('#EAF4F3')
W,H=A4; LEFT=18*mm; WIDTH=W-2*LEFT
c=canvas.Canvas(str(QA/'manual-pages.pdf'),pagesize=A4)
c.setTitle('模式二馬達控制板 H 版使用手冊｜40 × 40 mm')
c.setAuthor('模式二控制板專案')
page=0

def para(text,x,y,w=WIDTH,size=10.5,color=NAVY,bold=False):
    style=ParagraphStyle('body',fontName='JHB' if bold else 'JH',fontSize=size,
                         leading=size*1.55,textColor=color,wordWrap='CJK')
    p=Paragraph(text,style);_,height=p.wrap(w,H)
    assert y-height>=17*mm,(page,text,y-height)
    p.drawOn(c,x,y-height)
    return y-height

def start(title,subtitle):
    global page
    if page:c.showPage()
    page+=1
    c.setFillColor(TEAL);c.rect(LEFT,H-21*mm,13*mm,2*mm,fill=1,stroke=0)
    para('MODE 2  /  H',LEFT+17*mm,H-16.5*mm,60*mm,9,GRAY)
    para(title,LEFT,H-31*mm,WIDTH,22,NAVY,True)
    para(subtitle,LEFT,H-44*mm,WIDTH,10,GRAY)
    c.setStrokeColor(colors.HexColor('#D7E2E7'));c.line(LEFT,17*mm,W-LEFT,17*mm)
    c.setFillColor(GRAY);c.setFont('JH',8)
    c.drawString(LEFT,11*mm,'H 版 · 2026-09-10 · 設計原型，尚未實機測試')
    c.drawRightString(W-LEFT,11*mm,f'{page} / 7')
    return H-58*mm

def picture(name,x,top,w,h):
    image=ImageReader(str(OUT/name));iw,ih=image.getSize()
    scale=min(w/iw,h/ih);dw,dh=iw*scale,ih*scale
    c.drawImage(image,x+(w-dw)/2,top-dh,width=dw,height=dh,mask='auto')
    return top-dh

def table(headers,rows,widths,y,size=10):
    style=ParagraphStyle('cell',fontName='JH',fontSize=size,leading=size*1.5,wordWrap='CJK',textColor=NAVY)
    head=ParagraphStyle('head',parent=style,fontName='JHB',textColor=colors.white)
    data=[[Paragraph(str(t),head if i==0 else style) for t in row] for i,row in enumerate([headers]+rows)]
    t=Table(data,colWidths=[w*mm for w in widths],hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[PALE,colors.white]),
                         ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
                         ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    _,h=t.wrap(WIDTH,H);assert y-h>19*mm,(page,y-h)
    t.drawOn(c,LEFT,y-h)
    return y-h-6*mm

def sub(text,y):
    return para(text,LEFT,y,WIDTH,12,TEAL,True)-3*mm

y=start('模式二馬達控制板','使用手冊 · 40 × 40 mm · 2 粒 AA · 免燒錄')
y=picture('PCB-3D.png',LEFT,y,WIDTH,109*mm)-3*mm
y=para('SW1 正轉 → SW2 反轉 → SW1 停止',LEFT,y,WIDTH,17,TEAL,True)-7*mm
y=table(['項目','本版配置'],[
    ['板體','一塊 PCB；40 × 40 mm，厚 1.6 mm；正反面銅線，全部零件裝正面。'],
    ['接線','四組螺絲端子：電池、馬達、SW1、SW2；S0 電源開關裝在板上。'],
    ['控制','沒有 MCU、程式、LED、模式跳線或 Q1；停止後可立即重新操作。'],
    ['馬達','Tamiya 980112M Mabuchi FA-130；只使用兩粒 AA 串聯。'],
],[26,148],y)
para('圖為 KiCad 3D 示意，並非已製成的實物照片。端子、S0 和 U3 使用尺寸外形模型。',LEFT,y,WIDTH,9,GRAY)

y=start('01  接線與首次啟動','接線前，把 S0 撥到 OFF 並取出電池。')
y=picture('PCB正面.png',LEFT,y,WIDTH,94*mm)-3*mm
y=para('方向基準：零件面朝上，S0 大開關在左上角。右側端子的線從板右邊插入，下方端子的線從板下邊插入。',LEFT,y,WIDTH,10)-5*mm
y=table(['接口','位置與接法'],[
    ['P1／BAT','右上：上孔接電池負極（黑），下孔接正極（紅）。兩粒 AA 串聯。'],
    ['P4／MOTOR','右側中間：上孔 M2，下孔 M1。馬達方向與預期相反時，關電後交換兩線。'],
    ['P2／SW1','左下：左孔 NO，右孔 COM。接第一個帶線機械微動開關。'],
    ['P3／SW2','下方中間：左孔 NO，右孔 COM。接第二個帶線機械微動開關。'],
],[29,145],y,9.5)
y=para('微動開關使用 COM 和 NO，NC 不接。不要只靠線色判斷接點；未按下時兩線不通，按下時導通。開關的兩線對調不影響功能。',LEFT,y,WIDTH,10)-3*mm
para('將線頭插入端子的夾線孔，再鎖緊螺絲，輕拉確認不鬆脫；不可留下跨接相鄰端子的散銅絲。',LEFT,y,WIDTH,10)

y=start('02  操作方法','每次按下後放開；一次只按一個開關。')
y=sub('第一次使用',y)
for text in ['1. 接好電池盒、馬達及兩個微動開關，確認 BAT 正負極。',
             '2. 在馬達兩端焊接板外 C8（100nF 陶瓷電容）；它跨接兩端，不接 GND。',
             '3. 放開 SW1 和 SW2，再裝入兩粒 AA，把 S0 撥到 ON。馬達應保持停止。',
             '4. 按 SW1，馬達正轉；放開後繼續轉。',
             '5. 按 SW2，馬達反轉；放開後繼續轉。',
             '6. 再按 SW1，馬達停止。放開再按 SW1，即可重新正轉。']:
    y=para(text,LEFT,y)-3*mm
y-=4*mm
y=table(['目前狀態','按 SW1','按 SW2'],[
    ['停止','開始正轉','保持停止'],['正轉','保持正轉','改為反轉'],['反轉','停止','保持反轉']
],[40,67,67],y)
y=sub('使用時留意',y)
y=para('沒有三秒鎖定，也沒有 LED 顯示。電源開關 S0 可直接關機。兩個開關同時按下的結果未定義，請依上述次序操作。',LEFT,y)-4*mm
para('「停止」是電路停止驅動；實際停下所需時間仍與馬達及機械負載有關，不是機械鎖住。',LEFT,y)

y=start('03  電路怎樣記住狀態','U1 整理按鍵訊號；U2 記住狀態；U3 把電力送到馬達。')
y=table(['部件','作用'],[
    ['U1<br/>SN74HC14DR','配合 R1–R4、C5、C6，減少微動開關接點彈跳造成的重複觸發；也整理上電復位訊號。'],
    ['U2<br/>SN74HC74DR','內有兩個 D 觸發器，分別保存 RUN（是否運轉）與 REV（是否反轉）。不需要輸入程式。'],
    ['U3<br/>DRV8212DSGR','接收 RUN／REV，內部 H 橋切換馬達兩端電壓，產生正轉、反轉及停止。'],
],[44,130],y)
y=sub('三個狀態',y)
y=table(['動作後','RUN','REV','馬達'],[
    ['上電／停止','0','0','停止'],['按 SW1','1','0','正轉'],['再按 SW2','1','1','反轉'],['再按 SW1','0','0','停止']
],[74,23,23,54],y)
y=para('SW1 觸發時，U2 把「REV 的相反值」存入 RUN。因此尚未反轉時 SW1 會啟動；已反轉時 SW1 會停止。SW2 則把 RUN 存入 REV，所以停機時按 SW2 不會啟動。RUN 變成 0 時也會清除 REV。',LEFT,y)-5*mm
y=sub('其他小零件',y)
para('C1–C3：各晶片的電源去耦。C4：緩衝電源波動。R5、C7、D1：上電復位。R6：關機時放掉電源電容的電荷。C8：靠近馬達抑制電刷干擾。本手冊不列 R／C 計算。',LEFT,y)

y=start('04  PCB 走線與尺寸','以下正、背面均為 KiCad 成品走線圖；背面圖是從板背觀看。')
picture('pcb-traces-front.png',LEFT,y,83*mm,83*mm)
picture('pcb-traces-back.png',LEFT+91*mm,y,83*mm,83*mm)
y-=87*mm
para('正面銅線與絲印',LEFT,y,83*mm,10,TEAL,True)
para('背面銅線與絲印',LEFT+91*mm,y,83*mm,10,TEAL,True)
y-=14*mm
y=table(['比較','G 版','H 版（本版）'],[
    ['PCB 長 × 闊','40 × 40 mm','40 × 40 mm'],
    ['S0 電源開關','C&K 1101 系列','SS12D10G5 直腳'],
    ['S0 腳距','4.70 mm','4.80 mm'],
    ['零件／操作','22 個正面零件','同樣 22 個；操作相同'],
],[54,54,66],y,9.5)
y=para('圖中紅／藍色是銅箔，包含接地鋪銅；白色是無銅空隙。H 版更換 S0 封裝及附近走線，其餘零件型號、數值與操作流程沿用 G 版。',LEFT,y)-4*mm
y=para('WSON 晶片短引出線為 0.20 mm，一般訊號線 0.25 mm；正反面以過孔相連，這仍是一塊板。走線轉彎已檢查，沒有 90° 轉彎；焊盤內接合及 T 形分支另計。',LEFT,y)-4*mm
para('電源及馬達主幹維持 1.00 mm。開關模型是依商品圖建立的外形示意，並非原廠精密模型；實物尺寸及直流負載仍待驗證。',LEFT,y,WIDTH,10,GRAY)

y=start('05  裝配、檢查與檔案','製板及裝配請使用整套 H 版資料，不要混用舊版本的製板檔。')
y=sub('給裝配店的重點',y)
y=para('U1／U2：SOIC-14 的 SN74HC14DR／SN74HC74DR。U3：DRV8212DSGR，WSON-8，底部散熱焊盤必須焊接；適合交由貼片店回流焊。',LEFT,y)-3*mm
y=para('S0：SS12D10G5 直腳型，依商品圖採用 4.80mm 腳距、1.85mm 孔徑。四組端子：KEFA KF128-2.54-2P，2.54mm 腳距。C4 正極朝板下方，D1 色帶端朝左。完整物料表見 BOM.csv。',LEFT,y)-3*mm
y=para('S0 改用使用者指定款，商品標示 2A／125V AC；未驗證 DC 馬達負載。商品圖註明手量誤差，量產前須實測腳距及 ON／OFF 接點方向。',LEFT,y)-5*mm
y=table(['現象','先檢查'],[
    ['完全不動','S0 是否 ON、電池方向及電量、端子是否夾緊；負載下電源須維持至少 2V。'],
    ['按鍵沒有反應','開關是否接 COM／NO；是否放開後再按；是否處於該按鍵不改變狀態的階段。'],
    ['正反方向相反','關機後交換 MOTOR 的兩條線。'],
    ['啟動時重置／不穩','電池接觸、電壓下降、馬達卡住、C8 及焊接；先停止測試再排查。'],
],[43,131],y,9.3)
y=sub('已完成與仍待測試',y)
y=para(f"ERC／DRC 均為 0 違規；0 漏接；0 原理圖一致性問題。已核對 81 個接腳連接、1,024 組按鍵順序及 28 個指定 RC 情境。一般過孔共 {report['vias']} 個，另有 U3 的兩個 0.20mm 散熱孔。",LEFT,y,WIDTH,9.5)-3*mm
y=para('尚未實機測試馬達啟動、反轉、溫升及不同微動開關的彈跳。沒有額外固定 0.8A 限流；U3 的內建保護不能當作精確限流器。不要故意卡住馬達。',LEFT,y,WIDTH,9.5)-4*mm
y=para('KiCad：解壓完整專案 → 開啟 .kicad_pro → PCB 編輯器 → Alt＋3。製板條件：FR-4、40 × 40 mm、2 層、1.6 mm、1oz 銅；表面處理請由貼片店確認。第 7 頁為可放大的 A3 原理圖。',LEFT,y,WIDTH,9.5)-3*mm
para('原廠資料：<link href="https://www.ti.com/lit/ds/symlink/sn74hc14.pdf" color="#007F82">HC14</link> · <link href="https://www.ti.com/lit/ds/symlink/sn74hc74.pdf" color="#007F82">HC74</link> · <link href="https://www.ti.com/lit/ds/symlink/drv8212.pdf" color="#007F82">DRV8212</link> · S0：使用者提供商品圖（隨包 sources/） · <link href="https://www.ti.com/lit/an/slva959b/slva959b.pdf" color="#007F82">馬達驅動佈局指南</link>',LEFT,y,WIDTH,9,GRAY)
c.save()
assert page==6
writer=PdfWriter()
writer.append(str(QA/'manual-pages.pdf'))
writer.append(str(OUT/'原理圖-H.pdf'))
writer.add_metadata({'/Title':'模式二馬達控制板 H 版使用手冊 - 40 × 40 mm','/Author':'模式二控制板專案'})
destination=OUT/'模式二控制板H版使用手冊.pdf'
with destination.open('wb') as stream:writer.write(stream)
reader=PdfReader(destination)
assert len(reader.pages)==7
content='\n'.join(p.extract_text() or '' for p in reader.pages)
assert 'MODE 2 / G' not in content and '1101M2S3CQE2' not in content
for required in ('40 × 40','SS12D10G5','4.80','SN74HC14DR','SN74HC74DR','DRV8212DSGR','COM','NO','SW1','SW2','尚未實機測試'):
    assert required in content,required
(QA/'text.txt').write_text(content,encoding='utf-8')
print(destination,'7 pages; text checks passed')
