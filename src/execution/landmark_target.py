"""Window-title and optional OCR landmark helpers for more robust clicks."""

from __future__ import annotations

import ctypes
import time
from typing import Any, Dict, List, Optional, Tuple


user32 = ctypes.windll.user32


def list_window_titles() -> List[str]:
    titles: List[str] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def _enum(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.strip()
                if title:
                    titles.append(title)
        return True

    user32.EnumWindows(_enum, 0)
    return titles


def find_hwnd_by_title(substring: str) -> Optional[int]:
    needle = (substring or "").strip().lower()
    if not needle:
        return None
    found = {"hwnd": None}

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def _enum(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value.strip()
        if needle in title.lower():
            found["hwnd"] = int(hwnd)
            return False
        return True

    user32.EnumWindows(_enum, 0)
    return found["hwnd"]


def focus_window_by_title(substring: str, retries: int = 3, delay: float = 0.35) -> Dict[str, Any]:
    """Bring a window whose title contains substring to the foreground."""
    for attempt in range(retries):
        hwnd = find_hwnd_by_title(substring)
        if hwnd:
            try:
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                user32.SetForegroundWindow(hwnd)
                time.sleep(0.15)
                return {"ok": True, "hwnd": hwnd, "matched": substring, "attempts": attempt + 1}
            except Exception as exc:
                return {"ok": False, "error": str(exc), "matched": substring}
        time.sleep(delay)
    return {
        "ok": False,
        "error": f"Window matching “{substring}” not found.",
        "available": list_window_titles()[:12],
    }


def active_window_title() -> str:
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value or ""


def find_text_on_screen(needle: str) -> Optional[Tuple[int, int]]:
    """
    Best-effort OCR landmark: returns center (x,y) of matching text box.
    Returns None if OCR stack unavailable or no match.
    """
    text = (needle or "").strip()
    if not text:
        return None
    try:
        from PIL import ImageGrab
        import pytesseract
        import os

        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        img = ImageGrab.grab()
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        target = text.lower()
        n = len(data.get("text") or [])
        for i in range(n):
            word = (data["text"][i] or "").strip()
            if not word:
                continue
            if target in word.lower() or word.lower() in target:
                x = int(data["left"][i] + data["width"][i] / 2)
                y = int(data["top"][i] + data["height"][i] / 2)
                if x > 0 and y > 0:
                    return (x, y)
    except Exception:
        return None
    return None


def resolve_click_point(step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prefer OCR landmark_text, else focus window_title then use absolute coords.
    """
    landmark = (step.get("landmark_text") or "").strip()
    if landmark:
        pt = find_text_on_screen(landmark)
        if pt:
            return {"ok": True, "x": pt[0], "y": pt[1], "method": "ocr_landmark"}
        return {
            "ok": False,
            "error": f"Could not find on-screen text “{landmark}”.",
            "method": "ocr_landmark",
        }

    title = (step.get("window_title") or "").strip()
    if title:
        focused = focus_window_by_title(title)
        if not focused.get("ok"):
            return {
                "ok": False,
                "error": focused.get("error") or "Window focus failed.",
                "method": "window_title",
                "available": focused.get("available") or [],
            }

    try:
        x = int(step["x"])
        y = int(step["y"])
    except Exception:
        return {"ok": False, "error": "Click step missing numeric x/y.", "method": "coords"}
    return {"ok": True, "x": x, "y": y, "method": "coords_after_focus" if title else "coords"}
