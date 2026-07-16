import sys
import os
import json
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

try:
    import pyautogui
    import win32gui
    pyautogui.FAILSAFE = True
except ImportError:
    raise ImportError("Dependencies missing. Please run: pip install pyautogui pywin32")

from src.ingestion.screen_capture import ScreenContextLayer

class SystemOperatorBridge:
    def __init__(self):
        self.capturer = ScreenContextLayer()
        self.layout_path = os.path.join("src", "ingestion", "window_layouts.json")
        self.layouts = self._load_layouts()

    def _load_layouts(self):
        try:
            with open(self.layout_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def execute_targeted_click(self, app_key: str, element_key: str) -> bool:
        """
        Resolves target app window boundaries with an automated self-healing retry loop,
        ensuring slow-booting application windows finish mounting before deployment.
        """
        max_retries = 6
        retry_delay = 0.5
        bounds = None

        print(f"[GM AI Bridge] Target lock engaged for '{app_key}.{element_key}'. Verifying window stability...")

        for attempt in range(1, max_retries + 1):
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd).lower() if hwnd != 0 else ""
            
            # Check if the desired application moniker is active in the foreground string hook
            if app_key.lower() in title or (app_key.lower() == "notepad" and "notepad" in title):
                bounds = self.capturer.extract_window_bounds()
                print(f"[GM AI Bridge] Target window '{app_key}' verified stable on attempt {attempt}.")
                break
                
            print(f"[GM AI Warning] Window stability delay: Current foreground context '{title}' does not match '{app_key}'. Retrying...")
            time.sleep(retry_delay)

        # Fallback to current focus if the target application fails to mount within the safety threshold
        if bounds is None:
            print(f"[GM AI Recovery] Window wait timeout breached for '{app_key}'. Falling back to current bounding matrix.")
            bounds = self.capturer.extract_window_bounds()

        left, top, right, bottom = bounds
        win_w = right - left
        win_h = bottom - top

        screen_width, screen_height = pyautogui.size()
        print(f"[GM AI Scaler] Live hardware display matrix: {screen_width}x{screen_height}")

        if app_key in self.layouts and element_key in self.layouts[app_key]:
            rel = self.layouts[app_key][element_key]

            target_x = left + int(win_w * rel["rel_x"])
            target_y = top + int(win_h * rel["rel_y"])

            target_x = max(0, min(target_x, screen_width - 1))
            target_y = max(0, min(target_y, screen_height - 1))

            print(f"[GM AI Operator] Dynamic target scaled safely to point: ({target_x}, {target_y})")
            pyautogui.moveTo(target_x, target_y, duration=0.5)
            pyautogui.click()
            print("[GM AI Operator] Cross-display scaled action deployed.")
            return True

        print(f"[GM AI Operator] Target mapping mismatch: {app_key}.{element_key}")
        return False

    def execute_text_input(self, text: str, press_enter: bool = True):
        print(f"[GM AI Operator] Emulating text entry sequencing: '{text}'")
        pyautogui.write(text, interval=0.05)
        if press_enter:
            pyautogui.press('enter')

    def execute_system_hotkey(self, hotkey_combination: str) -> bool:
        print(f"[GM AI Operator] Dispatched system key combo sequence: [{hotkey_combination}]")
        keys = [k.strip().lower() for k in hotkey_combination.split("+")]
        try:
            pyautogui.hotkey(*keys)
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"[GM AI Operator Error] Hotkey macro injection mismatch: {e}")
            return False

if __name__ == "__main__":
    operator = SystemOperatorBridge()
    print("[GM AI] Running operator bridge initialization pass...")
    # Trigger a clean, safe hotkey pass to ensure all pywin32 bindings load correctly
    operator.execute_system_hotkey("ctrl+shift+esc")



