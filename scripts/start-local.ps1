$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run scripts/setup.ps1 first.' }
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot '.data\logs') | Out-Null
docker compose up -d --wait postgres redis
& $pythonPath -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
$services = @(
    @{ Name='api'; Args=@('-m','uvicorn','backend.api:app','--host','127.0.0.1','--port','8000') },
    @{ Name='worker'; Args=@('-m','arq','backend.worker.WorkerSettings') }
)
$pidsFile = Join-Path $projectRoot '.data\services.json'
if (Test-Path -LiteralPath $pidsFile) {
    $existing = Get-Content -LiteralPath $pidsFile -Raw | ConvertFrom-Json
    foreach ($item in $existing) {
        if (Get-Process -Id $item.Id -ErrorAction SilentlyContinue) { throw 'Local processes already recorded. Run scripts/stop-local.ps1 before starting again.' }
    }
}
$started = @()
foreach ($service in $services) {
    $taskProcess = Start-Process -FilePath $pythonPath -ArgumentList $service.Args -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot ('.data\logs\'+$service.Name+'.out.log')) -RedirectStandardError (Join-Path $projectRoot ('.data\logs\'+$service.Name+'.err.log')) -PassThru
    $started += @{ Name=$service.Name; Id=$taskProcess.Id; Started=$taskProcess.StartTime.ToUniversalTime().ToString('o') }
}
$npmPath = (Get-Command npm.cmd).Source
$webProcess = Start-Process -FilePath $npmPath -ArgumentList @('run','start','--','--port','3000') -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot '.data\logs\web.out.log') -RedirectStandardError (Join-Path $projectRoot '.data\logs\web.err.log') -PassThru
$started += @{ Name='web'; Id=$webProcess.Id; Started=$webProcess.StartTime.ToUniversalTime().ToString('o') }
$started | ConvertTo-Json | Set-Content -LiteralPath $pidsFile -Encoding UTF8
Write-Output 'AI Auditor: http://localhost:3000 | API docs: http://127.0.0.1:8000/docs'
