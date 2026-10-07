@echo off
setlocal
cd /d "%~dp0..\.."
if not exist ".venv\Scripts\python.exe" (
  echo SOL-Lite is not installed. Run scripts\setup.bat first.
  exit /b 1
)
".venv\Scripts\python.exe" -m sol_lite doctor
exit /b %ERRORLEVEL%
