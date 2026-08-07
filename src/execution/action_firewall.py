"""Allowlist firewall for desktop automation action steps."""

from typing import Any, Dict, Set


ALLOWED_ACTION_TYPES: Set[str] = {
    "run_backup",
    "sort_intel",
    "extract_intel",
    "run_saved_macro",
    "learn_macro",
    "click_element",
    "type_text",
    "press_key",
    "press_hotkey",
    "speak_log",
}


class VassalOpsActionFirewall:
    """Rejects unknown action types and lightly validates payloads before execution."""

    def __init__(self, allowed_types: Set[str] = None):
        self.allowed_types = allowed_types or set(ALLOWED_ACTION_TYPES)

    def verify_step(self, step: Dict[str, Any]) -> dict:
        if not isinstance(step, dict):
            return {"status": "REJECTED", "reason": "Action step must be an object."}

        action_type = step.get("type")
        if not action_type or not isinstance(action_type, str):
            return {"status": "REJECTED", "reason": "Action step missing string 'type'."}

        action_type = action_type.strip()
        if action_type not in self.allowed_types:
            return {
                "status": "REJECTED",
                "reason": f"Action type '{action_type}' is not on the allowlist.",
            }

        payload = step.get("payload", "")
        if action_type in ("type_text", "press_key", "press_hotkey", "click_element", "speak_log", "learn_macro", "run_saved_macro"):
            if payload is None or (isinstance(payload, str) and not payload.strip() and action_type != "speak_log"):
                return {"status": "REJECTED", "reason": f"Action '{action_type}' requires a non-empty payload."}

        if action_type == "press_key":
            key = str(payload).strip()
            if " " in key or len(key) > 32:
                return {"status": "REJECTED", "reason": "press_key payload must be a single key token."}

        if action_type == "click_element":
            target = str(payload)
            if "." not in target:
                return {"status": "REJECTED", "reason": "click_element payload must be 'app.element'."}

        if action_type == "press_hotkey":
            keys = str(payload).replace("+", " ").split()
            if not keys or any(len(k) > 32 for k in keys):
                return {"status": "REJECTED", "reason": "press_hotkey payload is invalid."}

        return {"status": "VERIFIED", "reason": "Action matches allowlist rules."}


if __name__ == "__main__":
    fw = VassalOpsActionFirewall()
    print(fw.verify_step({"type": "type_text", "payload": "hello"}))
    print(fw.verify_step({"type": "shell_exec", "payload": "rm -rf /"}))
