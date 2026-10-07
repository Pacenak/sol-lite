$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root
$Python = $null
if (Get-Command py -ErrorAction SilentlyContinue) { $Python = 'py'; & py -3 install\common\install.py }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $Python = 'python'; & python install\common\install.py }
else { throw 'Python 3.11 or newer was not found. Install Python and rerun this installer.' }
$StartMenu = [Environment]::GetFolderPath('StartMenu')
$ShortcutDir = Join-Path $StartMenu 'Programs\SOL-Lite'
New-Item -ItemType Directory -Path $ShortcutDir -Force | Out-Null
$Shortcut = Join-Path $ShortcutDir 'SOL-Lite.lnk'
$Shell = New-Object -ComObject WScript.Shell
$Link = $Shell.CreateShortcut($Shortcut)
$Link.TargetPath = Join-Path $Root 'launcher\windows\SOL-Lite.cmd'
$Link.WorkingDirectory = $Root
$Link.Description = 'SOL-Lite local-first multi-agent engineering runtime'
$Link.Save()
Write-Host "SOL-Lite installed. Start Menu shortcut created: $Shortcut"
