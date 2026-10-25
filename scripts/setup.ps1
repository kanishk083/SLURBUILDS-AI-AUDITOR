$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
uv venv --python 3.13 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements-local.lock --torch-backend cpu
if ($LASTEXITCODE -ne 0) { throw 'Locked dependency installation failed.' }
uv pip install --python .venv\Scripts\python.exe --no-deps -e .
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
Push-Location -LiteralPath (Join-Path $projectRoot 'frontend')
try { npm.cmd ci; if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }; npm.cmd run build; if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' } }
finally { Pop-Location }
docker compose up -d --wait postgres redis
& .\.venv\Scripts\python.exe -m alembic upgrade head
& .\.venv\Scripts\python.exe scripts/warm_models.py
