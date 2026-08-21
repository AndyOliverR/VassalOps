"""
Best-effort intent guardrails for VassalOps.

Refuses high-severity harmful goals (terrorism, violent crime planning, CSAM,
non-consensual sexual exploitation, fraud/credential theft, critical-infrastructure
sabotage). Warns the user, logs a local refusal, and shuts the app down.

This is friction + policy enforcement on a local agent — not a guarantee against
determined adversaries who patch or bypass the software.
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple


REFUSAL_DIR = os.path.join("storage", "runs")

# High-severity phrase/keyword patterns (lowercase). Keep specific to limit false positives.
_RULES: List[Tuple[str, str, re.Pattern]] = [
    # Child sexual exploitation / CSAM
    (
        "child_exploitation",
        "Content involving sexual exploitation of minors is forbidden.",
        re.compile(
            r"\b("
            r"csam|child\s*porn|child\s*sex|underage\s*sex|pedo(?:phile)?|lolita|"
            r"sexual(?:ly)?\s+(?:with\s+)?(?:a\s+)?(?:child|minor|kid|kids|under\s*1[0-7])|"
            r"(?:child|minor|kid)s?\s+(?:porn|nude|nudes|sex)"
            r")\b",
            re.I,
        ),
    ),
    # Terrorism / mass violence
    (
        "terrorism_violence",
        "Planning terrorism or mass-casualty violence is forbidden.",
        re.compile(
            r"\b("
            r"terrorist|terrorism|bomb\s*threat|build\s+(?:a\s+)?bomb|make\s+(?:a\s+)?bomb|"
            r"mass\s*shooting|school\s*shooting|kill\s+(?:everyone|civilians|people)|"
            r"assassinate|behead(?:ing)?|suicide\s*bomb|ied\b|pipe\s*bomb|"
            r"how\s+to\s+(?:make|build)\s+(?:an?\s+)?(?:explosive|bomb|weapon)"
            r")\b",
            re.I,
        ),
    ),
    # Fraud / credential theft / phishing
    (
        "fraud_theft",
        "Fraud, phishing, and credential theft automation is forbidden.",
        re.compile(
            r"\b("
            r"steal\s+(?:passwords?|credentials?|otp|2fa|credit\s*cards?)|"
            r"phishing\s+(?:kit|page|email|campaign)|credential\s*stuff|"
            r"keylogger|ransomware|dark\s*web\s+market|"
            r"bypass\s+(?:bank|2fa|mfa)\s+(?:for\s+)?(?:fraud|theft)|"
            r"scrape\s+(?:and\s+)?sell\s+(?:ssn|social\s*security|cards?)"
            r")\b",
            re.I,
        ),
    ),
    # Non-consensual sexual / voyeurism / revenge porn
    (
        "nonconsensual_sexual",
        "Non-consensual sexual targeting or image abuse is forbidden.",
        re.compile(
            r"\b("
            r"revenge\s*porn|non[-\s]?consensual\s+(?:sex|nude|intimate)|"
            r"hidden\s*camera\s+(?:in\s+)?(?:bathroom|bedroom|shower)|"
            r"spy\s+on\s+(?:her|him|them)\s+(?:naked|undress|shower)|"
            r"upskirt|deepfake\s+(?:porn|nude|sex)\s+(?:of|without)"
            r")\b",
            re.I,
        ),
    ),
    # Critical infrastructure / sabotage / espionage tooling via desktop agent
    (
        "critical_sabotage",
        "Sabotage of critical infrastructure or espionage automation is forbidden.",
        re.compile(
            r"\b("
            r"sabotage\s+(?:power\s*grid|water\s*plant|airport|hospital|rail)|"
            r"attack\s+(?:the\s+)?(?:power\s*grid|scada|nuclear\s*plant)|"
            r"disable\s+(?:emergency\s+)?(?:911|hospital\s+systems)|"
            r"exfiltrate\s+(?:classified|state\s+secrets)|"
            r"espionage\s+(?:against|on)\s+(?:government|military)"
            r")\b",
            re.I,
        ),
    ),
]


def assess_intent(text: str) -> Dict[str, Any]:
    """
    Return {allowed: bool, category, reason, matched}.
    Keyword/phrase path only (hermetic, no network).
    """
    raw = (text or "").strip()
    if not raw:
        return {"allowed": True, "category": "", "reason": "", "matched": ""}

    for category, reason, pattern in _RULES:
        m = pattern.search(raw)
        if m:
            return {
                "allowed": False,
                "category": category,
                "reason": reason,
                "matched": m.group(0)[:80],
            }
    return {"allowed": True, "category": "", "reason": "", "matched": ""}


def write_refusal_log(assessment: Dict[str, Any], source: str = "chat") -> str:
    os.makedirs(REFUSAL_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(REFUSAL_DIR, f"refusal-{stamp}.json")
    payload = {
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": source,
        "category": assessment.get("category"),
        "reason": assessment.get("reason"),
        "matched": assessment.get("matched"),
        "note": "VassalOps refused and initiated shutdown per ACCEPTABLE_USE.md",
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def _show_warning(title: str, body: str) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, body, title, 0x10)  # MB_ICONERROR
    except Exception:
        print(f"[VassalOps Guard] {title}: {body}")


def schedule_shutdown(delay_sec: float = 0.8) -> None:
    """Hard-exit after UI has a moment to show the refusal message."""

    def _exit() -> None:
        try:
            # Best-effort: destroy pywebview windows if present
            import webview

            for w in list(getattr(webview, "windows", []) or []):
                try:
                    w.destroy()
                except Exception:
                    pass
        except Exception:
            pass
        os._exit(1)

    threading.Timer(delay_sec, _exit).start()


def enforce_intent_or_shutdown(text: str, *, source: str = "chat") -> Optional[str]:
    """
    If text is forbidden: log, warn, schedule shutdown, return user-facing message.
    If allowed: return None.
    """
    assessment = assess_intent(text)
    if assessment.get("allowed", True):
        return None

    path = write_refusal_log(assessment, source=source)
    category = assessment.get("category") or "policy"
    reason = assessment.get("reason") or "This request violates VassalOps acceptable use."
    body = (
        "VassalOps will not assist with this request.\n\n"
        f"{reason}\n\n"
        "Category: {0}\n"
        "See ACCEPTABLE_USE.md in the VassalOps folder.\n\n"
        "This session will close after you dismiss this warning.\n"
        f"(Refusal logged: {path})"
    ).format(category)

    _show_warning("VassalOps — Use blocked", body)
    schedule_shutdown(0.9)
    return (
        "BLOCKED: " + reason + " VassalOps is shutting down. "
        "See ACCEPTABLE_USE.md. Refusal log: " + path
    )


def guard_prompt_block() -> str:
    """Short block for agent system prompts."""
    return (
        "POLICY: Refuse terrorism, mass violence, CSAM/child sexual exploitation, "
        "non-consensual sexual targeting, fraud/credential theft, and critical-infrastructure "
        "sabotage. If the user asks for those, stop and do not use desktop tools."
    )
