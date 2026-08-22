"""Screen geometry helpers for VassalOps windows."""
from __future__ import annotations

import time
from typing import Callable, List, Optional, Tuple


def primary_work_area() -> Tuple[int, int, int, int]:
    """Return (left, top, width, height) for the primary monitor work area."""
    try:
        import ctypes
        from ctypes import wintypes

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", wintypes.LONG),
                ("top", wintypes.LONG),
                ("right", wintypes.LONG),
                ("bottom", wintypes.LONG),
            ]

        SPI_GETWORKAREA = 48
        rect = RECT()
        ok = ctypes.windll.user32.SystemParametersInfoW(  # type: ignore[attr-defined]
            SPI_GETWORKAREA, 0, ctypes.byref(rect), 0
        )
        if ok:
            return (
                int(rect.left),
                int(rect.top),
                int(rect.right - rect.left),
                int(rect.bottom - rect.top),
            )

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        return 0, 0, int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
    except Exception:
        return 0, 0, 1280, 720


def centered_xy(width: int, height: int) -> Tuple[int, int]:
    left, top, work_w, work_h = primary_work_area()
    x = left + max(0, (work_w - int(width)) // 2)
    y = top + max(0, (work_h - int(height)) // 2)
    return x, y


def fitted_window(
    preferred_w: int = 960,
    preferred_h: int = 640,
    *,
    max_frac: float = 0.60,
) -> Tuple[int, int, int, int]:
    """Size ≤ max_frac of work area (aspect preserved) + center. Returns (x, y, w, h)."""
    left, top, work_w, work_h = primary_work_area()
    max_w = max(320, int(work_w * max_frac))
    max_h = max(240, int(work_h * max_frac))
    scale = min(max_w / float(preferred_w), max_h / float(preferred_h), 1.0)
    width = min(max(320, int(round(preferred_w * scale))), max_w, work_w)
    height = min(max(240, int(round(preferred_h * scale))), max_h, work_h)
    x = left + max(0, (work_w - width) // 2)
    y = top + max(0, (work_h - height) // 2)
    return x, y, width, height


def _enum_hwnds_by_title(substr: str = "VassalOps") -> List[int]:
    """Find top-level windows whose title contains substr."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    found: List[int] = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @WNDENUMPROC
    def _cb(hwnd, _lparam):  # type: ignore[misc]
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        if substr.lower() in buf.value.lower():
            found.append(int(hwnd))
        return True

    user32.EnumWindows(_cb, 0)
    return found


def find_vassalops_hwnd() -> Optional[int]:
    import ctypes

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    hwnd = int(user32.FindWindowW(None, "VassalOps") or 0)
    if hwnd:
        return hwnd
    matches = _enum_hwnds_by_title("VassalOps")
    return matches[0] if matches else None


def seat_hwnd_centered(hwnd: int, *, max_frac: float = 0.60, preferred_w: int = 960, preferred_h: int = 640) -> bool:
    """
    Resize + center `hwnd` on the monitor it currently sits on.
    Uses that monitor's work area (taskbar-aware) at max_frac of size.
    """
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD),
        ]

    MONITOR_DEFAULTTONEAREST = 2
    SWP_NOZORDER = 0x0004
    SWP_SHOWWINDOW = 0x0040
    SW_RESTORE = 9

    hmon = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    if not user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
        return False

    work = mi.rcWork
    work_w = int(work.right - work.left)
    work_h = int(work.bottom - work.top)
    if work_w < 200 or work_h < 200:
        return False

    max_w = max(320, int(work_w * max_frac))
    max_h = max(240, int(work_h * max_frac))
    scale = min(max_w / float(preferred_w), max_h / float(preferred_h), 1.0)
    width = min(max(320, int(round(preferred_w * scale))), max_w, work_w)
    height = min(max(240, int(round(preferred_h * scale))), max_h, work_h)
    x = int(work.left + max(0, (work_w - width) // 2))
    y = int(work.top + max(0, (work_h - height) // 2))

    user32.ShowWindow(hwnd, SW_RESTORE)
    ok = bool(
        user32.SetWindowPos(
            hwnd,
            0,
            x,
            y,
            width,
            height,
            SWP_NOZORDER | SWP_SHOWWINDOW,
        )
    )
    return ok


def win32_place_vassalops_window(x: int, y: int, width: int, height: int) -> bool:
    """Legacy absolute place — prefer seat_hwnd_centered / seat_vassalops_loop."""
    hwnd = find_vassalops_hwnd()
    if not hwnd:
        return False
    try:
        import ctypes

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        SWP_NOZORDER = 0x0004
        SWP_SHOWWINDOW = 0x0040
        return bool(
            user32.SetWindowPos(hwnd, 0, int(x), int(y), int(width), int(height), SWP_NOZORDER | SWP_SHOWWINDOW)
        )
    except Exception:
        return False


def seat_vassalops_loop(
    *,
    max_frac: float = 0.60,
    preferred_w: int = 960,
    preferred_h: int = 640,
    duration_s: float = 2.5,
    interval_s: float = 0.12,
    log: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Keep re-centering for a short period so Edge/WebView2 can't snap the window
    back to the default cascade corner after our first SetWindowPos.
    """
    def _log(msg: str) -> None:
        if log:
            log(msg)

    deadline = time.time() + duration_s
    placed = False
    while time.time() < deadline:
        hwnd = find_vassalops_hwnd()
        if hwnd:
            ok = seat_hwnd_centered(
                hwnd,
                max_frac=max_frac,
                preferred_w=preferred_w,
                preferred_h=preferred_h,
            )
            if ok and not placed:
                _log(f"seated hwnd={hwnd} frac={max_frac}")
                placed = True
        time.sleep(interval_s)
    if not placed:
        _log("seat_vassalops_loop: never found VassalOps hwnd")
