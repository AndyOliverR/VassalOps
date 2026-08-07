@echo off
title VassalOps
cd /d "%~dp0"

REM One-click entry: bootstrap deps + Ollama, then open the chat UI.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap_and_run.ps1"
if errorlevel 1 (
  echo.
  echo VassalOps failed to start. See storage\launch.log
  pause
  exit /b 1
)
exit /b 0
