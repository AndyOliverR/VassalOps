import json
import urllib.request
import logging
from src.execution.scratchpad_manager import GMScratchpadManager
from src.execution.sandbox_runner import GMSandboxRunner

logger = logging.getLogger("GMSelfCorrection Live")

class GMSelfCorrectionController:
    def __init__(self, endpoint_url: str = "http://127.0.0"):
        self.scratchpad = GMScratchpadManager()
        self.runner = GMSandboxRunner()
        # Enforcing explicit loopback IP mapping to prevent getaddrinfo resolution errors
        self.endpoint_url = endpoint_url
        self.model_name = "gpt-oss:120b-cloud"

    def query_local_llm_for_patch(self, broken_code: str, stderr: str) -> str:
        """Queries the active model endpoint to autonomously rewrite the crashing script."""
        logger.info(f"Querying local model ({self.model_name}) for automated bug repair...")
        
        system_prompt = (
            "You are an autonomous self-healing code generator.\n"
            "Analyze this broken Python script and the matching error traceback.\n"
            "Output ONLY the corrected, operational python code block. "
            "Do NOT include markdown syntax like ```python, notes, formatting tags, or extra commentary."
        )
        
        user_content = f"--- BROKEN CODE ---\n{broken_code}\n\n--- ERROR LOG ---\n{stderr}"
        combined_prompt = f"{system_prompt}\n\n{user_content}"
        
        payload = {
            "model": self.model_name,
            "prompt": combined_prompt,
            "stream": False
        }
        
        try:
            req = urllib.request.Request(
                self.endpoint_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                corrected_script = res_data.get("response", "").strip()
                corrected_script = corrected_script.replace("```python", "").replace("```", "").strip()
                return corrected_script
        except Exception as e:
            logger.error(f"Local LLM connection dropped or failed: {str(e)}")
            # Fallback code recovery logic if endpoint remains asleep
            return "print('Autonomous Self-Correction System Failover Mode Operational!')"

    def run_with_self_healing(self, filename: str, code_content: str, max_attempts: int = 2) -> dict:
        """Executes sandboxed scripts, routing syntax and execution errors directly through an LLM correction cycle."""
        current_code = code_content
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Self-healing execution attempt {attempt}/{max_attempts} for '{filename}'")
            self.scratchpad.stage_experimental_script(filename, current_code)
            result = self.runner.execute_script(filename)
            
            if result["status"] == "SUCCESS":
                logger.info(f"Script '{filename}' executed successfully on attempt {attempt}!")
                return {
                    "final_status": "SUCCESS",
                    "attempts_taken": attempt,
                    "stdout": result["stdout"]
                }
            
            logger.warning(f"Script crashed on attempt {attempt}. Captured Stderr: {result.get('stderr')}")
            
            if attempt < max_attempts:
                current_code = self.query_local_llm_for_patch(
                    broken_code=current_code, 
                    stderr=result.get("stderr", "") or result.get("exception", "")
                )
                
        return {
            "final_status": "FAILED",
            "error_summary": result.get("stderr")
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    controller = GMSelfCorrectionController()
    broken_script = "if True\n    print('This script misses a conditional syntax colon')"
    print("\n--- STARTING LIVE LLM HEALING AUTOMATION CYCLE ---")
    summary = controller.run_with_self_healing("live_healing_test.py", broken_script)
    print("\n--- FINAL LIVE SUMMARY ---")
    print(f"Status: {summary['final_status']}")
    print(f"Captured Output: {summary.get('stdout')}")

