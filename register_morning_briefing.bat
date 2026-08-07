@echo off
REM Optional: register VassalOps to open on weekday logon for the morning briefing.
REM Does NOT auto-run duties — only launches the UI (Approve still required).
cd /d "%~dp0"

schtasks /Create /F /TN "VassalOpsMorningBriefing" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 08:55 /TR "\"%~dp0bootstrap_and_run.bat\"" /RL LIMITED
if errorlevel 1 (
  echo Failed to create scheduled task. Run this .bat as your user (not SYSTEM).
  pause
  exit /b 1
)
echo Created task VassalOpsMorningBriefing (weekdays 08:55).
echo It only opens VassalOps for your Daily Duties briefing — it will not run duties without Approve.
pause
