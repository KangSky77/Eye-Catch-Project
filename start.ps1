param([int]$Port = 8001)
$ErrorActionPreference = 'Stop'
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw 'Missing .venv\Scripts\python.exe. Create the project environment first (see README).'
}
& $taskPython (Join-Path $PSScriptRoot 'scripts\start_presentation.py') --port $Port
exit $LASTEXITCODE
