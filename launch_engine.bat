@echo off
title VassalOps Core Engine
cls
echo ======================================================
echo       VassalOps -- LOCAL PYWEBVIEW UI
echo ======================================================
echo [*] Status: Initializing local engine modules...
echo [*] Directory: %CD%

if not exist gm_memory.db (
    echo [!] Warning: Relational memory state ledger missing. Building local instance...
)

echo [*] Network note: http.server and socket_broker are NOT auto-started.
echo [*] UI runs inside pywebview only (no LAN-exposed dashboard).
echo [*] To run the broker manually later: python src\communication\socket_broker.py
echo [*] Broker binds 127.0.0.1 and requires broker_auth_token from config.json.

echo [*] Target: Initializing automated background telemetry task schedulers...
start "VassalOps Telemetry Task Daemon" cmd /k "python src\execution\task_scheduler.py"

echo [*] Target: Initializing primary human interactive console environment...
echo ======================================================
echo [SYSTEM ONLINE] Local pywebview UI launching.
echo ======================================================
echo.
cmd /k "python app.py"
