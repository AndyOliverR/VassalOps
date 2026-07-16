import sys
import os
import json
import time

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

try:
    from pynput import mouse, keyboard
except ImportError:
    raise ImportError("Dependencies missing. Please run: pip install pynput")

class GMAIMacroRecorder:
    def __init__(self, output_filename: str = "recorded_macro.json"):
        self.output_path = os.path.join("storage", output_filename)
        os.makedirs("storage", exist_ok=True)
        self.macro_steps = []
        self.start_time = time.time()
        
        self.mouse_listener = None
        self.keyboard_listener = None
        print(f"[GM AI Recorder] Macro pipeline tracking targets bound to: {self.output_path}")

    def _get_elapsed_time(self) -> float:
        return round(time.time() - self.start_time, 2)

    def on_click(self, x: int, y: int, button, pressed):
        """Callback that intercepts and tokenizes physical human click points."""
        if pressed:
            step = {
                "type": "click",
                "x": x,
                "y": y,
                "button": str(button),
                "delay": self._get_elapsed_time()
            }
            print(f" [*] Logged Click: Button.{button} at ({x}, {y})")
            self.macro_steps.append(step)

    def on_press(self, key):
        """Callback that logs alphanumeric keystrokes and escape parameters."""
        try:
            # Check for standard characters
            key_stroke = key.char
        except AttributeError:
            # Handle system modifiers (like space, enter, backspace)
            key_stroke = str(key).replace("Key.", "")

        # End recording condition: pressing the escape key triggers the teardown sequence
        if key == keyboard.Key.esc:
            print("\n[GM AI Recorder] Escape token captured. Suspending listeners...")
            return False

        step = {
            "type": "keystroke",
            "key": key_stroke,
            "delay": self._get_elapsed_time()
        }
        print(f" [*] Logged Key: {key_stroke}")
        self.macro_steps.append(step)

    def start_recording(self):
        """Spins up background input capture loops concurrently."""
        print("======================================================")
        print(" GM AI Macro Recorder Active — Session Started")
        print("======================================================")
        print("[!] NOTICE: All inputs are now actively monitored.")
        print("[!] To stop recording, tap the ESC key on your keyboard.")
        print("======================================================\n")
        
        self.start_time = time.time()

        # Mount non-blocking mouse and keyboard listener loops
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)

        self.mouse_listener.start()
        self.keyboard_listener.start()

        # Keep thread alive until the keyboard listener terminates via ESC
        self.keyboard_listener.join()
        self.mouse_listener.stop()

        self.save_macro()

    def save_macro(self):
        """Serializes captured sequence timeline artifacts to local storage disk."""
        try:
            with open(self.output_path, "w") as f:
                json.dump({"steps": self.macro_steps}, f, indent=2)
            print(f"\n[GM AI Recorder] Macro sequence file successfully written to disk: {self.output_path}")
        except Exception as e:
            print(f"[GM AI Recorder Error] Failed to export session sequence: {e}")

if __name__ == "__main__":
    recorder = GMAIMacroRecorder()
    recorder.start_recording()



