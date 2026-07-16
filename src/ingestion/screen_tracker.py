# src/ingestion/screen_tracker.py
import time
import numpy as np
import cv2
from typing import Optional, Tuple

class ScreenLayoutTracker:
    def __init__(self, pixel_threshold_pct: float = 1.0, min_interval_sec: float = 0.2):
        """
        Tracks live screen changes to prevent redundant OCR operations.
        :param pixel_threshold_pct: Percentage of pixels that must change to trigger a delta event.
        :param min_interval_sec: Minimum cooldown time between frame checks.
        """
        self.threshold = pixel_threshold_pct
        self.interval = min_interval_sec
        self.last_frame: Optional[np.ndarray] = None
        self.last_check_time = 0.0

    def has_drifted(self, current_frame: np.ndarray) -> Tuple[bool, float]:
        """
        Compares the current frame against the last saved baseline frame using fast matrix math.
        """
        now = time.time()
        if now - self.last_check_time < self.interval:
            return False, 0.0
            
        self.last_check_time = now

        # Convert to grayscale if the frame is incoming as BGR/RGB
        if len(current_frame.shape) == 3:
            gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        else:
            gray_frame = current_frame

        # Initialize baseline on the very first run
        if self.last_frame is None:
            self.last_frame = gray_frame
            return True, 100.0

        # Calculate absolute pixel difference matrix
        delta_matrix = cv2.absdiff(self.last_frame, gray_frame)
        
        # Threshold the binary mask (treat absolute changes greater than 25 values as true shifts)
        _, thresh = cv2.threshold(delta_matrix, 25, 255, cv2.THRESH_BINARY)
        
        # Calculate percentage of modified pixels across the surface array
        changed_pixels = np.count_nonzero(thresh)
        total_pixels = thresh.size
        drift_percentage = (changed_pixels / total_pixels) * 100.0

        # If change breaches threshold, save baseline frame and flag the event
        if drift_percentage >= self.threshold:
            self.last_frame = gray_frame
            return True, drift_percentage

        return False, drift_percentage

if __name__ == "__main__":
    print("[INIT] Testing ScreenLayoutTracker matrix math structures...")
    tracker = ScreenLayoutTracker(pixel_threshold_pct=0.5)
    
    # Mocking pure black and pure white frame switches to verify array operations
    f1 = np.zeros((1080, 1920), dtype=np.uint8)
    f2 = np.ones((1080, 1920), dtype=np.uint8) * 255
    
    drift_detected, pct = tracker.has_drifted(f1)
    print(f"Frame 1 (Base): Drift={drift_detected}, Delta={pct:.2f}%")
    
    drift_detected, pct = tracker.has_drifted(f2)
    print(f"Frame 2 (Inverted): Drift={drift_detected}, Delta={pct:.2f}%")

