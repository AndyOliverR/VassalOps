"""Redacted markdown run reports (HITL evidence pack, not pentest PoCs)."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from src.ingestion.secret_redactor import redact_secrets


RUNS_DIR = os.path.join("storage", "runs")


def write_run_report(
    *,
    goal: str,
    ok: bool,
    turns: int = 0,
    observations: Optional[List[str]] = None,
    final: str = "",
    reason: str = "",
    kind: str = "agent_loop",
    runs_dir: str = RUNS_DIR,
) -> str:
    os.makedirs(runs_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(runs_dir, f"{stamp}.md")
    status = "OK" if ok else "FAIL"
    lines = [
        f"# VassalOps run {stamp}",
        "",
        f"- **Kind:** {kind}",
        f"- **Status:** {status}",
        f"- **Turns:** {turns}",
        f"- **Goal:** {redact_secrets(goal or '')}",
        f"- **Reason:** {redact_secrets(reason or '')}",
        "",
        "## Observations",
    ]
    obs = observations or []
    if not obs:
        lines.append("(none)")
    else:
        for item in obs:
            lines.append(f"- {redact_secrets(str(item))}")
    lines.extend(["", "## Final", redact_secrets(final or "(none)"), ""])
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path.replace("\\", "/")
