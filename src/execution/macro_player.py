import sys
import os
import json
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

try:
    import pyautogui
    pyautogui.FAILSAFE = True
except ImportError:
    raise ImportError("Dependency missing. Please run: pip install pyautogui")

from src.execution.landmark_target import resolve_click_point, focus_window_by_title
from src.execution.plan_narrator import narrate_macro_steps
from src.execution.run_controller import run_controller


class VassalOpsMacroPlayer:
    def __init__(self, target_filename: str = "recorded_macro.json", controller=None):
        self.target_path = os.path.join("storage", target_filename)
        self.controller = controller if controller is not None else run_controller
        print(f"[VassalOps Player] Initializing macro play suite for: {self.target_path}")

    def execute_replay(self) -> bool:
        """Reads the structural timeline log and mimics captured interactions with human delay mapping."""
        if not os.path.exists(self.target_path):
            print(f"[VassalOps Player] Error: Macro tracking artifact missing at {self.target_path}")
            if self.controller:
                self.controller.finish(False, f"Macro missing: {self.target_path}")
            return False

        with open(self.target_path, "r", encoding="utf-8") as f:
            macro_data = json.load(f)

        steps = macro_data.get("steps", [])
        if not steps:
            print("[VassalOps Player] Warning: Target macro profile steps are empty.")
            if self.controller:
                self.controller.finish(False, "Macro has no steps.")
            return False

        readable = narrate_macro_steps(steps)
        if self.controller:
            self.controller.reset_for_run(readable, phase=f"macro:{os.path.basename(self.target_path)}")

        print(f"\n======================================================")
        print(f" VassalOps Macro Replay Initiated — Total Steps: {len(steps)}")
        print(f"======================================================")
        print("[!] Move your mouse cursor to the top-left corner to abort execution instantly.")
        print("[!] Use Stop in the VassalOps window to halt safely.")
        time.sleep(1.0)

        last_step_time = 0.0

        for idx, step in enumerate(steps, 1):
            if self.controller and self.controller.stop_requested():
                print("[VassalOps Player] Stop requested — aborting replay.")
                self.controller.finish(False, "Stopped by user.")
                return False

            label = readable[idx - 1] if idx - 1 < len(readable) else f"Step {idx}"
            if self.controller:
                self.controller.set_progress(idx, label)

            current_delay = float(step.get("delay") or 0.0)
            sleep_interval = max(0.0, current_delay - last_step_time)
            # Cap long recorded gaps so demos stay snappy
            time.sleep(min(sleep_interval, 3.0))
            last_step_time = current_delay

            action_type = step.get("type")
            print(f" [{idx}/{len(steps)}] Executing {str(action_type).upper()}...")

            try:
                ok = self._execute_step(step, idx, len(steps))
            except Exception as exc:
                err = f"Step {idx} failed: {exc}"
                print(f"  [!] {err}")
                if self.controller:
                    self.controller.finish(False, err)
                return False

            if ok == "stop":
                if self.controller:
                    self.controller.finish(False, "Stopped by user.")
                return False
            if ok is False:
                err = f"Step {idx} failed: {label}"
                if self.controller:
                    snap = self.controller.snapshot()
                    err = snap.get("last_error") or err
                    self.controller.finish(False, err)
                return False

        print("======================================================")
        print("[VassalOps Player] Macro sequence completed successfully.")
        print("======================================================\n")
        if self.controller:
            self.controller.finish(True)
        return True

    def _execute_step(self, step: dict, idx: int, total: int):
        action_type = step.get("type")

        if action_type == "click":
            return self._execute_click(step, idx)

        if action_type == "keystroke":
            key = step.get("key")
            if key is None:
                return False
            if len(str(key)) > 1:
                pyautogui.press(str(key))
            else:
                pyautogui.write(str(key))
            return True

        if action_type == "hotkey":
            keys = step.get("keys") or []
            if isinstance(keys, str):
                keys = [k.strip() for k in keys.replace("+", " ").split() if k.strip()]
            if not keys:
                return False
            pyautogui.hotkey(*[str(k) for k in keys])
            return True

        if action_type == "type_text":
            text = str(step.get("text") or step.get("payload") or "")
            pyautogui.write(text, interval=0.02)
            return True

        if action_type == "focus_window":
            title = str(step.get("title") or step.get("payload") or "")
            result = focus_window_by_title(title)
            if result.get("ok"):
                return True
            return self._pause_for_stuck(
                result.get("error") or f"Window “{title}” not found.",
                "Open or focus the window, then Continue.",
            )

        if action_type == "wait":
            time.sleep(float(step.get("seconds") or 1.0))
            return True

        print(f"  [!] Unknown step type: {action_type}")
        return False

    def _execute_click(self, step: dict, idx: int):
        while True:
            if self.controller and self.controller.stop_requested():
                return "stop"

            resolved = resolve_click_point(step)
            if resolved.get("ok"):
                x, y = int(resolved["x"]), int(resolved["y"])
                button_str = str(step.get("button", "left")).lower()
                btn = "left" if "left" in button_str else "right" if "right" in button_str else "middle"
                try:
                    screen_w, screen_h = pyautogui.size()
                    x = min(max(0, x), screen_w - 1)
                    y = min(max(0, y), screen_h - 1)
                except Exception:
                    pass
                pyautogui.moveTo(x, y, duration=0.15)
                pyautogui.click(button=btn)
                return True

            reason = resolved.get("error") or "Could not resolve click target."
            print(f"  [!] Stuck on click step {idx}: {reason}")
            decision = self._pause_for_stuck(
                reason,
                "Open the expected app/window (or finish MFA), then Continue to retry this click. Skip to ignore it.",
            )
            if decision == "stop":
                return "stop"
            if decision == "skip":
                print(f"  [!] Skipping click step {idx}")
                return True
            # continue -> retry loop

    def _pause_for_stuck(self, reason: str, hint: str):
        if not self.controller:
            print(f"  [!] {reason} (no UI controller; failing soft)")
            return False
        if self.controller:
            self.controller.enter_stuck(reason, hint)
            print(f"  [!] PAUSED: {reason}")
            decision = self.controller.wait_while_paused()
            if decision == "stop":
                return "stop"
            return decision  # continue | skip
        return False


if __name__ == "__main__":
    player = VassalOpsMacroPlayer()
    player.execute_replay()
