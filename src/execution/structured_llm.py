"""Instructor-style structured JSON: Pydantic schema, one validation retry.

Calls stay local (Ollama). This is not the Instructor SaaS SDK.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

from src.execution.action_firewall import ALLOWED_ACTION_TYPES

T = TypeVar("T", bound=BaseModel)


class PlannerStep(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    payload: str = ""

    @field_validator("type")
    @classmethod
    def type_allowlisted(cls, value: str) -> str:
        action = str(value or "").strip()
        if action not in ALLOWED_ACTION_TYPES:
            raise ValueError(f"Action type '{action}' is not on the allowlist.")
        return action

    @field_validator("payload", mode="before")
    @classmethod
    def payload_as_str(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return json.dumps(value)


class PlannerPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    steps: List[PlannerStep]


class LoopDecisionModel(BaseModel):
    """Normalized agent-loop decision: tool_call or final."""

    model_config = ConfigDict(extra="ignore")

    kind: str
    name: str = ""
    payload: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise ValueError("Model output was not an object.")
        if data.get("kind") in ("tool_call", "final"):
            payload = data.get("payload")
            if payload is None:
                payload = ""
            if not isinstance(payload, str):
                payload = json.dumps(payload)
            name = str(data.get("name") or "").strip()
            kind = data["kind"]
            if kind == "tool_call" and not name:
                raise ValueError("tool_call missing name.")
            return {"kind": kind, "name": name, "payload": payload}

        action = str(data.get("action") or data.get("type") or "").strip().lower()
        name = str(data.get("name") or data.get("tool") or "").strip()
        payload = data.get("payload")
        if payload is None:
            payload = data.get("text") or data.get("message") or ""
        payload_s = payload if isinstance(payload, str) else json.dumps(payload)

        if action in ("final", "done", "speak_log") and not name:
            return {"kind": "final", "name": "", "payload": payload_s}
        if action in ("final", "done") or name == "final":
            return {"kind": "final", "name": "", "payload": payload_s}
        if action in ("tool_call", "tool", "call") or name:
            if not name:
                raise ValueError("tool_call missing name.")
            return {"kind": "tool_call", "name": name, "payload": payload_s}
        raise ValueError("JSON missing action tool_call or final.")

    @field_validator("kind")
    @classmethod
    def kind_allowed(cls, value: str) -> str:
        if value not in ("tool_call", "final"):
            raise ValueError("kind must be tool_call or final.")
        return value


@dataclass
class StructuredResult:
    ok: bool
    data: Optional[BaseModel] = None
    error: str = ""
    attempts: int = 0
    raw: Any = None


def coerce_json(raw: Any) -> Any:
    """Parse a model reply into a JSON value (dict/list/scalar)."""
    if isinstance(raw, (dict, list)):
        return raw
    if raw is None:
        raise ValueError("Empty model output.")
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            raise ValueError("Empty model output.")
        return json.loads(text)
    return raw


def complete_structured(
    prompt: str,
    schema: Type[T],
    call_model: Callable[[str], Any],
    *,
    max_retries: int = 1,
) -> StructuredResult:
    """Call the model, validate against schema, retry once with the validation error."""
    current = prompt
    last_error = ""
    last_raw: Any = None
    attempts = 0
    for attempt in range(max_retries + 1):
        attempts = attempt + 1
        try:
            last_raw = call_model(current)
        except Exception as exc:
            last_error = str(exc)
            if attempt >= max_retries:
                return StructuredResult(
                    ok=False,
                    error=f"Model call failed: {exc}",
                    attempts=attempts,
                    raw=last_raw,
                )
            current = _with_validation_error(prompt, last_error)
            continue
        try:
            parsed = coerce_json(last_raw)
            data = schema.model_validate(parsed)
            return StructuredResult(ok=True, data=data, attempts=attempts, raw=last_raw)
        except (ValidationError, ValueError, json.JSONDecodeError, TypeError) as exc:
            last_error = str(exc)
            if attempt >= max_retries:
                return StructuredResult(
                    ok=False,
                    error=last_error,
                    attempts=attempts,
                    raw=last_raw,
                )
            current = _with_validation_error(prompt, last_error)
    return StructuredResult(ok=False, error=last_error, attempts=attempts, raw=last_raw)


def call_ollama_json(
    prompt: str,
    *,
    host: str,
    port: int,
    model_name: str,
    timeout: int = 60,
    post: Optional[Callable[..., Any]] = None,
) -> Any:
    """POST /api/generate with format=json. Returns parsed JSON or the raw string."""
    import requests

    http_post = post or requests.post
    url = f"http://{host}:{port}/api/generate"
    body = {"model": model_name, "prompt": prompt, "stream": False, "format": "json"}
    response = http_post(url, json=body, timeout=timeout).json()
    raw = (response.get("response") or "{}").strip()
    try:
        return json.loads(raw)
    except Exception:
        return raw


def plan_to_dict(plan: PlannerPlan) -> Dict[str, Any]:
    return plan.model_dump()


def _with_validation_error(prompt: str, error: str) -> str:
    return (
        f"{prompt}\n\n"
        "VALIDATION ERROR (fix and return JSON only):\n"
        f"{error}"
    )
