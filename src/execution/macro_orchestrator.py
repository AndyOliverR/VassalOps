import sys
import os
import re

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.execution.macro_recorder import VassalOpsMacroRecorder
from src.execution.macro_player import VassalOpsMacroPlayer

class VassalOpsAutomationRouter:
    def __init__(self):
        print("[VassalOps Router] Core execution routing layer online.")

    def route_command(self, user_input: str) -> str:
        """Parses broken unstructured phrases for 'learn' or 'fetch' markers."""
        cleaned_input = user_input.lower().strip()

        # Check for Learn macro intent
        if "learn" in cleaned_input:
            macro_name = self._extract_macro_name(cleaned_input, "learn")
            print(f"[VassalOps Router] Instantiating background capture pipeline for: {macro_name}")
            
            recorder = VassalOpsMacroRecorder(output_filename=macro_name)
            recorder.start_recording()
            return f"Successfully saved your system macro profile as '{macro_name}'."

        # Check for Fetch / Replay intent
        elif "fetch" in cleaned_input or "run macro" in cleaned_input:
            macro_name = self._extract_macro_name(cleaned_input, "fetch")
            print(f"[VassalOps Router] Initializing local system driver emulation for: {macro_name}")
            
            player = VassalOpsMacroPlayer(target_filename=macro_name)
            success = player.execute_replay()
            
            if success:
                return f"Successfully executed system macro profile '{macro_name}'."
            else:
                return f"Failed to execute macro profile '{macro_name}'. Check your local storage folder."

        return "Command unhandled. Please use 'learn [name]' or 'fetch [name]' rules."

    def _extract_macro_name(self, command: str, keyword: str) -> str:
        """Helper to extract an isolated filename from a conversational sentence block."""
        if keyword in command:
            raw_name = command.split(keyword)[1].replace("please", "").replace("now", "").strip()
            clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', raw_name)
            if clean_name:
                return f"{clean_name}.json"
        return "recorded_macro.json"

if __name__ == "__main__":
    router = VassalOpsAutomationRouter()
    print(router.route_command("hey learn sap_login please"))
