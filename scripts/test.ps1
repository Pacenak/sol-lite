$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path .\.venv\Scripts\python.exe)) { throw "Run .\scripts\install.ps1 first." }
.\.venv\Scripts\python.exe -m pytest -q
