"""UTF-8-safe console helpers for Windows cp1252 / pythonw."""

from __future__ import annotations

import sys
from typing import Any, Optional, TextIO


def configure_utf8_stdio() -> None:
    """Prefer UTF-8 on stdout/stderr so Unicode logs do not raise on Windows."""
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def safe_print(*args: Any, sep: str = " ", end: str = "\n", file: Optional[TextIO] = None) -> None:
    """print() that never raises UnicodeEncodeError (pythonw / cp1252 safe)."""
    stream = file if file is not None else sys.stdout
    if stream is None:
        return
    text = sep.join(str(a) for a in args) + end
    try:
        stream.write(text)
        stream.flush()
    except UnicodeEncodeError:
        encoding = getattr(stream, "encoding", None) or "utf-8"
        raw = text.encode(encoding, errors="replace")
        buffer = getattr(stream, "buffer", None)
        if buffer is not None:
            try:
                buffer.write(raw)
                buffer.flush()
                return
            except Exception:
                pass
        try:
            stream.write(raw.decode(encoding, errors="replace"))
            stream.flush()
        except Exception:
            pass
    except Exception:
        pass
