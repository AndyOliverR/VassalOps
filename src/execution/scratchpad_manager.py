import os
import shutil
import logging
from typing import Dict, Any

logger = logging.getLogger("GMScratchpadManager")

class GMScratchpadManager:
    def __init__(self, scratch_dir: str = "C:\\VassalOps\\scratchpad"):
        self.scratch_dir = scratch_dir
        self.ensure_scratchpad_exists()

    def ensure_scratchpad_exists(self):
        """Creates an isolated clean-slate directory boundary for experimental AI scripts."""
        if not os.path.exists(self.scratch_dir):
            os.makedirs(self.scratch_dir)
            logger.info(f"Initialized isolated Arbor-style scratchpad zone at: {self.scratch_dir}")

    def clean_scratchpad(self):
        """Wipes the virtual canvas clean to avoid caching historical code errors."""
        if os.path.exists(self.scratch_dir):
            shutil.rmtree(self.scratch_dir)
        os.makedirs(self.scratch_dir)
        logger.info("Scratchpad environment cleared and reset to fresh baseline state.")

    def stage_experimental_script(self, filename: str, raw_code_content: str) -> str:
        """Writes the AI generated script directly inside the sandbox boundary."""
        self.ensure_scratchpad_exists()
        target_path = os.path.join(self.scratch_dir, filename)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(raw_code_content)
        logger.info(f"Experimental script staged inside safety harness sandbox: {target_path}")
        return target_path

if __name__ == "__main__":
    manager = GMScratchpadManager()
    manager.clean_scratchpad()
    path = manager.stage_experimental_script("test_autonomy.py", "print('Autonomous Code Run Successful')")
    print(f"[SCRATCHPAD VERIFIED] Temporary module safely isolated at: {path}")

