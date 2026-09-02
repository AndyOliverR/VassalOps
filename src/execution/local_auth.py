"""Local-only PIN gate: email + hashed PIN + secret Q/A for reset."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import time
import uuid
from typing import Any, Callable, Dict, Optional, Tuple

import requests

AUTH_DIR = os.path.join("storage", "auth")
PROFILE_PATH = os.path.join(AUTH_DIR, "profile.json")
PBKDF2_ITERATIONS = 200_000
PIN_RE = re.compile(r"^\d{4,8}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

DEFAULT_QUESTIONS = [
    "What city were you born in?",
    "What was the name of your first pet?",
    "What is your mother's maiden name?",
    "What was your first school?",
    "Custom…",
]


def _workspace_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def profile_path(root: Optional[str] = None) -> str:
    base = root if root is not None else _workspace_root()
    return os.path.join(base, AUTH_DIR, "profile.json")


def _ensure_auth_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _new_salt() -> str:
    return secrets.token_hex(16)


def _hash_secret(value: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        value.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return digest.hex()


def _verify(value: str, salt: str, expected_hex: str) -> bool:
    got = _hash_secret(value, salt)
    return hmac.compare_digest(got, expected_hex)


def normalize_answer(answer: str) -> str:
    return (answer or "").strip().lower()


def validate_pin(pin: str) -> Tuple[bool, str]:
    if not PIN_RE.match(pin or ""):
        return False, "PIN must be 4–8 digits."
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    e = (email or "").strip()
    if not EMAIL_RE.match(e):
        return False, "Enter a valid email address."
    return True, ""


def mask_email(email: str) -> str:
    e = (email or "").strip()
    if "@" not in e:
        return "***"
    local, _, domain = e.partition("@")
    if len(local) <= 1:
        shown = "*"
    else:
        shown = local[0] + "***"
    return f"{shown}@{domain}"


def load_profile(root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    path = profile_path(root)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


def save_profile(data: Dict[str, Any], root: Optional[str] = None) -> None:
    path = profile_path(root)
    _ensure_auth_dir(path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def has_profile(root: Optional[str] = None) -> bool:
    return load_profile(root) is not None


def read_app_version(root: Optional[str] = None) -> str:
    base = root if root is not None else _workspace_root()
    path = os.path.join(base, "VERSION")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip() or "0.0.0"
    except Exception:
        return "0.0.0"


def _deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for key, val in (overlay or {}).items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def load_merged_config(root: Optional[str] = None) -> Dict[str, Any]:
    """Load config.json then overlay config.local.json (secrets stay out of git)."""
    base = root if root is not None else _workspace_root()
    merged: Dict[str, Any] = {}
    for name in ("config.json", "config.local.json"):
        path = os.path.join(base, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                merged = _deep_merge(merged, data)
        except Exception:
            continue
    return merged


def registration_settings(root: Optional[str] = None) -> Dict[str, str]:
    rb = (load_merged_config(root).get("runtime_boundaries") or {})
    return {
        "endpoint": str(rb.get("registration_endpoint") or "").strip(),
        "github_repo": str(rb.get("registration_github_repo") or "").strip(),
        "github_token": str(rb.get("registration_github_token") or "").strip(),
    }


def registration_endpoint_from_config(root: Optional[str] = None) -> str:
    return registration_settings(root)["endpoint"]


def _install_payload(email: str, install_id: str, version: str) -> Dict[str, str]:
    return {
        "app": "VassalOps",
        "email": email,
        "install_id": install_id,
        "version": version,
    }


def _github_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {(token or '').strip()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "VassalOps-Handshake",
    }


def _response_json(resp: Any) -> Dict[str, Any]:
    try:
        data = resp.json() if callable(getattr(resp, "json", None)) else {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _issue_number_from_response(resp: Any) -> Optional[int]:
    raw = _response_json(resp).get("number")
    return raw if isinstance(raw, int) and raw > 0 else None


def post_github_issue(
    *,
    repo: str,
    token: str,
    title: str,
    body: str,
    post: Optional[Callable[..., Any]] = None,
    timeout: float = 8.0,
) -> Tuple[bool, str, Optional[int]]:
    """Create an Issue on the installs notepad repo. Returns (ok, message, number)."""
    repo_s = (repo or "").strip().strip("/")
    token_s = (token or "").strip()
    if not repo_s or not token_s:
        return False, "GitHub registration not configured (repo/token).", None
    if repo_s.count("/") != 1:
        return False, "registration_github_repo must look like owner/name.", None
    url = f"https://api.github.com/repos/{repo_s}/issues"
    http_post = post or requests.post
    try:
        resp = http_post(
            url,
            json={"title": title, "body": body},
            headers=_github_headers(token_s),
            timeout=timeout,
        )
        code = int(getattr(resp, "status_code", 0))
        if 200 <= code < 300:
            return True, "Noted on GitHub Issues notepad.", _issue_number_from_response(resp)
        return False, f"GitHub Issues ping failed (HTTP {code}).", None
    except Exception as exc:
        return False, f"GitHub Issues ping skipped: {exc}", None


def post_github_comment(
    *,
    repo: str,
    token: str,
    issue_number: int,
    body: str,
    post: Optional[Callable[..., Any]] = None,
    timeout: float = 8.0,
) -> Tuple[bool, str]:
    repo_s = (repo or "").strip().strip("/")
    token_s = (token or "").strip()
    if not repo_s or not token_s or issue_number <= 0:
        return False, "GitHub comment not configured."
    url = f"https://api.github.com/repos/{repo_s}/issues/{int(issue_number)}/comments"
    http_post = post or requests.post
    try:
        resp = http_post(
            url,
            json={"body": body},
            headers=_github_headers(token_s),
            timeout=timeout,
        )
        code = int(getattr(resp, "status_code", 0))
        if 200 <= code < 300:
            return True, "Handshake comment posted."
        return False, f"GitHub comment failed (HTTP {code})."
    except Exception as exc:
        return False, f"GitHub comment skipped: {exc}"


def try_github_issue_register(
    *,
    email: str,
    install_id: str,
    version: str,
    repo: str,
    token: str,
    post: Optional[Callable[..., Any]] = None,
    timeout: float = 8.0,
) -> Tuple[bool, str]:
    """Create one private-repo Issue as the installs notepad. Returns (ok, message)."""
    payload = _install_payload(email, install_id, version)
    ok, msg, _number = post_github_issue(
        repo=repo,
        token=token,
        title=f"install: {email}",
        body="```json\n" + json.dumps(payload, indent=2) + "\n```\n",
        post=post,
        timeout=timeout,
    )
    if ok:
        return True, "Install noted on GitHub Issues notepad."
    return False, msg


def try_github_issue_register_ex(
    *,
    email: str,
    install_id: str,
    version: str,
    repo: str,
    token: str,
    post: Optional[Callable[..., Any]] = None,
    timeout: float = 8.0,
) -> Tuple[bool, str, Optional[int]]:
    payload = _install_payload(email, install_id, version)
    ok, msg, number = post_github_issue(
        repo=repo,
        token=token,
        title=f"install: {email}",
        body="```json\n" + json.dumps(payload, indent=2) + "\n```\n",
        post=post,
        timeout=timeout,
    )
    if ok:
        return True, "Install noted on GitHub Issues notepad.", number
    return False, msg, None


def try_oneshot_register(
    *,
    email: str,
    install_id: str,
    version: str,
    endpoint: str = "",
    github_repo: str = "",
    github_token: str = "",
    post: Optional[Callable[..., Any]] = None,
    timeout: float = 8.0,
) -> Tuple[bool, str]:
    """Prefer GitHub Issues notepad; else generic HTTPS POST. No-op if neither configured."""
    if (github_repo or "").strip() and (github_token or "").strip():
        ok, msg, _number = try_github_issue_register_ex(
            email=email,
            install_id=install_id,
            version=version,
            repo=github_repo,
            token=github_token,
            post=post,
            timeout=timeout,
        )
        return ok, msg
    url = (endpoint or "").strip()
    if not url:
        return False, "No registration target configured (local only)."
    payload = _install_payload(email, install_id, version)
    http_post = post or requests.post
    try:
        resp = http_post(url, json=payload, timeout=timeout)
        if 200 <= int(getattr(resp, "status_code", 0)) < 300:
            return True, "Registration ping sent."
        return False, f"Registration ping failed (HTTP {getattr(resp, 'status_code', '?')})."
    except Exception as exc:
        return False, f"Registration ping skipped: {exc}"


def covenant_complete(profile: Optional[Dict[str, Any]]) -> bool:
    if not profile:
        return False
    cov = profile.get("covenant")
    return isinstance(cov, dict) and bool(cov.get("completed_at"))


def _stamp_register_success(profile: Dict[str, Any], issue_number: Optional[int] = None) -> None:
    profile["registered_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if isinstance(issue_number, int) and issue_number > 0:
        profile["github_issue_number"] = issue_number


def _register_profile(
    profile: Dict[str, Any],
    root: Optional[str] = None,
    *,
    post: Optional[Callable[..., Any]] = None,
) -> Tuple[bool, str]:
    settings = registration_settings(root)
    version = read_app_version(root)
    email = str(profile.get("email") or "")
    install_id = str(profile.get("install_id") or "")
    if (settings["github_repo"] and settings["github_token"]):
        ping_ok, ping_msg, number = try_github_issue_register_ex(
            email=email,
            install_id=install_id,
            version=version,
            repo=settings["github_repo"],
            token=settings["github_token"],
            post=post,
        )
        if ping_ok:
            _stamp_register_success(profile, number)
            save_profile(profile, root)
        return ping_ok, ping_msg
    ping_ok, ping_msg = try_oneshot_register(
        email=email,
        install_id=install_id,
        version=version,
        endpoint=settings["endpoint"],
        post=post,
    )
    if ping_ok:
        _stamp_register_success(profile)
        save_profile(profile, root)
    return ping_ok, ping_msg


def maybe_register_pending(
    root: Optional[str] = None,
    *,
    post: Optional[Callable[..., Any]] = None,
) -> Dict[str, Any]:
    """
    If a local profile exists and is not yet registered, try one-shot register once.
    Idempotent when registered_at is already set.
    """
    profile = load_profile(root)
    if not profile:
        return {"ok": False, "skipped": True, "reason": "no_profile"}
    if profile.get("registered_at"):
        return {"ok": True, "skipped": True, "reason": "already_registered"}
    settings = registration_settings(root)
    if not (
        (settings["github_repo"] and settings["github_token"])
        or settings["endpoint"]
    ):
        return {"ok": False, "skipped": True, "reason": "not_configured"}
    email = str(profile.get("email") or "")
    install_id = str(profile.get("install_id") or "")
    if not email or not install_id:
        return {"ok": False, "skipped": True, "reason": "incomplete_profile"}
    ping_ok, ping_msg = _register_profile(profile, root, post=post)
    return {
        "ok": ping_ok,
        "skipped": False,
        "message": ping_msg,
        "registered": ping_ok,
    }


class LocalAuthSession:
    """Process-lifetime unlock state + profile ops."""

    def __init__(self, root: Optional[str] = None) -> None:
        self.root = root
        self._unlocked = False

    @property
    def unlocked(self) -> bool:
        return self._unlocked

    def lock(self) -> None:
        self._unlocked = False

    def status(self) -> Dict[str, Any]:
        profile = load_profile(self.root)
        has = profile is not None
        email = str((profile or {}).get("email") or "")
        return {
            "unlocked": self._unlocked,
            "has_profile": has,
            "email_masked": mask_email(email) if has else "",
            "question": str((profile or {}).get("question") or "") if has else "",
            "registered": bool((profile or {}).get("registered_at")),
            "covenant_complete": covenant_complete(profile),
            "default_questions": list(DEFAULT_QUESTIONS),
        }

    def _ping_after_save(self, profile: Dict[str, Any]) -> Tuple[bool, str]:
        return _register_profile(profile, self.root)

    def complete_covenant(
        self,
        *,
        sponsored: bool,
        starred: bool,
        rating: str,
        post: Optional[Callable[..., Any]] = None,
    ) -> Dict[str, Any]:
        if not self._unlocked:
            return {"ok": False, "error": UNLOCK_REQUIRED}
        profile = load_profile(self.root)
        if not profile:
            return {"ok": False, "error": "No local account yet."}
        if not sponsored:
            return {"ok": False, "error": "Sponsor any amount on GitHub Sponsors, then tick the box."}
        if not starred:
            return {"ok": False, "error": "Star the public VassalOps repo on GitHub, then tick the box."}
        rate = (rating or "").strip()
        if rate not in {"1", "2", "3", "4", "5"}:
            return {"ok": False, "error": "Choose a 1–5 rating so other operators can see how we are doing."}

        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        profile["covenant"] = {
            "sponsored_claimed": True,
            "starred_claimed": True,
            "rating": rate,
            "completed_at": now,
            "handshake_consent": True,
        }
        save_profile(profile, self.root)

        settings = registration_settings(self.root)
        ping_msg = "Covenant saved locally."
        issue_number = profile.get("github_issue_number")
        if settings["github_repo"] and settings["github_token"]:
            body = (
                "Lab-rat covenant completed.\n\n"
                "```json\n"
                + json.dumps(
                    {
                        "email": profile.get("email"),
                        "install_id": profile.get("install_id"),
                        "version": read_app_version(self.root),
                        "sponsored_claimed": True,
                        "starred_claimed": True,
                        "rating": rate,
                        "completed_at": now,
                    },
                    indent=2,
                )
                + "\n```\n"
            )
            if isinstance(issue_number, int) and issue_number > 0:
                ok, ping_msg = post_github_comment(
                    repo=settings["github_repo"],
                    token=settings["github_token"],
                    issue_number=issue_number,
                    body=body,
                    post=post,
                )
            else:
                ok, ping_msg, number = post_github_issue(
                    repo=settings["github_repo"],
                    token=settings["github_token"],
                    title=f"covenant: {profile.get('email')}",
                    body=body,
                    post=post,
                )
                if ok and number:
                    profile["github_issue_number"] = number
                    save_profile(profile, self.root)
            if not ok:
                ping_msg = "Covenant saved locally. " + ping_msg

        return {
            "ok": True,
            "covenant_complete": True,
            "message": ping_msg,
        }

    def signup(self, email: str, pin: str, question: str, answer: str) -> Dict[str, Any]:
        if has_profile(self.root):
            return {"ok": False, "error": "A local account already exists. Unlock with your PIN."}
        ok_e, err_e = validate_email(email)
        if not ok_e:
            return {"ok": False, "error": err_e}
        ok_p, err_p = validate_pin(pin)
        if not ok_p:
            return {"ok": False, "error": err_p}
        q = (question or "").strip()
        if not q or q == "Custom…":
            return {"ok": False, "error": "Choose or type a secret question."}
        ans = normalize_answer(answer)
        if len(ans) < 2:
            return {"ok": False, "error": "Secret answer is too short."}

        salt = _new_salt()
        install_id = str(uuid.uuid4())
        email_s = email.strip()
        profile = {
            "email": email_s,
            "salt": salt,
            "pin_hash": _hash_secret(pin, salt),
            "question": q,
            "answer_hash": _hash_secret(ans, salt),
            "install_id": install_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "registered_at": None,
        }
        save_profile(profile, self.root)

        ping_ok, ping_msg = self._ping_after_save(profile)

        self._unlocked = True
        return {
            "ok": True,
            "unlocked": True,
            "email_masked": mask_email(email_s),
            "registration": ping_msg,
            "registered": ping_ok,
            "covenant_complete": False,
        }

    def unlock(self, pin: str) -> Dict[str, Any]:
        profile = load_profile(self.root)
        if not profile:
            return {"ok": False, "error": "No local account yet. Create one first."}
        ok_p, err_p = validate_pin(pin)
        if not ok_p:
            return {"ok": False, "error": err_p}
        if not _verify(pin, str(profile.get("salt") or ""), str(profile.get("pin_hash") or "")):
            return {"ok": False, "error": "Incorrect PIN."}
        self._unlocked = True
        return {
            "ok": True,
            "unlocked": True,
            "email_masked": mask_email(str(profile.get("email") or "")),
            "covenant_complete": covenant_complete(profile),
        }

    def reset_pin(self, answer: str, new_pin: str) -> Dict[str, Any]:
        profile = load_profile(self.root)
        if not profile:
            return {"ok": False, "error": "No local account yet."}
        ok_p, err_p = validate_pin(new_pin)
        if not ok_p:
            return {"ok": False, "error": err_p}
        salt = str(profile.get("salt") or "")
        if not _verify(normalize_answer(answer), salt, str(profile.get("answer_hash") or "")):
            return {"ok": False, "error": "Secret answer did not match."}
        profile["pin_hash"] = _hash_secret(new_pin, salt)
        save_profile(profile, self.root)
        self._unlocked = True
        return {
            "ok": True,
            "unlocked": True,
            "message": "PIN updated. You are unlocked.",
            "covenant_complete": covenant_complete(profile),
        }

    def change_pin(self, current_pin: str, new_pin: str) -> Dict[str, Any]:
        if not self._unlocked:
            return {"ok": False, "error": "Unlock VassalOps first."}
        profile = load_profile(self.root)
        if not profile:
            return {"ok": False, "error": "No local account yet."}
        ok_p, err_p = validate_pin(new_pin)
        if not ok_p:
            return {"ok": False, "error": err_p}
        salt = str(profile.get("salt") or "")
        if not _verify(current_pin, salt, str(profile.get("pin_hash") or "")):
            return {"ok": False, "error": "Current PIN is incorrect."}
        profile["pin_hash"] = _hash_secret(new_pin, salt)
        save_profile(profile, self.root)
        return {"ok": True, "message": "PIN changed."}

    def change_secret(self, pin: str, question: str, answer: str) -> Dict[str, Any]:
        if not self._unlocked:
            return {"ok": False, "error": "Unlock VassalOps first."}
        profile = load_profile(self.root)
        if not profile:
            return {"ok": False, "error": "No local account yet."}
        salt = str(profile.get("salt") or "")
        if not _verify(pin, salt, str(profile.get("pin_hash") or "")):
            return {"ok": False, "error": "PIN is incorrect."}
        q = (question or "").strip()
        if not q or q == "Custom…":
            return {"ok": False, "error": "Choose or type a secret question."}
        ans = normalize_answer(answer)
        if len(ans) < 2:
            return {"ok": False, "error": "Secret answer is too short."}
        profile["question"] = q
        profile["answer_hash"] = _hash_secret(ans, salt)
        save_profile(profile, self.root)
        return {"ok": True, "message": "Secret question updated."}


# Process-wide session used by the dashboard API.
local_auth = LocalAuthSession()

UNLOCK_REQUIRED = "Unlock VassalOps first (enter your PIN)."
