# Stop carry-mode Lite processes started from this stick, then remind to eject safely.
$ErrorActionPreference = "Continue"
Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'sol-lite.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'sol_lite|sol-lite' } |
  ForEach-Object {
    Write-Host "Stopping PID $($_.ProcessId)"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
Write-Host "Lite stop requested. Use 'Safely Remove Hardware' before unplugging the stick."
Write-Host "Do not hot-unplug while models or git are writing to data/."
