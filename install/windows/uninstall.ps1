$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$answer = Read-Host "Remove SOL-Lite runtime (.venv and data/state) from $Root? [y/N]"
if ($answer -notin @('y','Y','yes','YES')) { exit 0 }
Remove-Item -LiteralPath (Join-Path $Root '.venv') -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $Root 'data\state\install.json') -Force -ErrorAction SilentlyContinue
Write-Host 'SOL-Lite runtime installation removed. Source, configuration, skills and workspaces were retained.'
