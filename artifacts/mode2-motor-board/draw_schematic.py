from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
W, H, S = 1800, 1160, 2
im = Image.new('RGB', (W * S, H * S), 'white')
d = ImageDraw.Draw(im)
ink, power, signal, muted = '#25313d', '#b64936', '#236c85', '#657382'
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="white"/>']

def line(points, color=ink, width=2.5):
    d.line([(int(x*S), int(y*S)) for x, y in points], fill=color, width=round(width*S))
    coords = ' '.join(f'{x},{y}' for x, y in points)
    svg.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>')

def rect(x, y, w, h, fill='white', color=ink):
    d.rectangle((x*S, y*S, (x+w)*S, (y+h)*S), fill=fill, outline=color, width=4)
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{color}" stroke-width="2"/>')

def circle(x, y, r, fill='white', color=ink):
    d.ellipse(((x-r)*S, (y-r)*S, (x+r)*S, (y+r)*S), fill=fill, outline=color, width=4)
    svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{color}" stroke-width="2"/>')

def txt(x, y, value, size=23, color=ink, anchor='start', bold=False):
    font = ImageFont.truetype('C:/Windows/Fonts/msjhbd.ttc' if bold else 'C:/Windows/Fonts/msjh.ttc', size*S)
    a = {'start':'ls', 'middle':'ms', 'end':'rs'}[anchor]
    d.text((x*S, y*S), value, font=font, fill=color, anchor=a)
    svg.append(f'<text x="{x}" y="{y}" font-family="Microsoft JhengHei,sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{700 if bold else 400}">{escape(value)}</text>')

def dot(x, y, color=ink):
    circle(x, y, 4, color, color)

def ground(x, y):
    line([(x, y), (x, y+10)])
    for dy, hw in [(10, 15), (17, 10), (24, 5)]:
        line([(x-hw, y+dy), (x+hw, y+dy)])

def cap(x, top, bottom, name, value, label_side=1, polarized=False):
    mid = (top+bottom)/2
    line([(x, top), (x, mid-7)])
    line([(x-18, mid-7), (x+18, mid-7)])
    line([(x-18, mid+7), (x+18, mid+7)])
    line([(x, mid+7), (x, bottom)])
    tx = x + 32*label_side
    a = 'start' if label_side > 0 else 'end'
    txt(tx, mid-6, name, 21, anchor=a, bold=True)
    txt(tx, mid+24, value, 21, anchor=a)
    if polarized:
        txt(x-29, mid-19, '+', 22, power)

txt(60, 74, '模式二固定版｜最少元件接線草圖', 38, bold=True)
txt(60, 118, '2 粒 AA 串聯 · Tamiya FA-130 · 兩個機械微動開關 · 無 J1、無 LED', 25, muted)
line([(60, 145), (1740, 145)], '#dce3e8', 1.5)

# 電池與電源開關。
txt(60, 205, '電池 +', 24, power)
line([(155,210), (220,210)], power)
circle(220,210,4, color=power)
circle(290,210,4, color=power)
line([(220,210), (282,190)], power)
line([(290,210), (1360,210)], power, 3)
txt(253, 177, 'S0 電源開關', 21, anchor='middle')
txt(1400, 218, 'VBAT 約 2.4–3.0 V（標稱）', 23, power)
txt(60, 284, '電池 -', 24)
line([(155,280), (195,280), (195,302)])
ground(195,302)
txt(240, 303, '所有 GND 相連', 21, muted)

# 獨立去耦及儲能電容。
for x, name, value, side, pol in [(470,'C1','100 nF',1,False), (930,'C2','100 nF',1,False), (1360,'C3','100 µF / 6.3 V',1,True)]:
    dot(x,210,power)
    line([(x,210), (x,250)], power)
    cap(x,250,320,name,value,side,pol)
    ground(x,320)
txt(470, 378, '靠近 U1', 19, muted, 'middle')
txt(930, 378, '靠近 U2', 19, muted, 'middle')
txt(1360, 378, '靠近 U2；容量為初值', 19, muted, 'middle')

# IC 符號採功能排列，數字按實際封裝接腳。
rect(460,410,310,330, '#f7fafb')
rect(990,410,310,330, '#f7fafb')
txt(615,450,'U1  ATtiny202',27,anchor='middle',bold=True)
txt(615,480,'SOIC-8 · 需燒錄程式',20,muted,'middle')
txt(1145,450,'U2  DRV8213DSG',25,anchor='middle',bold=True)
txt(1145,480,'WSON-8 · 2 × 2 mm',20,muted,'middle')
for x, label in [(660,'(1) VDD'), (1130,'(1) VM')]:
    dot(x,210,power)
    line([(x,210), (x,410)],power)
    txt(x+15,396,label,20,power)

