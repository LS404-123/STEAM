# 模式二馬達控制板 · C 版原型

KiCad 10 專案。PCB 尺寸 **24 × 22 mm**，雙面、1.6 mm FR-4、外層銅厚 1 oz；所有元件裝在正面。S0 改為薄型滑動開關，由 Q1 接通電源；電池、馬達、SW1、SW2 均使用插座。沒有 LED 和模式選擇跳線。

此交付包含完整原理圖、已佈線 PCB、自含符號與封裝庫、物料表、檢查報告，以及 Gerber／鑽孔檔。**目前是硬體原型；尚未製造、焊接、燒錄或實機測試。套件不含韌體，空白 U1 不會執行模式二。**

## 開啟與檔案

1. 解壓整個專案資料夾，保留 `Mode2.pretty`、`models` 及兩個 `*-lib-table`。
2. 在 KiCad 10 開啟 `mode2-motor.kicad_pro`。
3. 開啟 `mode2-motor.kicad_sch` 查看原理圖，或 `mode2-motor.kicad_pcb` 查看板圖。
4. `exports/mode2-schematic.pdf` 是可直接閱讀的原理圖；`exports/pcb-top.png`、`pcb-bottom.png` 及 `pcb-3d.png` 是預覽。
5. `fabrication/` 及同名壓縮包提供打板資料；`BOM.csv` 是物料表。Gerber 已包含佈線和鋪銅。

`build_board.py` 是此次建檔來源，需 KiCad 的 Python／pcbnew。它會重建並覆寫設計檔；若之後在 KiCad 手動修改，請勿直接重跑它。

## 接線

| 接點 | 腳 1（矩形／圓角矩形焊盤） | 腳 2 | 腳 3 |
|---|---|---|---|
| P1 電池 | 電池正極 | 電池負極／GND | — |
| P2 SW1 | 微動開關 NO | 微動開關 COM／GND | — |
| P3 SW2 | 微動開關 NO | 微動開關 COM／GND | — |
| P4 馬達 | OUT1 | OUT2 | — |
| P5 燒錄 | VBAT／目標電壓 | UPDI | GND |

- **使用 2 粒 AA 串聯。不要接 3 粒 AA、USB 5 V 或 9 V 電池。** 2 粒鎳氫電池標稱 2.4 V，2 粒鹼性電池標稱 3 V。馬達端電壓會隨電池狀態及負載變化。
- **P1 電池、P4 馬達：JST XH 2.5 mm 兩針直立插座 B2B-XH-A(LF)(SN)**。配套使用 XHP-2 插頭、SXH-001T-P0.6 端子及 AWG22 銅線；直接買已壓接好的兩芯線組最方便。3 A 額定值以 AWG22 為條件。P5 保留 2.54 mm 燒錄孔。
- 從正面看，電池插座在右上、馬達插座在右下。**P1 與 P4 外形相同，接線前按「電池／馬達」絲印核對，切勿互插。** 電池紅線接 P1 的 1 腳正極，黑線接 2 腳負極；馬達兩條線接 P4 的 1、2 腳。馬達方向相反時，在斷電下交換馬達的兩條線。
- P2、P3 改用 **JST PH 2.0 mm 白色兩針直立插座 B2B-PH-K-S(LF)(SN)**，配套插頭是 **PHR-2**。可購買已壓好端子的 PH 2.0 mm 兩芯線組，每個開關一組；不要買成 XH 2.5 mm。
- SW1／SW2 只使用 COM、NO；NC 不接。線組接 P2/P3 的 1 腳至 NO、2 腳至 COM；依腳號核對，不能只靠線的顏色判斷。S1/S2 是板外微動開關。
- C4 是 **100 nF 無極性陶瓷電容**，直接焊在馬達兩端，不裝在這片 PCB。馬達兩端均不可固定接 GND。
- S0 使用 **SHOU HAN MSK12C02，立創料號 C431540**，按 2024-12-14 資料表建立封裝。1–2 接通為關機；2–3 接通為開機；4 腳為外殼接地。不同廠牌的 MSK12C02 不能只按名稱互換，需核對腳位和尺寸。
- C3 的正極接 VBAT，負極接 GND；依 PCB 的「+」與電容本體負極標記核對方向。U1/U2 依封裝的 1 腳標記安裝。
- 燒錄使用支援 ATtiny202 的 UPDI 工具。燒錄器和電池只能選一個供電來源。**若燒錄器供電，必須拔下 P1 電池插頭，不能只關 S0**：Q1 的本體二極體仍可從 VBAT 回灌到電池端。若電池供電，燒錄器 Vtarget 只作電壓感測，不能同時輸出電壓。

