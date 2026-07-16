import sys
import os
import json
import time

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

try:
    import pyautogui
    pyautogui.FAILSAFE = True
except ImportError:
    raise ImportError("Dependency missing. Please run: pip install pyautogui")

class VassalOpsMacroPlayer:
    def __init__(self, target_filename: str = "recorded_macro.json"):
        self.target_path = os.path.join("storage", target_filename)
        print(f"[VassalOps Player] Initializing macro play suite for: {self.target_path}")

    def execute_replay(self):
        """Reads the structural timeline log and mimics captured interactions with human delay mapping."""
        if not os.path.exists(self.target_path):
            print(f"[VassalOps Player] Error: Macro tracking artifact missing at {self.target_path}")
            return False

        with open(self.target_path, "r") as f:
            macro_data = json.load(f)

        steps = macro_data.get("steps", [])
        if not steps:
            print("[VassalOps Player] Warning: Target macro profile steps are empty.")
            return False

        print(f"\n======================================================")
        print(f" VassalOps Macro Replay Initiated — Total Steps: {len(steps)}")
        print(f"======================================================")
        print("[!] Move your mouse cursor to the top-left corner to abort execution instantly.")
        time.sleep(2.0) # Grace delay to let user switch focus if needed

        last_step_time = 0.0

        for idx, step in enumerate(steps, 1):
            # Calculate the human delay interval relative to the prior action timestamp
            current_delay = step["delay"]
            sleep_interval = max(0.0, current_delay - last_step_time)
            time.sleep(sleep_interval)
            last_step_time = current_delay

            action_type = step["type"]
            print(f" [{idx}/{len(steps)}] Executing {action_type.upper()}...")

            if action_type == "click":
                # Extract click points and target button mapping profiles
                x, y = step["x"], step["y"]
                button_str = step["button"].lower()
                btn = "left" if "left" in button_str else "right" if "right" in button_str else "middle"

                pyautogui.moveTo(x, y, duration=0.2)
                pyautogui.click(button=btn)

            elif action_type == "keystroke":
                key = step["key"]
                # Handle special key layout normalization translations
                if len(key) > 1:
                    pyautogui.press(key)
                else:
                    pyautogui.write(key)

        print("======================================================")
        print("[VassalOps Player] Macro sequence completed successfully.")
        print("======================================================\n")
        return True

if __name__ == "__main__":
    player = VassalOpsMacroPlayer()
    player.execute_replay()
