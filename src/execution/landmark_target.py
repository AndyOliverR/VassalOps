"""Window-title and optional OCR landmark helpers for more robust clicks."""

from __future__ import annotations

import ctypes
import re
import time
from typing import Any, Dict, List, Optional, Tuple


user32 = ctypes.windll.user32


def normalize_title(value: str) -> str:
    """Lowercase and collapse whitespace for title comparisons."""
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def score_title_match(needle: str, title: str) -> int:
    """
    Score how well title matches needle (higher is better; 0 = no match).

    Prefer exact title, then prefix, then substring (shorter titles win ties),
    then all needle words present as tokens.
    """
    n = normalize_title(needle)
    t = normalize_title(title)
    if not n or not t:
        return 0
    if t == n:
        return 1000
    if t.startswith(n):
        return 800 + max(0, 50 - len(t))
    if n in t:
        # Prefer shorter titles containing the needle (more specific window).
        return 500 + max(0, 80 - len(t))
    n_words = [w for w in n.split(" ") if w]
    t_words = set(t.split(" "))
    if n_words and all(w in t_words or any(w in tw for tw in t_words) for w in n_words):
        return 200 + max(0, 40 - len(t))
    return 0


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
    """Return hwnd for the best-scoring visible window title match."""
    needle = (substring or "").strip()
    if not needle:
        return None
    best = {"hwnd": None, "score": 0}

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
        score = score_title_match(needle, title)
        if score > best["score"]:
            best["hwnd"] = int(hwnd)
            best["score"] = score
        return True

    user32.EnumWindows(_enum, 0)
    return best["hwnd"] if best["score"] > 0 else None


def focus_window_by_title(substring: str, retries: int = 3, delay: float = 0.35) -> Dict[str, Any]:
    """Bring a window whose title best matches substring to the foreground."""
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
    Best-effort OCR landmark: returns center (x,y) of matching text.
    Tries single words first, then joins consecutive OCR tokens for multi-word needles.
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
        words = data.get("text") or []
        n = len(words)

        for i in range(n):
            word = (words[i] or "").strip()
            if not word:
                continue
            if target in word.lower() or word.lower() in target:
                x = int(data["left"][i] + data["width"][i] / 2)
                y = int(data["top"][i] + data["height"][i] / 2)
                if x > 0 and y > 0:
                    return (x, y)

        # Multi-word: slide a window of consecutive non-empty tokens.
        tokens: List[Tuple[int, str]] = [
            (i, (words[i] or "").strip()) for i in range(n) if (words[i] or "").strip()
        ]
        needle_words = target.split()
        if len(needle_words) >= 2:
            width = len(needle_words)
            for start in range(0, len(tokens) - width + 1):
                chunk = tokens[start : start + width]
                joined = " ".join(w.lower() for _, w in chunk)
                if joined == target or target in joined:
                    idxs = [i for i, _ in chunk]
                    left = min(int(data["left"][i]) for i in idxs)
                    top = min(int(data["top"][i]) for i in idxs)
                    right = max(int(data["left"][i] + data["width"][i]) for i in idxs)
                    bottom = max(int(data["top"][i] + data["height"][i]) for i in idxs)
                    x = (left + right) // 2
                    y = (top + bottom) // 2
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
            return {
                "ok": True,
                "x": pt[0],
                "y": pt[1],
                "method": "ocr_landmark",
                "landmark": landmark,
                "active_window": active_window_title(),
            }
        return {
            "ok": False,
            "error": f"Could not find on-screen text “{landmark}”.",
            "method": "ocr_landmark",
            "landmark": landmark,
            "active_window": active_window_title(),
            "available_titles": list_window_titles()[:12],
        }

    title = (step.get("window_title") or "").strip()
    if title:
        focused = focus_window_by_title(title)
        if not focused.get("ok"):
            return {
                "ok": False,
                "error": focused.get("error") or "Window focus failed.",
                "method": "window_title",
                "window_title": title,
                "active_window": active_window_title(),
                "available": focused.get("available") or [],
                "score_hint": _best_title_score(title),
            }

    try:
        x = int(step["x"])
        y = int(step["y"])
    except Exception:
        return {"ok": False, "error": "Click step missing numeric x/y.", "method": "coords"}
    return {
        "ok": True,
        "x": x,
        "y": y,
        "method": "coords_after_focus" if title else "coords",
        "window_title": title or None,
        "active_window": active_window_title(),
    }


def _best_title_score(needle: str) -> Dict[str, Any]:
    best_title = ""
    best_score = 0
    for title in list_window_titles():
        score = score_title_match(needle, title)
        if score > best_score:
            best_score = score
            best_title = title
    return {"best_title": best_title, "best_score": best_score}


def resolve_click_point_with_retries(
    step: Dict[str, Any],
    *,
    max_auto_retries: int = 2,
    delay: float = 0.45,
) -> Dict[str, Any]:
    """
    Sugar retry ladder before HITL stuck:
    1) resolve once
    2) refocus window_title (if any) and retry
    3) re-OCR landmark (if any) and retry
    Then return last failure for Continue/Skip pause.
    """
    last: Dict[str, Any] = {"ok": False, "error": "No attempt made."}
    title = (step.get("window_title") or "").strip()
    landmark = (step.get("landmark_text") or "").strip()

    for attempt in range(max_auto_retries + 1):
        if attempt > 0:
            if title:
                focus_window_by_title(title, retries=2, delay=delay)
            time.sleep(delay)
            # Landmark path re-runs OCR inside resolve_click_point
        result = resolve_click_point(step)
        result["auto_attempt"] = attempt + 1
        result["auto_retries_max"] = max_auto_retries
        if result.get("ok"):
            return result
        last = result

    last["auto_exhausted"] = True
    last["tried"] = (
        f"Tried resolve + up to {max_auto_retries} auto-retries "
        f"(refocus{' + re-OCR' if landmark else ''}). "
        f"Active window: {last.get('active_window') or '(unknown)'}."
    )
    return last
