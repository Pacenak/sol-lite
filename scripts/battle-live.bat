@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo SOL-Lite .venv not found. Run scripts\install.ps1 first.
  exit /b 1
)
".venv\Scripts\python.exe" -m sol_lite battle-test --live --agent sol_engineer
exit /b %ERRORLEVEL%