## 元件與選型依據

板上共 **14 個元件**：2 顆 IC、1 顆 MOSFET、3 顆電阻、3 顆電容、1 個小滑動開關及 4 個插座。另需 4 組配套插頭線組。P5 是燒錄孔，可不裝排針。

| 位號 | 型號／規格 | 封裝與說明 |
|---|---|---|
| U1 | Microchip ATtiny202-SSNR | SOIC-8，3.9 × 4.9 mm，腳距 1.27 mm；須燒錄 |
| U2 | Texas Instruments DRV8213DSGR | DSG WSON-8，2 × 2 mm，腳距 0.5 mm；底部 EP 接地 |
| R1 | 1.24 kΩ，1%，≥0.063 W | 0603／1608 metric；例如 Yageo RC0603FR-071K24L |
| C1、C2 | 100 nF，16 V，X7R，±10% | 0603／1608 metric；例如 Murata GRM188R71C104KA01D |
| C3 | Panasonic EEEFK0J101UR，100 µF／6.3 V | 有極性鋁電解，直徑 5 mm、高 5.8 mm；原型初值 |
| S0 | SHOU HAN MSK12C02，C431540 | 50 mA／12 V，SMD；本體高約 1.4 mm，只切換閘極控制訊號 |
| Q1 | Diodes DMP2035U-7 | P 通道 MOSFET，SOT-23；1=G、2=S、3=D |
| R2 | 1 kΩ，1%，0603；RC0603FR-071KL | 串聯於 S0 與 Q1 閘極，限制切換瞬間電流 |
| R3 | 100 kΩ，1%，0603；RC0603FR-07100KL | Q1 閘極至源極上拉，換檔間隙預設關斷 |
| P1、P4 | JST B2B-XH-A(LF)(SN) | XH 2.5 mm 兩針直立插座，配 XHP-2、SXH-001T-P0.6、AWG22 線 |
| P2、P3 | JST B2B-PH-K-S(LF)(SN) | 白色兩針直立插座，腳距 2.0 mm，本體 5.9 × 4.5 mm |
| 插頭線組（板外） | XHP-2 兩組；PHR-2 兩組 | XH 接電池／馬達；PH 接 SW1／SW2，不可混用系列 |
| C4（板外） | 100 nF 無極性陶瓷，耐壓 ≥10 V | 焊在馬達接點，封裝依實際焊接空間選擇 |

電容 C3 的焊盤以指定底座尺寸設計；替代品需核對端子。S0 的 8 × 2.8 mm 外形數值包含橫向焊腳，本體金屬殼約 6.7 × 2.8 mm、高 1.4 mm；手柄橫向伸出 PCB 上邊約 1.05 mm。沒有使用原本高身的進口電源開關。

C 版增加電池、馬達插座後，PCB 由 B 版 22 × 20 mm 改為 24 × 22 mm。XH 插頭接妥後還需為線材及插拔預留上方空間。規格依 [JST XH 原廠資料表](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf) 及 [JST PH 原廠資料表](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)。

## 小電源開關怎樣工作

