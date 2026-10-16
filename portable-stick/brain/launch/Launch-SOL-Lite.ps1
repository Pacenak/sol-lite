# Carry-mode: run SOL-Lite with data/workspace on this BRAIN stick.
# Usage: .\Launch-SOL-Lite.ps1 [-RepoRoot <path-to-PLG_Ai_Lite-clone>]
param(
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"
$LaunchDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BrainRoot = Split-Path -Parent $LaunchDir

python "$LaunchDir\resolve_stick_root.py" | ForEach-Object {
    if ($_ -match "^([^=]+)=(.*)$") {
        Set-Item -Path "Env:$($Matches[1])" -Value $Matches[2]
    }
}

Write-Host "SOL_DATA_ROOT=$env:SOL_DATA_ROOT"
Write-Host "SOL_WORKSPACE_ROOT=$env:SOL_WORKSPACE_ROOT"

if (-not $RepoRoot) {
    # Prefer SOL_LITE_REPO (from resolver / SOLLITE volume), then legacy brain\sol-lite-src
    if ($env:SOL_LITE_REPO -and (Test-Path $env:SOL_LITE_REPO)) {
        $RepoRoot = $env:SOL_LITE_REPO
    } elseif (Test-Path (Join-Path $BrainRoot "sol-lite-src\pyproject.toml")) {
        $RepoRoot = Join-Path $BrainRoot "sol-lite-src"
    }
}

if ($RepoRoot) {
    Write-Host "SOL_LITE_REPO=$RepoRoot"
    Set-Location $RepoRoot
    if (Test-Path ".\.venv\Scripts\sol-lite.exe") {
        & ".\.venv\Scripts\sol-lite.exe" start --workspace $env:SOL_WORKSPACE_ROOT
    } elseif (Test-Path ".\.venv\Scripts\python.exe") {
        & ".\.venv\Scripts\python.exe" -m sol_lite start --workspace $env:SOL_WORKSPACE_ROOT
    } else {
        python -m sol_lite start --workspace $env:SOL_WORKSPACE_ROOT
    }
} else {
    Write-Host "Set SOL_LITE_REPO to your PLG_Ai_Lite clone on SOLLITE (or legacy brain\sol-lite-src)"
    Write-Host "Env is set — run: sol-lite start --workspace `$env:SOL_WORKSPACE_ROOT"
}
