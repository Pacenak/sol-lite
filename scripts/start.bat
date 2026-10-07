@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo SOL-Lite is not installed. Run scripts\setup.bat first.
  exit /b 1
)
".venv\Scripts\python.exe" scripts\preflight.py
if errorlevel 1 exit /b %ERRORLEVEL%
".venv\Scripts\python.exe" -m sol_lite start %*
exit /b %ERRORLEVEL%