電池正極接 Q1 的 Source（2 腳），Q1 的 Drain（3 腳）供電給 VBAT。S0 不承受馬達啟動電流。

- **關機，S0 1–2 接通：** GDRV 接電池正極，經 R2 把 Gate 拉到 Source 電位，VGS 約 0 V，Q1 關斷。
- **開機，S0 2–3 接通：** GDRV 接地，Gate 被拉低，Q1 導通。3 V 電池下 VGS 約 -2.97 V；R2、R3 分壓支路電流約 29.7 µA。
- **R2 = 1 kΩ：** 以 3.3 V 電池計，理想最大閘極充電電流約 3.3 mA，低於 S0 的 50 mA 額定值。它控制瞬間閘極電流，並非馬達限流電阻。
- **R3 = 100 kΩ：** 開關在兩檔之間斷開時，把 Gate 拉回 Source，避免浮接；同時降低開機時的持續耗電。
- Q1 在 VGS=-1.8 V 時 RDS(on) 最大 62 mΩ（25°C 資料表測試條件），2 A 時估算損耗約 0.248 W、壓降 0.124 V。實際溫升仍受板面散熱和工作時間影響，不代表可無限期堵轉。

Q1 不是反接保護，也不是雙向隔離開關。斷電時 C3 可能仍有殘餘電壓；進行接線或更換元件前拔掉電池。

資料依 [DMP2035U 原廠資料表](https://www.diodes.com/datasheet/download/DMP2035U.pdf) 與 [SHOU HAN MSK12C02 2024-12-14 圖面](https://datasheet.lcsc.com/datasheet/pdf/5162155576bfd231c35aa9a893d25c8c.pdf?productCode=C431540)。

U2 的 GAINSEL 接地，電流鏡比例為 205 µA/A，DSG 內部參考電壓標稱 0.510 V。因此 R1 的標稱限流值為 `0.510 / (205e-6 × 1240) ≈ 2.006 A`；IC 與電阻誤差會影響實際值。這是待測的啟動／負載限流設定，不是連續工作電流保證，也不是堵轉自動停機功能。[TI DRV8213 資料表](https://www.ti.com/lit/ds/symlink/drv8213.pdf)

Tamiya 980112M 的產品規格列出 1.5–3 V 工作範圍及 3 V 時 2.1 A 堵轉電流，所以本版採用 2 粒 AA。[馬達產品規格](https://www.pololu.com/product/77/specs)

U1 接腳依 [Microchip ATtiny202 資料表](https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/ATtiny202-204-402-404-406-DataSheet-DS40002318A.pdf)；C3 尺寸依 [Panasonic 產品頁](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-smd/models/EEEFK0J101UR)。

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
- U2 是底部接點 WSON，需合適的回流焊／熱風工藝；焊接 EP 是必要步驟。S0 已降低至約 1.4 mm；現在整體高度主要由插座及插入的插頭決定。
- 板上未加入反接保護；接電池前核對 P1 極性。C3 的容量、電源尖峰、反轉電流與持續負載溫升尚待示波器及實機測試。不要用長時間堵轉來驗證功能。
- KiCad 的 ERC、DRC、未接線及原理圖一致性結果見 `reports/`；這些檢查能發現連線／幾何問題，不能代替韌體和實體測試。
- 3D 預覽使用 KiCad 通用元件模型；S0、U2 是依封裝尺寸製作的外形示意。3D 圖不作外殼精密干涉檢查依據。

## 檔案來源

SOIC、SOT-23、WSON、電阻、電容及 JST PH／XH 插座焊盤沿用 KiCad 10 官方封裝庫；MOSFET 符號取自 KiCad Transistor_FET:Q_PMOS_GSD；S0 焊盤依 SHOU HAN 2024-12-14 圖面建立。KiCad 庫資產的授權資訊見 [KiCad Libraries License](https://www.kicad.org/libraries/license/)。廠方 PDF 與 STEP 原始資料保留原有權利聲明。
