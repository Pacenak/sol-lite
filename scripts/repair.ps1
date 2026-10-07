$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
& (Join-Path $Root 'install\windows\repair.ps1')
