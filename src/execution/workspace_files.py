"""Workspace-bounded path helpers for coding-lite agent tools."""

from __future__ import annotations

import os
from typing import List, Tuple


def workspace_root() -> str:
    # Repo root: .../src/execution -> parents[2]
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def resolve_workspace_path(relative: str) -> Tuple[bool, str, str]:
    """
    Resolve a path under the workspace root.
    Returns (ok, abs_path, error_message).
    """
    root = workspace_root()
    rel = (relative or "").strip().replace("\\", "/")
    if not rel or rel.startswith("/") or re_drive(rel):
        return False, "", "Path must be relative to the VassalOps workspace."
    if ".." in rel.split("/"):
        return False, "", "Path must not contain '..'."
    abs_path = os.path.abspath(os.path.join(root, rel.replace("/", os.sep)))
    root_norm = os.path.normcase(root)
    path_norm = os.path.normcase(abs_path)
    if path_norm != root_norm and not path_norm.startswith(root_norm + os.sep):
        return False, "", "Path escapes the VassalOps workspace."
    return True, abs_path, ""


def re_drive(rel: str) -> bool:
    return len(rel) >= 2 and rel[1] == ":"


def list_workspace_dir(relative: str = ".", *, limit: int = 80) -> str:
    ok, path, err = resolve_workspace_path(relative if relative not in ("", ".") else ".")
    if relative in ("", "."):
        path = workspace_root()
        ok = True
        err = ""
    if not ok:
        return f"list_dir error: {err}"
    if not os.path.isdir(path):
        return f"list_dir error: not a directory: {relative}"
    names = sorted(os.listdir(path))
    lines: List[str] = []
    for name in names[:limit]:
        full = os.path.join(path, name)
        kind = "dir" if os.path.isdir(full) else "file"
        lines.append(f"{kind}\t{name}")
    more = "" if len(names) <= limit else f"\n… {len(names) - limit} more"
    return f"list_dir {relative or '.'} ({len(names)} entries):\n" + "\n".join(lines) + more


def read_workspace_file(relative: str, *, max_chars: int = 12000) -> str:
    ok, path, err = resolve_workspace_path(relative)
    if not ok:
        return f"read_file error: {err}"
    if not os.path.isfile(path):
        return f"read_file error: not a file: {relative}"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read(max_chars + 1)
    except Exception as exc:
        return f"read_file error: {exc}"
    if len(text) > max_chars:
        return text[:max_chars] + "\n…[truncated]"
    return text


def write_workspace_file(relative: str, content: str, *, approved: bool = False) -> str:
    if not approved:
        return "write_file blocked: requires human Approve (set approved flag after Approve)."
    ok, path, err = resolve_workspace_path(relative)
    if not ok:
        return f"write_file error: {err}"
    parent = os.path.dirname(path)
    try:
        os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content if content is not None else "")
    except Exception as exc:
        return f"write_file error: {exc}"
    return f"write_file ok: wrote {len(content or '')} chars to {relative}"
