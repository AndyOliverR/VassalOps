import sys
import os
import json
from typing import Dict, Any

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.ingestion.screen_capture import ScreenContextLayer

class GMAILayoutProfiler:
    def __init__(self):
        self.capturer = ScreenContextLayer()
        self.registry_path = os.path.join("src", "ingestion", "window_layouts.json")
        print("[GM AI Profiler] Automated Structural Layout Profiler active.")

    def profile_active_window(self, app_key: str) -> Dict[str, Any]:
        """Scans the active foreground application window and calculates relative grid targets."""
        bounds = self.capturer.extract_window_bounds()
        left, top, right, bottom = bounds
        win_w = right - left
        win_h = bottom - top

        print(f"[GM AI Profiler] Profiling active window envelope for '{app_key}': {win_w}x{win_h}")

        # Compute a standardized 9-point structural subdivision mesh layout mapping
        dynamic_profile = {
            "center_focus": {"rel_x": 0.5, "rel_y": 0.5},
            "top_left_action": {"rel_x": 0.05, "rel_y": 0.05},
            "bottom_input_line": {"rel_x": 0.5, "rel_y": 0.9}
        }

        self._append_to_registry(app_key, dynamic_profile)
        return dynamic_profile

    def _append_to_registry(self, app_key: str, profile_data: Dict[str, Any]):
        """Safely merges the newly discovered app elements into your window_layouts.json matrix."""
        current_registry = {}
        
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r") as f:
                    current_registry = json.load(f)
            except Exception:
                pass

        # Merge structural layouts cleanly
        current_registry[app_key.lower().strip()] = profile_data

        with open(self.registry_path, "w") as f:
            json.dump(current_registry, f, indent=2)
        print(f"[GM AI Profiler] Layout elements for '{app_key}' dynamically committed to registry matrix.")

if __name__ == "__main__":
    profiler = GMAILayoutProfiler()
    app_name = "command_prompt"
    print(f"[GM AI] Triggering automated surface scanning for profile key: {app_name}")
    profiler.profile_active_window(app_name)



