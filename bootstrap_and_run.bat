@echo off
cd /d "%~dp0"

REM Lay-user path: Desktop shortcut uses run_vassalops.vbs (fully hidden).
REM This .bat is for troubleshooting. Pass "verbose" to watch bootstrap in a console.
if /I "%~1"=="verbose" (
  title VassalOps
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap_and_run.ps1"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0bootstrap_and_run.ps1"
)

if errorlevel 1 (
  echo.
  echo VassalOps failed to start. See storage\launch.log
  pause
  exit /b 1
)
exit /b 0
