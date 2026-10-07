$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$python = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw "SOL-Lite .venv Python not found. Run scripts\install.ps1 first." }
& $python -m sol_lite start
exit $LASTEXITCODE
