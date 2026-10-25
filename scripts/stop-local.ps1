$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pidsFile = Join-Path $projectRoot '.data\services.json'
if (-not (Test-Path -LiteralPath $pidsFile)) { Write-Output 'No recorded local processes.'; exit }
$recorded = Get-Content -LiteralPath $pidsFile -Raw | ConvertFrom-Json
foreach ($item in $recorded) {
    $taskProcess = Get-Process -Id $item.Id -ErrorAction SilentlyContinue
    if ($taskProcess -and ($taskProcess.StartTime.ToUniversalTime() - [datetime]$item.Started).Duration().TotalSeconds -lt 2) {
        # Stop only the recorded process tree after checking its creation time (avoid PID reuse).
        taskkill.exe /PID $item.Id /T /F | Out-Null
    }
}
Remove-Item -LiteralPath $pidsFile
Write-Output 'Recorded app processes stopped. PostgreSQL and Redis remain available.'
