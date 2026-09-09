$ErrorActionPreference = 'Stop'
$taskWord = New-Object -ComObject Word.Application
$taskWord.Visible = $false
$taskWord.DisplayAlerts = 0
try {
    $taskDoc = $taskWord.Documents.Open((Join-Path $PSScriptRoot '模式二控制板E版使用手冊.docx'), $false, $true)
    $taskDoc.Fields.Update() | Out-Null
    $taskDoc.ExportAsFixedFormat((Join-Path $PSScriptRoot '模式二控制板E版使用手冊.pdf'), 17)
    Write-Output ('Pages: ' + $taskDoc.ComputeStatistics(2))
    $taskDoc.Close(0)
}
finally { $taskWord.Quit() }
& pdftoppm -scale-to 1600 -png (Join-Path $PSScriptRoot '模式二控制板E版使用手冊.pdf') (Join-Path $PSScriptRoot 'qa/user-manual/page')
