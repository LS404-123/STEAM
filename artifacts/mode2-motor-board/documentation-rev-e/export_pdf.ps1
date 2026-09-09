$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskWord = New-Object -ComObject Word.Application
$taskWord.Visible = $false
$taskWord.DisplayAlerts = 0
try {
    $taskDoc = $taskWord.Documents.Open((Join-Path $taskRoot '模式二控制板E版使用與原理說明.docx'), $false, $true)
    $taskDoc.Fields.Update() | Out-Null
    $taskDoc.ExportAsFixedFormat((Join-Path $taskRoot '模式二控制板E版使用與原理說明.pdf'), 17)
    Write-Output ('Pages: ' + $taskDoc.ComputeStatistics(2))
    $taskDoc.Close(0)
}
finally { $taskWord.Quit() }
& pdftoppm -scale-to 1800 -png (Join-Path $taskRoot '模式二控制板E版使用與原理說明.pdf') (Join-Path $taskRoot 'qa/page')
