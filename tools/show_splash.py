"""One-shot frameless splash after INSTALL.bat (pywebview)."""
from __future__ import annotations

import os
import sys
import threading
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPLASH = os.path.join(ROOT, "storage", "dashboard", "splash.html")


class SplashApi:
    def __init__(self) -> None:
        self._window = None
        self.done = False

    def splash_finished(self) -> str:
        self.done = True
        try:
            if self._window is not None:
                self._window.destroy()
        except Exception:
            pass
        return "ok"


def main() -> int:
    if not os.path.isfile(SPLASH):
        print(f"[splash] missing {SPLASH}", file=sys.stderr)
        return 1
    try:
        import webview
    except ImportError:
        print("[splash] pywebview not installed; skip", file=sys.stderr)
        return 0

    os.chdir(ROOT)
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from src.window_center import fitted_window, seat_hwnd_centered, find_vassalops_hwnd

    api = SplashApi()
    x, y, win_w, win_h = fitted_window(480, 520, max_frac=0.55)
    window = webview.create_window(
        title="VassalOps",
        url=os.path.abspath(SPLASH),
        width=win_w,
        height=win_h,
        x=x,
        y=y,
        resizable=False,
        frameless=True,
        easy_drag=True,
        on_top=True,
        js_api=api,
    )
    api._window = window

    def _seat_center() -> None:
        try:
            window.resize(win_w, win_h)
            window.move(x, y)
        except Exception:
            pass
        hwnd = find_vassalops_hwnd()
        if hwnd:
            seat_hwnd_centered(hwnd, max_frac=0.55, preferred_w=480, preferred_h=520)

    window.events.shown += _seat_center

    def safety_close() -> None:
        # Hold slightly longer than splash.html (5s hold + fade) so INSTALL splash isn't cut short
        time.sleep(6.5)
        if not api.done:
            try:
                window.destroy()
            except Exception:
                pass

    threading.Thread(target=safety_close, daemon=True).start()
    webview.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
