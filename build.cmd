@echo off
setlocal
set "MODE=%~1"
if "%MODE%"=="" set "MODE=all"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\windows\build.ps1" -Mode "%MODE%"
exit /b %ERRORLEVEL%
