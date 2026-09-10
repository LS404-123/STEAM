# 已安裝 KiCad 10 後執行；所有成品檢查通過才匯出製板檔。
$ErrorActionPreference = 'Stop'
$fBin = 'C:/Users/LS404/AppData/Local/Programs/KiCad/10.0/bin'
$fCli = Join-Path $fBin 'kicad-cli.exe'
Push-Location -LiteralPath $PSScriptRoot
try {
function Invoke-FKiCad {
    param([string[]]$CommandArgs)
    & $fCli @CommandArgs
    if ($LASTEXITCODE -ne 0) { throw "KiCad 失敗：$($CommandArgs -join ' ')" }
}
Invoke-FKiCad @('sch','erc','--format','json','--exit-code-violations','--output','erc.json','mode2-no-firmware.kicad_sch')
Invoke-FKiCad @('pcb','drc','--refill-zones','--save-board','--all-track-errors','--schematic-parity','--format','json','--exit-code-violations','--output','reports/drc.json','mode2-no-firmware.kicad_pcb')
Invoke-FKiCad @('sch','export','netlist','--format','kicadxml','--output','netlist.xml','mode2-no-firmware.kicad_sch')
& (Join-Path $fBin 'python.exe') verify_design.py
if ($LASTEXITCODE -ne 0) { throw '原理圖／PCB 功能及成品檢查失敗' }
Invoke-FKiCad @('sch','export','pdf','--exclude-drawing-sheet','--output','exports/原理圖-H.pdf','mode2-no-firmware.kicad_sch')
Invoke-FKiCad @('pcb','export','svg','--layers','F.Cu,F.SilkS,Edge.Cuts','--exclude-drawing-sheet','--page-size-mode','2','--mode-single','--output','exports/正面佈線.svg','mode2-no-firmware.kicad_pcb')
Invoke-FKiCad @('pcb','export','svg','--layers','B.Cu,B.SilkS,Edge.Cuts','--mirror','--exclude-drawing-sheet','--page-size-mode','2','--mode-single','--output','exports/背面佈線.svg','mode2-no-firmware.kicad_pcb')
Invoke-FKiCad @('pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,Edge.Cuts','--output','fabrication/','mode2-no-firmware.kicad_pcb')
Invoke-FKiCad @('pcb','export','drill','--output','fabrication/','--format','excellon','--excellon-units','mm','--excellon-separate-th','--generate-report','--report-path','reports/drill-report.txt','mode2-no-firmware.kicad_pcb')
Invoke-FKiCad @('pcb','export','pos','--format','csv','--units','mm','--smd-only','--output','exports/貼片座標.csv','mode2-no-firmware.kicad_pcb')
Invoke-FKiCad @('pcb','export','vrml','--force','--units','mm','--output','exports/完整3D板.wrl','mode2-no-firmware.kicad_pcb')
Invoke-FKiCad @('pcb','render','--width','1600','--height','1600','--quality','high','--output','exports/PCB正面.png','mode2-no-firmware.kicad_pcb')
Invoke-FKiCad @('pcb','render','--side','bottom','--width','1600','--height','1600','--quality','high','--output','exports/PCB背面.png','mode2-no-firmware.kicad_pcb')
Invoke-FKiCad @('pcb','render','--rotate','-25,0,20','--zoom','0.7','--perspective','--width','1600','--height','1400','--quality','high','--output','exports/PCB-3D.png','mode2-no-firmware.kicad_pcb')
} finally { Pop-Location }
