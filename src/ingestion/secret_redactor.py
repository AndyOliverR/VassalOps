"""Redact common secret patterns from text before sending to a model prompt."""

import re


_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_SK_RE = re.compile(r"\bsk-[A-Za-z0-9_\-]{10,}\b")
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]+=*\b", re.IGNORECASE)
_LONG_DIGIT_RE = re.compile(r"\b\d{12,}\b")
_KV_SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|secret|api[_-]?key|token|authorization)\s*[=:]\s*([^\s,;]+)"
)


def redact_secrets(text: str) -> str:
    """Return a copy of text with emails, tokens, and long digit runs masked."""
    if not text:
        return text

    redacted = str(text)
    redacted = _SK_RE.sub("[REDACTED_API_KEY]", redacted)
    redacted = _BEARER_RE.sub("Bearer [REDACTED_TOKEN]", redacted)
    redacted = _KV_SECRET_RE.sub(r"\1=[REDACTED]", redacted)
    redacted = _EMAIL_RE.sub("[REDACTED_EMAIL]", redacted)
    redacted = _LONG_DIGIT_RE.sub("[REDACTED_DIGITS]", redacted)
    return redacted


if __name__ == "__main__":
    sample = "user@example.com sk-abc1234567890 Bearer xyz password=hunter2 4111111111111111"
    print(redact_secrets(sample))
