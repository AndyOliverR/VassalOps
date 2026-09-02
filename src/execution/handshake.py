"""Launch/close handshake: send sanitized skills, receive product updates."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from typing import Any, Callable, Dict, Optional

from src.execution.local_auth import (
    load_merged_config,
    load_profile,
    post_github_comment,
    post_github_issue,
    read_app_version,
    registration_settings,
    save_profile,
)
from src.execution.product_update import (
    apply_pending_update,
    apply_release_zip,
    fetch_latest_release,
    find_release_zip_url,
    is_newer_version,
    read_app_version as read_version,
    stage_pending_update,
)
from src.execution.skill_distillate import build_skill_distillate


STATE_NAME = os.path.join("storage", "auth", "handshake_state.json")
SEND_DEBOUNCE_SEC = 120


def _workspace_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def handshake_enabled(root: Optional[str] = None) -> bool:
    if os.environ.get("VASSALOPS_SKIP_HANDSHAKE") == "1":
        return False
    cfg = load_merged_config(root)
    handshake = cfg.get("handshake")
    if isinstance(handshake, dict) and handshake.get("enabled") is False:
        return False
    return True


def product_update_enabled() -> bool:
    return os.environ.get("VASSALOPS_SKIP_UPDATE") != "1"


def _state_path(root: str) -> str:
    return os.path.join(root, STATE_NAME)


def load_handshake_state(root: str) -> Dict[str, Any]:
    path = _state_path(root)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_handshake_state(root: str, data: Dict[str, Any]) -> None:
    path = _state_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def _product_repo(root: Optional[str] = None) -> str:
    cfg = load_merged_config(root)
    handshake = cfg.get("handshake") if isinstance(cfg.get("handshake"), dict) else {}
    repo = str((handshake or {}).get("product_repo") or "").strip()
    return repo or "AndyOliverR/VassalOps"


def _learn_target(root: Optional[str] = None) -> Dict[str, str]:
    settings = registration_settings(root)
    cfg = load_merged_config(root)
    handshake = cfg.get("handshake") if isinstance(cfg.get("handshake"), dict) else {}
    repo = str((handshake or {}).get("learn_repo") or "").strip() or settings["github_repo"]
    return {"repo": repo, "token": settings["github_token"]}


def _fingerprint(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def _should_send(
    *,
    reason: str,
    fingerprint: str,
    state: Dict[str, Any],
) -> bool:
    last_fp = str(state.get("last_fingerprint") or "")
    last_at = str(state.get("last_send_at") or "")
    if fingerprint != last_fp:
        return True
    if reason == "close":
        return False
    try:
        last_epoch = time.mktime(time.strptime(last_at, "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return True
    return (time.time() - last_epoch) >= SEND_DEBOUNCE_SEC


def send_skill_update(
    root: str,
    *,
    reason: str,
    post: Optional[Callable[..., Any]] = None,
) -> Dict[str, Any]:
    profile = load_profile(root)
    if not profile or not str(profile.get("install_id") or "").strip():
        return {"ok": False, "skipped": True, "reason": "no_profile"}
    version = read_app_version(root)
    distillate = build_skill_distillate(
        root,
        install_id=str(profile.get("install_id") or ""),
        version=version,
        reason=reason,
    )
    fingerprint = _fingerprint(distillate)
    state = load_handshake_state(root)
    if not _should_send(reason=reason, fingerprint=fingerprint, state=state):
        return {
            "ok": True,
            "skipped": True,
            "reason": "unchanged",
            "fingerprint": fingerprint,
            "duty_count": distillate.get("duty_count", 0),
        }
    target = _learn_target(root)
    if not target["repo"] or not target["token"]:
        return {"ok": False, "skipped": True, "reason": "not_configured"}

    body = (
        f"Handshake `{reason}` from VassalOps {version}.\n\n"
        "Sanitized skill distillate (no documents, keystrokes, screens, or inventory):\n\n"
        "```json\n"
        + json.dumps(distillate, indent=2)
        + "\n```\n"
    )
    issue_number = profile.get("github_issue_number") or state.get("learn_issue_number")
    sent_ok = False
    message = ""
    used_number = None
    if isinstance(issue_number, int) and issue_number > 0:
        sent_ok, message = post_github_comment(
            repo=target["repo"],
            token=target["token"],
            issue_number=issue_number,
            body=body,
            post=post,
        )
        used_number = issue_number
    if not sent_ok:
        title = f"learn: {profile.get('install_id') or 'install'} {version}"
        sent_ok, message, used_number = post_github_issue(
            repo=target["repo"],
            token=target["token"],
            title=title,
            body=body,
            post=post,
        )
        if sent_ok and used_number:
            profile["github_issue_number"] = used_number
            save_profile(profile, root)

    if sent_ok:
        state.update(
            {
                "last_send_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "last_send_reason": reason,
                "last_fingerprint": fingerprint,
                "learn_issue_number": used_number or state.get("learn_issue_number"),
            }
        )
        save_handshake_state(root, state)
    return {
        "ok": sent_ok,
        "skipped": False,
        "message": message,
        "duty_count": distillate.get("duty_count", 0),
        "issue_number": used_number,
        "fingerprint": fingerprint,
    }


def receive_product_update(
    root: str,
    *,
    apply_now: bool,
    stage_if_busy: bool,
    get: Optional[Callable[..., Any]] = None,
) -> Dict[str, Any]:
    pending = apply_pending_update(root)
    if pending.get("applied"):
        return {
            "ok": True,
            "applied": True,
            "staged": False,
            "version": pending.get("version"),
            "message": f"Applied staged update {pending.get('version')}.",
        }

    local = read_version(root)
    cfg = load_merged_config(root)
    rb = cfg.get("runtime_boundaries") if isinstance(cfg.get("runtime_boundaries"), dict) else {}
    token = str((rb or {}).get("registration_github_token") or "")
    ok, err, release = fetch_latest_release(_product_repo(root), token=token, get=get)
    if not ok:
        return {"ok": False, "applied": False, "staged": False, "message": err, "local": local}
    tag = str(release.get("tag_name") or "")
    remote = tag.lstrip("v").strip()
    if not remote or not is_newer_version(remote, local):
        return {
            "ok": True,
            "applied": False,
            "staged": False,
            "local": local,
            "latest": remote or local,
            "message": f"Already on {local}.",
        }
    zip_url = find_release_zip_url(release, remote)
    if not zip_url:
        return {
            "ok": False,
            "applied": False,
            "staged": False,
            "local": local,
            "latest": remote,
            "message": f"Update {remote} has no zip asset.",
        }
    if apply_now:
        result = apply_release_zip(root, zip_url, remote)
        result["local"] = local
        result["latest"] = remote
        if result.get("ok"):
            result["message"] = f"Updated VassalOps {local} → {remote}."
        else:
            result["message"] = result.get("reason") or "Update apply failed."
        return result
    if stage_if_busy:
        try:
            stage_pending_update(root, zip_url, remote)
            return {
                "ok": True,
                "applied": False,
                "staged": True,
                "local": local,
                "latest": remote,
                "message": f"Staged {remote} to apply after VassalOps exits.",
            }
        except Exception as exc:
            return {
                "ok": False,
                "applied": False,
                "staged": False,
                "local": local,
                "latest": remote,
                "message": f"Could not stage update: {exc}",
            }
    return {
        "ok": True,
        "applied": False,
        "staged": False,
        "local": local,
        "latest": remote,
        "message": f"{remote} is available (not applied while the app is running).",
    }


def spawn_apply_after_exit(root: str, pid: int) -> bool:
    script = os.path.join(root, "tools", "apply_pending_after_exit.ps1")
    if not os.path.isfile(script):
        return False
    python_exe = sys.executable or "python"
    args = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        script,
        "-Root",
        root,
        "-WaitPid",
        str(pid),
        "-Python",
        python_exe,
    ]
    kwargs: Dict[str, Any] = {
        "cwd": root,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000
    try:
        subprocess.Popen(args, **kwargs)
        return True
    except Exception:
        return False


def run_handshake(
    *,
    reason: str = "launch",
    apply_product: bool = False,
    stage_product: bool = False,
    root: Optional[str] = None,
    post: Optional[Callable[..., Any]] = None,
    get: Optional[Callable[..., Any]] = None,
    spawn_waiter: bool = False,
) -> Dict[str, Any]:
    base = root if root is not None else _workspace_root()
    if not handshake_enabled(base):
        return {"ok": True, "skipped": True, "reason": "disabled", "message": "Handshake skipped."}

    sent = send_skill_update(base, reason=reason, post=post)
    if product_update_enabled():
        received = receive_product_update(
            base,
            apply_now=apply_product,
            stage_if_busy=stage_product,
            get=get,
        )
    else:
        received = {
            "ok": True,
            "applied": False,
            "staged": False,
            "message": "Product update skipped (VASSALOPS_SKIP_UPDATE=1).",
        }
    if received.get("staged") and spawn_waiter:
        spawn_apply_after_exit(base, os.getpid())

    parts = []
    if sent.get("skipped") and sent.get("reason") == "no_profile":
        parts.append("Learning share waits until the local PIN account exists.")
    elif sent.get("skipped") and sent.get("reason") == "unchanged":
        parts.append("No new skill shapes to send.")
    elif sent.get("ok"):
        parts.append(f"Sent {sent.get('duty_count', 0)} skill shapes.")
    elif sent.get("skipped"):
        parts.append("Learning share skipped (not configured).")
    else:
        parts.append(sent.get("message") or "Could not send skill shapes.")

    if received.get("message"):
        parts.append(str(received["message"]))

    ok = bool(received.get("ok") or sent.get("ok") or sent.get("skipped"))
    return {
        "ok": ok,
        "reason": reason,
        "sent": sent,
        "received": received,
        "message": " ".join(parts).strip(),
        "needs_restart": bool(received.get("applied")),
    }
