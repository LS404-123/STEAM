# 文件範本執行契約
來源：C:/Users/LS404/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-system-design/assets/reference.docx
SHA-256：13504f6c221a42c1726460a9e865e563355539ff97d702d6c9b2267b4b261d76
已以 Word 唯讀轉 PDF，檢視全部 7 頁；內建 render_docx 因缺少 LibreOffice 失敗。

## 版面與元件
單節，Letter 8.5 × 11 英吋直向；上左右邊界 0.7 英吋，下 893 twips。
頁首與頁尾距 0.5 英吋；首頁頁尾獨立，正文中央頁尾。
封面：document.xml 的 body 前 21 段及前兩表；36 pt 雙標題、三欄狀態、兩欄四列資訊。
正文：Heading 1 13.5 pt，段後 6.5 pt；正文 normal，原段後 5.5 pt、1.25 倍行距。
正文表格取來源第 5 表三欄模式，表頭 #082A4A 白字，內文 #233447，淺藍 #E5EFF7 與 #F5F8FA 底色。
以原表頭、資料列及段落屬性複製新增段落與表格。圖與圖說取來源架構圖的置中內嵌模式。

## 內容槽
封面兩標題改為板名與說明書；三欄改為狀態、版次、日期；四列改為規格、電源、操作、圖面。
正文原軟體占位內容依任務改為接線、操作、U1/U2、R/C、原理圖、正反面銅圖、燒錄與驗證。
各章可複製來源正文頁、標題、圖說及表格模式；與硬體無關的 API、隱私、SLO 占位內容移除，不虛構填充。
封面空白圖片區以既有 3D 預覽取代；正文架構圖片槽及其複製用於實際 KiCad 圖。
英文字型保持來源；中文指定 Microsoft JhengHei 以支援繁體字。
文件技能要求標題黑色與表格 #D9D9D9 格線，以直接格式覆蓋；不改來源 styles.xml。
頁尾占位改為模式二 E 版說明。原示範註腳說明改為原型狀態說明。

## 保留與驗證
不改原範本；單節幾何與頁首保留。styles、theme、numbering、自訂 XML 及其他非內容零件 byte-for-byte 保留。
可變零件：document.xml、document.xml.rels、新圖片與 Content_Types、新正文頁尾文字、範例註腳文字、core metadata。
原有關聯及圖片零件保留；新增圖片可新增關聯。
最終 Word PDF 逐頁 PNG 檢視，核對頁數、表格、不溢字；核對包裹保留零件及板檔 SHA-256。
