import sys
import os
import asyncio
import time

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.ingestion.screen_capture import ScreenContextLayer
from src.ingestion.ocr_reader import VassalOpsScreenOCRReader
from src.execution.audit_ledger import GMANetworkAuditLedger

class VassalOpsBackgroundScheduler:
    def __init__(self, interval_seconds: int = 10):
        self.interval = interval_seconds
        self.screen_layer = ScreenContextLayer()
        self.ocr_engine = VassalOpsScreenOCRReader()
        self.ledger = GMANetworkAuditLedger()
        self.is_running = False
        print(f"[VassalOps Scheduler] Background automation loop initialized at {self.interval}s intervals.")

    async def monitor_loop(self):
        """Asynchronous worker that logs background context audits continuously without breaking main user execution."""
        self.is_running = True
        print("[VassalOps Scheduler] Continuous telemetry scan thread active. Monitoring system canvas...")
        
        try:
            while self.is_running:
                # 1. Capture current display surface
                frame_path = self.screen_layer.capture_full_display()
                
                # 2. Translate pixels to verify workspace signatures
                raw_text = self.ocr_engine.extract_text_from_matrix(frame_path)
                entities = self.ocr_engine.extract_structural_entities(raw_text)
                
                # 3. Log a heartbeat baseline artifact inside your relational database
                log_msg = f"Auto-Scan Heartbeat | Discovered tokens: URL={len(entities['urls'])} Path={len(entities['windows_paths'])}"
                self.ledger.log_action("System Background Guard", log_msg, status="AUDITED")
                
                # 4. Suspend execution cleanly for the interval duration
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            print("[VassalOps Scheduler] Telemetry loop suspended safely.")
        except Exception as e:
            print(f"[VassalOps Scheduler Error] Telemetry baseline loop failure: {e}")

    def start_scheduler(self):
        """Launches the asynchronous state loop wrapper."""
        try:
            asyncio.run(self.monitor_loop())
        except KeyboardInterrupt:
            print("\n[VassalOps Scheduler] Shutting down background timers cleanly.")

if __name__ == "__main__":
    # Initialize a hyper-fast 60-second baseline tracking interval to run local checks
    scheduler = VassalOpsBackgroundScheduler(interval_seconds=60)
    scheduler.start_scheduler()




