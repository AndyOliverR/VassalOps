"""Hermetic checks for Windows cp1252-safe console printing."""
from __future__ import annotations

import io
import unittest

from src.execution.console_io import safe_print
from src.execution.run_controller import VassalOpsRunController


class _StrictCp1252IO(io.TextIOBase):
    """Text stream that rejects Unicode arrows like real Windows charmap stdout."""

    encoding = "cp1252"

    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []

    def write(self, s: str) -> int:  # type: ignore[override]
        s.encode("cp1252", errors="strict")
        self.chunks.append(s)
        return len(s)

    def flush(self) -> None:
        return None


class TestConsoleEncoding(unittest.TestCase):
    def test_safe_print_survives_arrow_on_cp1252(self):
        stream = _StrictCp1252IO()
        # Would raise UnicodeEncodeError with print(..., file=stream)
        with self.assertRaises(UnicodeEncodeError):
            stream.write("think \u2192 tool")
        safe_print("think \u2192 tool \u2192 observe", file=stream)
        joined = "".join(stream.chunks)
        self.assertIn("think", joined)
        self.assertIn("tool", joined)

    def test_finish_if_active_preserves_first_error(self):
        ctl = VassalOpsRunController()
        ctl.reset_for_run(["step"], phase="test")
        ctl.set_summary("Hit max_turns=14 without a final answer.")
        ctl.finish(False, "Hit max_turns=14 without a final answer.")
        first = ctl.snapshot()
        self.assertEqual(first["status"], "done")
        self.assertEqual(first["last_error"], "Hit max_turns=14 without a final answer.")

        applied = ctl.finish_if_active(
            False,
            "'charmap' codec can't encode character '\\u2192'",
        )
        self.assertFalse(applied)
        second = ctl.snapshot()
        self.assertEqual(second["last_error"], "Hit max_turns=14 without a final answer.")
        self.assertIn("max_turns", second["summary"])


if __name__ == "__main__":
    unittest.main()
