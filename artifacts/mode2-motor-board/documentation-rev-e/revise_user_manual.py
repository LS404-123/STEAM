"""沿用既有文件的版式與圖面，另存為純使用手冊。"""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree
from docx import Document
from docx.oxml.ns import qn

root = Path(__file__).parent
source = root/'模式二控制板E版使用與原理說明.docx'
output = root/'模式二控制板E版使用手冊.docx'
doc = Document(source)
body = doc.element.body
elements = list(body)
ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def text(el):
    return ''.join(el.xpath('.//w:t/text()', namespaces=ns)) if type(el) is etree._Element else ''.join(t.text or '' for t in el.iter(qn('w:t')))

def replace(el, value):
    nodes = list(el.iter(qn('w:t')))
    assert nodes, value
    nodes[0].text = value
    for node in nodes[1:]: node.text = ''

def paragraph(index, value):
    el = deepcopy(elements[index]); replace(el,value); return el

assert text(elements[33]).startswith('3  U1')
assert text(elements[80]).startswith('7  完整')
assert text(elements[100]).startswith('10  交給')
for el in elements[33:80] + elements[100:-1]: body.remove(el)

replacements = {
 9:'使用手冊',
 20:'只用 2 粒 AA 串聯。不要接 3 粒 AA、USB 5 V 或 9 V。馬達兩條線只接 P4，不要另接電池負極。',
 21:'本板目前是未製造、未實測的硬體原型，尚未提供控制程式；完成裝配及燒錄後，才可按本手冊操作。',
 27:'4. 確認馬達兩端已裝上板外抗干擾電容 C4，由裝配者按原理圖焊接。核對接線後，才放入 2 粒 AA。',
 32:'本手冊列出預定操作順序。控制程式尚未完成，其他按鍵順序及同時按下的反應尚未定義。停止是自由滑行，不會立即鎖住馬達軸。',
 80:'4  電路原理圖',
 83:'圖面用途',
 84:'原理圖供裝配、檢查和維修時參考。日常接線請看本手冊第 1 節的端子表；圖中的位置不代表元件在電路板上的實際位置。',
 85:'控制晶片接收 SW1／SW2 訊號，按操作順序指令馬達驅動器正轉、反轉和停止。使用者不需要調整板上的電阻或電容。',
 86:'圖下方的兩個微動開關、馬達及抗干擾電容屬板外部分。P5 是燒錄孔，不是日常接線端子。',
 88:'5  PCB 正面銅線圖',
 92:'這張圖隱藏了元件外形，方便查看走線。日常接線請按端子旁的文字與 +／− 標示核對，不要靠銅線顏色判斷電池極性。',
 94:'6  PCB 背面銅線圖',
 98:'背面的 NO／COM 是微動開關接點標示。接線時仍以元件正面的端子位置為準，並先取出電池。',
}
for index,value in replacements.items():replace(elements[index],value)
for node in elements[13].iter(qn('w:t')):
    if node.text == '接線、操作邏輯、U1／U2、R／C、原理圖及銅線圖':node.text='接線、操作、注意事項、常見問題與電路板圖面'

operating = elements[29].findall(qn('w:tr'))
for row,value in zip(operating,['馬達反應','保持停止，等待按下 SW1','開始正轉，放開 SW1 後仍繼續轉動','切換為反轉','停止驅動，馬達逐漸停下','3 秒內不回應開關，之後可再按 SW1 開始']):
    replace(row.findall(qn('w:tc'))[2],value)

faq = [paragraph(14,'3  使用注意事項與常見問題'),
 paragraph(15,'首次使用前，請裝配者確認接線、焊接和控制程式已完成，並示範一次完整的正轉、反轉、停止流程。'),
 paragraph(23,'日常使用'),
 paragraph(24,'• 更換電線或交換馬達方向前，先關機並取出電池盒內全部電池。'),
 paragraph(24,'• 不要把馬達軸卡住或長時間堵轉。若異常發熱或卡住，立即關機並取出電池。'),
 paragraph(24,'• 使用後關掉 S0；長時間不用時取出電池。'),
 paragraph(23,'出現以下情況時'),
]
faq_table = deepcopy(elements[18])
data = [
 ['情況','先檢查','處理方法'],
 ['開機後馬達不轉','是否尚未按下 SW1','開機等待屬預定行為；按下並放開 SW1'],
 ['按 SW1 仍沒有反應','電池、S0、夾線及是否完成燒錄','先斷電檢查；空白晶片不能操作'],
 ['方向與需要相反','馬達兩條線的接法','取出電池，再交換 P4 的兩條線'],
 ['停止後暫時按不到','是否仍在 3 秒鎖定期間','等 3 秒，放開開關後再按 SW1'],
]
for row,values in zip(faq_table.findall(qn('w:tr')),data):
    for cell,value in zip(row.findall(qn('w:tc')),values):replace(cell,value)
faq.append(faq_table)
faq.extend([
 paragraph(23,'委託賣家燒錄'),
 paragraph(15,'請先確認賣家支援 ATtiny202 的 UPDI 燒錄，並在交貨前測試本手冊的操作順序。目前尚未提供可燒錄的程式檔，單做 PCB 或焊接不會自動具備模式二功能。'),
 paragraph(20,'若由燒錄器供電，必須先取出電池盒內全部電池，不能只關掉 S0。'),
 paragraph(21,'本手冊的 3D 與電路板圖片是 KiCad 預覽，並非實物照片；部分元件模型為外形示意。'),
])
for el in faq:body.insert(body.index(elements[80]),el)

xml = etree.tostring(doc.element,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(source) as old, ZipFile(output,'w',ZIP_DEFLATED) as new:
    for name in old.namelist():
        data = old.read(name)
        if name == 'word/document.xml':data=xml
        elif name.startswith('word/footer') and name.endswith('.xml') or name=='docProps/core.xml':
            data=data.replace('使用與原理說明'.encode(),'使用手冊'.encode())
        new.writestr(name,data)

result=Document(output)
all_text='\n'.join(t.text or '' for t in result.element.iter(qn('w:t')))
assert len(result.inline_shapes)==5
assert not any(s in all_text for s in ['Δt','µA','÷','電阻值','如何決定下一步'])
assert '使用手冊' in all_text and '3 秒' in all_text
with ZipFile(source) as a,ZipFile(output) as b:
    assert all(a.read(n)==b.read(n) for n in a.namelist() if n not in ['word/document.xml','docProps/core.xml'] and not n.startswith('word/footer'))
print(output.name)
