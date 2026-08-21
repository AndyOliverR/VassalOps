@echo off
title VassalOps Install
cd /d "%~dp0"

echo.
echo  VassalOps — one-time install
echo  Your PC's workday — taught by you, approved by you, run locally.
echo.
echo  This will set up Python/Ollama if needed, install packages,
echo  and put a VassalOps icon on your Desktop.
echo.
echo  Windows may ask for permission (winget / UAC). Allow it if prompted.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_vassalops.ps1"
set ERR=%ERRORLEVEL%

echo.
if %ERR% neq 0 (
  echo  Install did not finish cleanly. See messages above.
  echo  You can re-run INSTALL.bat after fixing any errors.
) else (
  echo  Next step: double-click the VassalOps icon on your Desktop.
)
echo.
pause
exit /b %ERR%
