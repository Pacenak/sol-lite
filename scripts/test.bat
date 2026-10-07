@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" ( echo SOL-Lite .venv not found. Run scripts\setup.bat first. & exit /b 1 )
".venv\Scripts\python.exe" -m pytest -q
exit /b %ERRORLEVEL%
