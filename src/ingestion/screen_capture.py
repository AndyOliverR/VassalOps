import os
import sys
import time
import ctypes
from typing import Dict, Any, Tuple

# Fix Python path tracking for local folder resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Force strict hardware coordinate tracking across high-DPI magnified displays
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per-Monitor DPI Aware profile
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware() # Classic Windows fallback hook
    except Exception:
        print("[VassalOps Scaling Warning] Failed to initialize hardware DPI awareness loops.")

try:
    from PIL import ImageGrab
    import numpy as np
    import win32gui
    # Import the tracker safely now that sys.path is updated
    from src.ingestion.screen_tracker import ScreenLayoutTracker
except ImportError:
    raise ImportError("Dependencies missing. Please run: pip install pillow numpy pywin32 opencv-python")

class ScreenContextLayer:
    def __init__(self, output_dir: str = "src/ingestion/cache/"):
        self.output_dir = os.path.abspath(os.path.join(project_root, output_dir))
        os.makedirs(self.output_dir, exist_ok=True)
        # Initialize the tracker with a 0.5% layout drift sensitivity threshold
        self.tracker = ScreenLayoutTracker(pixel_threshold_pct=0.5, min_interval_sec=0.2)
        self.cached_filepath = ""

    def capture_full_display(self) -> Tuple[str, bool]:
        """
        Captures the active screen, analyzes pixel drift in memory,
        and saves a new PNG file ONLY if a visual shift occurred.
        Returns: (filepath_to_current_frame, drift_detected)
        """
        self._purge_old_cache_frames(max_age_seconds=60)

        # 1. Grab screen to memory buffer as raw array instantly
        screenshot = ImageGrab.grab(all_screens=False)
        frame_np = np.array(screenshot)

        # 2. Run memory array delta comparison
        drift_detected, pct = self.tracker.has_drifted(frame_np)

        # 3. If drift is tracked or no previous frame path exists, update the disk asset
        if drift_detected or not self.cached_filepath or not os.path.exists(self.cached_filepath):
            timestamp = int(time.time())
            self.cached_filepath = os.path.join(self.output_dir, f"raw_surface_{timestamp}.png")
            screenshot.save(self.cached_filepath, "PNG")
            return self.cached_filepath, True

        # 4. If screen is static, skip saving to disk and return the last valid frame asset
        return self.cached_filepath, False

    def _purge_old_cache_frames(self, max_age_seconds: int = 60):
        try:
            now = time.time()
            for filename in os.listdir(self.output_dir):
                if filename.startswith("raw_surface_") and filename.endswith(".png"):
                    file_path = os.path.join(self.output_dir, filename)
                    if os.path.getmtime(file_path) < (now - max_age_seconds):
                        os.remove(file_path)
        except Exception as e:
            print(f"[VassalOps Cache Warning] Failed to clean workspace artifacts: {e}")

    def extract_window_bounds(self, target_title: str = "ActiveWindow") -> Tuple[int, int, int, int]:
        """Dynamically grabs the precise screen bounds of whichever window is currently in focus."""
        hwnd = win32gui.GetForegroundWindow()

        if hwnd != 0:
            title = win32gui.GetWindowText(hwnd)
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            if left >= -10000 and top >= -10000:
                print(f"[VassalOps] Intercepted Focused Window: '{title}'")
                return (left, top, right, bottom)

        print("[VassalOps] Warning: No active focused window tracked. Using sandbox bounds.")
        return (100, 100, 900, 700)

if __name__ == "__main__":
    parser = ScreenContextLayer()
    print("[VassalOps] Running Integrated Screen Capture + Tracker validation test...")
    
    # Run test frame 1
    path1, drift1 = parser.capture_full_display()
    print(f"[LOOP 1] Path: {path1} | New Drift Event Triggered: {drift1}")
    
    # Wait briefly to let the tracker cooldown elapse
    time.sleep(0.3)
    
    # Run test frame 2 (with a static screen display)
    path2, drift2 = parser.capture_full_display()
    print(f"[LOOP 2 - Static Screen] Path: {path2} | New Drift Event Triggered: {drift2}")




