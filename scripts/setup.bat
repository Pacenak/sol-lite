@echo off
setlocal
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (
  echo Existing SOL-Lite venv detected. Validating/repairing installation...
) else (
  echo Creating SOL-Lite installation...
)
where py >nul 2>&1
if not errorlevel 1 (
  py -3 install\common\install.py
  exit /b %ERRORLEVEL%
)
where python >nul 2>&1
if not errorlevel 1 (
  python install\common\install.py
  exit /b %ERRORLEVEL%
)
echo Python 3.11 or newer was not found.
exit /b 1
