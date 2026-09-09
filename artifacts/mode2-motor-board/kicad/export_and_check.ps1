# 使用 KiCad 的正式檢查與匯出功能；任一檢查失敗便停止交付輸出。
$ErrorActionPreference = 'Stop'
$taskKiCadBin = 'C:\Users\LS404\AppData\Local\Programs\KiCad\10.0\bin'
$taskCli = Join-Path $taskKiCadBin 'kicad-cli.exe'
Push-Location -LiteralPath $PSScriptRoot
try {
function Invoke-KiCad {
    param([string[]]$CommandArgs)
    & $taskCli @CommandArgs
    if ($LASTEXITCODE -ne 0) { throw "KiCad 命令失敗：$($CommandArgs -join ' ')" }
}
Invoke-KiCad @('sch','erc','--format','json','--exit-code-violations','--output','reports/erc.json','mode2-motor.kicad_sch')
Invoke-KiCad @('pcb','drc','--refill-zones','--save-board','--all-track-errors','--schematic-parity','--format','json','--exit-code-violations','--output','reports/drc.json','mode2-motor.kicad_pcb')
Invoke-KiCad @('sch','export','pdf','--output','exports/mode2-schematic.pdf','mode2-motor.kicad_sch')
Invoke-KiCad @('sch','export','svg','--output','exports/','mode2-motor.kicad_sch')
Invoke-KiCad @('sch','export','netlist','--format','kicadxml','--output','exports/mode2-netlist.xml','mode2-motor.kicad_sch')
Invoke-KiCad @('pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts','--output','fabrication/','mode2-motor.kicad_pcb')
Invoke-KiCad @('pcb','export','drill','--output','fabrication/','--format','excellon','--excellon-units','mm','--excellon-separate-th','--generate-report','--report-path','reports/drill-report.txt','mode2-motor.kicad_pcb')
Invoke-KiCad @('pcb','export','pos','--format','csv','--units','mm','--smd-only','--output','exports/assembly-smd.csv','mode2-motor.kicad_pcb')
Invoke-KiCad @('pcb','render','--width','1600','--height','1400','--output','exports/pcb-top.png','mode2-motor.kicad_pcb')
Invoke-KiCad @('pcb','render','--side','bottom','--width','1600','--height','1400','--output','exports/pcb-bottom.png','mode2-motor.kicad_pcb')
Invoke-KiCad @('pcb','render','--rotate','35,0,20','--zoom','0.55','--perspective','--width','1600','--height','1200','--output','exports/pcb-3d.png','mode2-motor.kicad_pcb')
} finally {
    Pop-Location
}
