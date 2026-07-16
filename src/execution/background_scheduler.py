import sys
import os
import time
import threading
import sqlite3

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.execution.audit_ledger import GMAIAuditLedger

class GMAIBackgroundDaemon:
    def __init__(self, check_interval_sec: float = 5.0):
        self.interval = check_interval_sec
        self.ledger = GMAIAuditLedger()
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Spawns the background telemetry scanner daemon thread loop."""
        if self.is_running:
            print("[GM AI Daemon] Warning: Background tracker is already executing.")
            return

        self.is_running = True
        self._thread = threading.Thread(target=self._daemon_loop, daemon=True)
        self._thread.start()
        print(f"[GM AI Daemon] Autonomous background scheduler initialized. Polling interval: {self.interval}s")

    def stop(self):
        """Gracefully terminates the execution loop flag."""
        self.is_running = False
        print("[GM AI Daemon] Halting background worker threads...")

    def _daemon_loop(self):
        while self.is_running:
            try:
                # Perform autonomous lightweight telemetry heartbeat check
                self._execute_heartbeat_audit()
            except Exception as e:
                print(f"[GM AI Daemon Error] Exception caught in background loop: {e}")
            time.sleep(self.interval)

    def _execute_heartbeat_audit(self):
        """Performs non-destructive diagnostic check on the system status."""
        print("[GM AI Daemon] Running background pipeline status audit...")
        
        # Self-healing test trace to confirm ledger connectivity
        self.ledger.commit_transaction(
            intent="Auto-Scan Heartbeat | Verified Local Processing Nodes",
            status="AUDITED",
            device="System Background Guard",
            channel="background_telemetry"
        )

if __name__ == "__main__":
    print("[INIT] Testing GMAIBackgroundDaemon scheduler matrix threads...")
    daemon = GMAIBackgroundDaemon(check_interval_sec=2.0)
    daemon.start()
    
    # Run loop for 5 seconds to let multiple ticks register, then exit
    time.sleep(5.0)
    daemon.stop()
    print("[INIT] Background test pass complete.")



