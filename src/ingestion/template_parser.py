import sys
import os
# Dynamically add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from typing import Dict, Any
from src.ingestion.screen_capture import ScreenContextLayer

class VisualTemplateParser:
    def __init__(self):
        self.capturer = ScreenContextLayer()
        # Predefined structural relative maps for whitelisted windows
        self.layout_registry = {
            "notepad_edit_field": {"rel_x": 0.1, "rel_y": 0.15, "width": 0.8, "height": 0.7}
        }

    def resolve_target_coordinates(self, app_name: str, element_key: str) -> Dict[str, int]:
        """Calculates absolute screen target positions relative to application windows."""
        bounds = self.capturer.extract_window_bounds(app_name)
        left, top, right, bottom = bounds
        win_w = right - left
        win_h = bottom - top

        if element_key in self.layout_registry:
            rel = self.layout_registry[element_key]
            abs_x = left + int(win_w * rel["rel_x"])
            abs_y = top + int(win_h * rel["rel_y"])
            return {"status": "RESOLVED", "x": abs_x, "y": abs_y}
            
        return {"status": "UNKNOWN_ELEMENT", "x": 0, "y": 0}

if __name__ == "__main__":
    engine = VisualTemplateParser()
    print("[VassalOps] Initializing Visual Template Parser target calculation test...")
    coordinates = engine.resolve_target_coordinates("Notepad", "notepad_edit_field")
    print(f"[VassalOps] Parsed Visual Context Coordinates: {coordinates}")




