# VassalOps thin launcher — finds install root and starts bootstrap_and_run.bat
# Built with: packaging\build_launcher.ps1  →  dist\VassalOps.exe / repo root VassalOps.exe

from __future__ import annotations

import os
import subprocess
import sys
import ctypes
from typing import Optional


def _msg(title: str, text: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(0, text, title, 0x10)
    except Exception:
        print(f"{title}: {text}")


def find_root() -> Optional[str]:
    if getattr(sys, "frozen", False):
        candidates = [os.path.dirname(sys.executable)]
    else:
        candidates = [os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))]

    candidates.append(r"C:\VassalOps")

    env = os.environ.get("VASSALOPS_ROOT")
    if env:
        candidates.insert(0, env)

    for root in candidates:
        bat = os.path.join(root, "bootstrap_and_run.bat")
        if os.path.isfile(bat):
            return root
    return None


def main() -> int:
    root = find_root()
    if not root:
        _msg(
            "VassalOps",
            "Could not find VassalOps.\n\n"
            "Place VassalOps.exe next to bootstrap_and_run.bat,\n"
            "or set VASSALOPS_ROOT, or install to C:\\VassalOps.\n\n"
            "Tip: run install_vassalops.ps1 first.",
        )
        return 1
    bat = os.path.join(root, "bootstrap_and_run.bat")
    try:
        subprocess.Popen(["cmd.exe", "/c", bat], cwd=root)
    except Exception as exc:
        _msg("VassalOps", f"Failed to start bootstrap:\n{exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
