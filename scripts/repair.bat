@echo off
setlocal
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File ".\install\windows\repair.ps1"
exit /b %ERRORLEVEL%
