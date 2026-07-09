import subprocess
import sys
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("GMSandboxRunner")

class GMSandboxRunner:
    def __init__(self, scratch_dir: str = "C:\\VassalOps\\scratchpad"):
        self.scratch_dir = scratch_dir

    def execute_script(self, filename: str, timeout_sec: float = 5.0) -> dict:
        """Executes a sandboxed script in an isolated subprocess and returns the execution matrix."""
        target_path = os.path.join(self.scratch_dir, filename)
        if not os.path.exists(target_path):
            return {"status": "ERROR", "exception": "Target script file does not exist inside sandbox."}

        # Enforce isolated environment pathing parameters
        custom_env = os.environ.copy()
        custom_env["PYTHONPATH"] = f"{self.scratch_dir};C:\\VassalOps;C:\\VassalOps\\src"

        try:
            # Run target script in an isolated process block capturing system outputs
            result = subprocess.run(
                [sys.executable, target_path],
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                env=custom_env
            )
            
            if result.returncode == 0:
                return {
                    "status": "SUCCESS",
                    "stdout": result.stdout.strip(),
                    "stderr": result.stderr.strip()
                }
            else:
                return {
                    "status": "CRASHED",
                    "stdout": result.stdout.strip(),
                    "stderr": result.stderr.strip(),
                    "exception": f"Process exited with non-zero return code: {result.returncode}"
                }

        except subprocess.TimeoutExpired:
            logger.error(f"Sandbox script execution exceeded timeout safety ceiling of {timeout_sec}s.")
            return {"status": "TIMEOUT", "exception": f"Execution timed out after {timeout_sec} seconds."}
        except Exception as e:
            return {"status": "ERROR", "exception": str(e)}

if __name__ == "__main__":
    runner = GMSandboxRunner()
    # Test execution against our existing staged script from Step 5
    run_matrix = runner.execute_script("test_autonomy.py")
    print(f"\n--- SANDBOX RUNNER TEST RESULT ---")
    print(f"Status: {run_matrix['status']}")
    print(f"Captured Output: {run_matrix.get('stdout')}")

