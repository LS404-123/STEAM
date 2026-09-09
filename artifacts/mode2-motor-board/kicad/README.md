# 模式二馬達控制板 · B 版原型

KiCad 10 專案。PCB 尺寸 **22 × 20 mm**，雙面、1.6 mm FR-4、外層銅厚 1 oz；所有元件裝在正面。保留板上 S0 電源開關，沒有 LED 和模式選擇跳線。

此交付包含完整原理圖、已佈線 PCB、自含符號與封裝庫、物料表、檢查報告，以及 Gerber／鑽孔檔。**目前是硬體原型；尚未製造、焊接、燒錄或實機測試。套件不含韌體，空白 U1 不會執行模式二。**

## 開啟與檔案

1. 解壓整個專案資料夾，保留 `Mode2.pretty`、`models` 及兩個 `*-lib-table`。
2. 在 KiCad 10 開啟 `mode2-motor.kicad_pro`。
3. 開啟 `mode2-motor.kicad_sch` 查看原理圖，或 `mode2-motor.kicad_pcb` 查看板圖。
4. `exports/mode2-schematic.pdf` 是可直接閱讀的原理圖；`exports/pcb-top.png`、`pcb-bottom.png` 及 `pcb-3d.png` 是預覽。
5. `fabrication/` 及同名壓縮包提供打板資料；`BOM.csv` 是物料表。Gerber 已包含佈線和鋪銅。

`build_board.py` 是此次建檔來源，需 KiCad 的 Python／pcbnew。它會重建並覆寫設計檔；若之後在 KiCad 手動修改，請勿直接重跑它。

## 接線

| 接點 | 腳 1（方形焊盤） | 腳 2 | 腳 3 |
|---|---|---|---|
| P1 電池 | 電池正極 | 電池負極／GND | — |
| P2 SW1 | 微動開關 NO | 微動開關 COM／GND | — |
| P3 SW2 | 微動開關 NO | 微動開關 COM／GND | — |
| P4 馬達 | OUT1 | OUT2 | — |
| P5 燒錄 | VBAT／目標電壓 | UPDI | GND |

- **使用 2 粒 AA 串聯。不要接 3 粒 AA、USB 5 V 或 9 V 電池。** 2 粒鎳氫電池標稱 2.4 V，2 粒鹼性電池標稱 3 V。馬達端電壓會隨電池狀態及負載變化。
- P1、P4 是間距 2.5 mm、孔徑 0.8 mm 的焊線孔。P5 間距 2.54 mm、孔徑 1.0 mm，可裝 1×3 排針，或直接接燒錄線。
- P2、P3 改用 **JST PH 2.0 mm 白色兩針直立插座 B2B-PH-K-S(LF)(SN)**，配套插頭是 **PHR-2**。可購買已壓好端子的 PH 2.0 mm 兩芯線組，每個開關一組；不要買成 XH 2.5 mm。
- SW1／SW2 只使用 COM、NO；NC 不接。線組接 P2/P3 的 1 腳至 NO、2 腳至 COM；依腳號核對，不能只靠線的顏色判斷。S1/S2 是板外微動開關。
- C4 是 **100 nF 無極性陶瓷電容**，直接焊在馬達兩端，不裝在這片 PCB。馬達兩端均不可固定接 GND。
- S0 型號固定為 **E-Switch 500ASSP1M2QE**。2 腳為共用端，1–2 接通時開機；切換至 2–3 時關機，3 腳不接其他網路。
- C3 的正極接 VBAT，負極接 GND；依 PCB 的「+」與電容本體負極標記核對方向。U1/U2 依封裝的 1 腳標記安裝。
- 燒錄使用支援 ATtiny202 的 UPDI 工具。燒錄器和電池只能選一個供電來源；若由電池供電，燒錄器的 Vtarget 接腳須作電壓感測，不能同時輸出另一個電壓。

## 元件與選型依據

板上共 9 個必要元件：2 顆 IC、1 顆電阻、3 顆電容、1 個電源開關及 2 個白色插座。另需兩組配套插頭線組；P1、P4 的焊線孔和 P5 燒錄孔無需另購連接器。

| 位號 | 型號／規格 | 封裝與說明 |
|---|---|---|
| U1 | Microchip ATtiny202-SSNR | SOIC-8，3.9 × 4.9 mm，腳距 1.27 mm；須燒錄 |
| U2 | Texas Instruments DRV8213DSGR | DSG WSON-8，2 × 2 mm，腳距 0.5 mm；底部 EP 接地 |
| R1 | 1.24 kΩ，1%，≥0.063 W | 0603／1608 metric；例如 Yageo RC0603FR-071K24L |
| C1、C2 | 100 nF，16 V，X7R，±10% | 0603／1608 metric；例如 Murata GRM188R71C104KA01D |
| C3 | Panasonic EEEFK0J101UR，100 µF／6.3 V | 有極性鋁電解，直徑 5 mm、高 5.8 mm；原型初值 |
| S0 | E-Switch 500ASSP1M2QE | 3 A／28 VDC 銀接點版本，直插、3 腳距 2.54 mm |
| P2、P3 | JST B2B-PH-K-S(LF)(SN) | 白色兩針直立插座，腳距 2.0 mm，本體 5.9 × 4.5 mm |
| 插頭線組（板外） | PHR-2 配套端子及兩芯線，各 2 組 | 建議直接買已壓接線組；PCB 1 腳接 NO，2 腳接 COM |
| C4（板外） | 100 nF 無極性陶瓷，耐壓 ≥10 V | 焊在馬達接點，封裝依實際焊接空間選擇 |

