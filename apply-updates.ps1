$ErrorActionPreference = "Stop"

$Root = (
    Resolve-Path (
        Split-Path -Parent $MyInvocation.MyCommand.Path
    )
).Path

$Overlay = Join-Path $Root "updated-files"

if (-not (Test-Path -LiteralPath $Overlay -PathType Container)) {
    throw "Replacement overlay directory was not found: $Overlay"
}

Get-ChildItem $Overlay -File -Recurse | ForEach-Object {
    $relative = $_.FullName.Substring(
        $Overlay.Length
    ).TrimStart('\')

    $destination = Join-Path $Root $relative

    New-Item `
        -ItemType Directory `
        -Force `
        (Split-Path -Parent $destination) |
        Out-Null

    Copy-Item `
        -Force `
        $_.FullName `
        $destination

    Write-Host "UPDATED $relative"
}

Write-Host ""
Write-Host "Overlay applied."
Write-Host ""
Write-Host "Run:"
Write-Host "  .\.venv\Scripts\python.exe -m ruff check src tests"
Write-Host "  .\.venv\Scripts\python.exe -m pytest -q"
Write-Host "  .\.venv\Scripts\python.exe scripts\preflight.py"