for y, name, pin in [(530,'SW1','(2) PA6'), (630,'SW2','(3) PA7')]:
    line([(140,y), (210,y)])
    line([(140,y), (140,y+18)])
    ground(140,y+18)
    circle(210,y,4)
    circle(280,y,4)
    line([(210,y), (271,y-22)])
    line([(280,y), (460,y)],signal)
    txt(245,y-39,name+' 常開',23,anchor='middle',bold=True)
    txt(206,y+33,'COM',18,muted,'middle')
    txt(288,y+33,'NO',18,muted,'middle')
    txt(478,y+7,pin,22)
txt(210,699,'NC 不接',20,muted,'middle')

for y, label1, label2 in [(530,'PA1 (4)','(6) IN1'), (610,'PA2 (5)','(5) IN2')]:
    txt(752,y+7,label1,22,anchor='end')
    txt(1008,y+7,label2,22)
    line([(770,y), (990,y)],signal)
txt(880,509,'正反轉控制',19,signal,'middle')

txt(478,696,'(6) UPDI',21)
line([(320,690), (460,690)],signal)
circle(320,690,5,color=signal)
txt(303,733,'燒錄焊盤',20,muted,'middle')
txt(752,696,'PA3 (7)',21,anchor='end')
txt(1008,696,'(8) IPROPI',21)
line([(770,690), (990,690)],signal)
txt(880,669,'電流回讀',19,signal,'middle')
dot(870,690,signal)
line([(870,690), (870,765)])
rect(859,765,22,54)
line([(870,819), (870,832)])
ground(870,832)
txt(907,783,'R1',22,bold=True)
txt(907,814,'1.24 kΩ · 1%',22)
txt(870,891,'標稱限流約 2.0 A',22,anchor='middle',bold=True)

txt(660,726,'GND (8)',20,anchor='middle')
line([(660,740), (660,798)])
ground(660,798)
for x,label in [(1080,'GND (4)'), (1225,'GAINSEL (7)')]:
    txt(x,726,label,19,anchor='middle')
    line([(x,740), (x,798)])
    ground(x,798)
txt(1160,870,'裸露散熱焊盤也接 GND',20,muted,'middle')

# 馬達及端子旁的抑噪電容。
txt(1282,525,'OUT1 (2)',21,anchor='end')
txt(1282,605,'OUT2 (3)',21,anchor='end')
line([(1300,520), (1570,520), (1570,537)],signal,3)
line([(1300,600), (1360,600), (1360,630), (1570,630), (1570,613)],signal,3)
circle(1570,575,38,color=signal)
txt(1570,587,'M',32,signal,'middle')
txt(1570,459,'FA-130 馬達',25,anchor='middle',bold=True)
dot(1430,520,signal)
dot(1430,630,signal)
line([(1430,520), (1430,549)],signal)
line([(1412,549), (1448,549)],signal)
line([(1412,561), (1448,561)],signal)
line([(1430,561), (1430,630)],signal)
txt(1430,679,'C4 · 100 nF',22,anchor='middle')
txt(1505,724,'C4 焊在馬達端子旁',22,muted,'middle')
txt(1505,759,'馬達兩端都不可固定接 GND',20,muted,'middle')

txt(75,797,'燒錄只留 3 個接觸焊盤',22,bold=True)
for x,label,col in [(145,'VBAT',power),(285,'UPDI',signal),(425,'GND',ink)]:
    circle(x,841,9,color=col)
    txt(x,882,label,20,col,'middle')

line([(60,932), (1740,932)], '#dce3e8', 1.5)
txt(60,977,'板上核心：2 IC + 1 電阻 + 3 電容；另加 S0。開關及馬達以焊線連接。',24,bold=True)
txt(60,1017,'MCU 程式：內建上拉、接點防彈跳、模式二、停止後鎖定 3 秒；時脈不超過 5 MHz。',22)
txt(60,1057,'R1、C3 為原型初值，需驗證啟動、換向及溫升；限流不等於卡住後自動停機。',22)
txt(60,1114,'接線草圖 v1｜數字為實際接腳號，符號位置不代表封裝腳位｜尚未作 PCB 佈線或實機測試',20,muted)

svg.append('</svg>')
OUT.joinpath('mode2-simple-schematic.svg').write_text('\n'.join(svg),encoding='utf-8')
im.resize((W,H),Image.Resampling.LANCZOS).save(OUT/'mode2-simple-schematic.png')
print(OUT/'mode2-simple-schematic.png')
print('標稱限流：', 0.510/(205e-6*1240), 'A')