不要按外觀用其他三腳開關替代 S0：腳距、額定電流及本體尺寸可能不同。電容 C3 的焊盤也以這個尺寸設計，替代品需核對底座與端子。

B 版只更改 SW1/SW2 連接器、相關佈線及 P5 位置，PCB 維持 22 × 20 mm。插座及配套插頭尺寸依 [JST PH 原廠資料表](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)；直立插座從板面上方插拔。

U2 的 GAINSEL 接地，電流鏡比例為 205 µA/A，DSG 內部參考電壓標稱 0.510 V。因此 R1 的標稱限流值為 `0.510 / (205e-6 × 1240) ≈ 2.006 A`；IC 與電阻誤差會影響實際值。這是待測的啟動／負載限流設定，不是連續工作電流保證，也不是堵轉自動停機功能。[TI DRV8213 資料表](https://www.ti.com/lit/ds/symlink/drv8213.pdf)

Tamiya 980112M 的產品規格列出 1.5–3 V 工作範圍及 3 V 時 2.1 A 堵轉電流，所以本版採用 2 粒 AA。[馬達產品規格](https://www.pololu.com/product/77/specs)

U1 接腳依 [Microchip ATtiny202 資料表](https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/ATtiny202-204-402-404-406-DataSheet-DS40002318A.pdf)；S0 電氣及機械規格依 [E-Switch 產品頁](https://www.e-switch.com/product/500a-series-subminiature-slide-switch/) 與 [原廠尺寸圖](https://configured-product-images.s3.amazonaws.com/2D/specs/500ASSP1M2QE.pdf)；C3 尺寸依 [Panasonic 產品頁](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-smd/models/EEEFK0J101UR)。

## 韌體要求（尚未實作）

| 功能 | U1 腳位 |
|---|---|
| SW1 輸入、啟用內置上拉 | 腳 2，PA6 |
| SW2 輸入、啟用內置上拉 | 腳 3，PA7 |
| U2 IN1 控制 | 腳 4，PA1 |
| U2 IN2 控制 | 腳 5，PA2 |
| UPDI 燒錄 | 腳 6，PA0 |
| IPROPI 電流感測 | 腳 7，PA3／ADC |

時鐘設定須符合電池電壓下的規格（本版以不高於 5 MHz 為目標）。開機先設定 IN1=0、IN2=0。SW1 按下後正轉（10），SW2 按下後反轉（01），再次 SW1 按下後停止（00），忽略兩個開關 3 秒，再回到等待。

00 是自由滑行停止，並非電氣煞車。按住開關不應重複觸發；需要去彈跳與按下事件判斷。其他按鍵次序、同時按下、反轉前的過渡時間、堵轉停止條件和低電壓復位策略，須在韌體階段定義並按機械負載測試。

## 製造與驗證範圍

- 雙面 FR-4、1.6 mm、1 oz。設計最小銅間距 0.15 mm；一般訊號線 0.20–0.25 mm，電池主幹 0.8 mm、馬達主幹 0.6 mm，IC 焊盤附近有短段 0.2 mm 引出線。
- U2 EP 下有兩個 0.2 mm 鍍通散熱孔，與正反面地平面連接。其他貫孔為 0.3 mm。下單時確認工廠支援 0.2 mm 鑽孔；散熱孔底面蓋油，EP 正面需焊接。裝配廠需注意小孔吸錫及 EP 焊接品質。
- U2 是底部接點 WSON，需合適的回流焊／熱風工藝；焊接 EP 是必要步驟。元件高度最高由 S0 決定，板面小並不代表總高度只有 1.6 mm。
- 板上未加入反接保護；接電池前核對 P1 極性。C3 的容量、電源尖峰、反轉電流與持續負載溫升尚待示波器及實機測試。不要用長時間堵轉來驗證功能。
- KiCad 的 ERC、DRC、未接線及原理圖一致性結果見 `reports/`；這些檢查能發現連線／幾何問題，不能代替韌體和實體測試。
- 3D 預覽使用廠方 S0 模型與 KiCad 通用元件模型；U2 是依封裝尺寸製作的外形示意。3D 圖不作外殼精密干涉檢查依據。

## 檔案來源

SOIC、WSON、電阻、電容及 JST PH 插座焊盤沿用 KiCad 10 官方封裝庫；S0 焊盤依廠方 T551002 rev G 圖面建立。KiCad 庫資產的授權資訊見 [KiCad Libraries License](https://www.kicad.org/libraries/license/)。廠方 PDF 與 STEP 原始資料保留原有權利聲明。
