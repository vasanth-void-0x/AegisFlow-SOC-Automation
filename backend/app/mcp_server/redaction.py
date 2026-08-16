"""Redacts anything that looks like a secret before it's logged or audited."""
import re

_SECRET_KEY_PATTERNS = re.compile(
    r"(api[_-]?key|token|password|secret|authorization|x-apikey)", re.IGNORECASE
)
_LOOKS_LIKE_SECRET_VALUE = re.compile(r"^(sk-|gsk_|ghp_|Bearer\s)", re.IGNORECASE)

REDACTED = "***REDACTED***"


def redact_dict(data: dict) -> dict:
    """Recursively redact values whose key looks sensitive, or whose value
    matches a known secret-token shape (API keys, bearer tokens, etc.)."""
    out = {}
    for key, value in data.items():
        if _SECRET_KEY_PATTERNS.search(str(key)):
            out[key] = REDACTED
        elif isinstance(value, dict):
            out[key] = redact_dict(value)
        elif isinstance(value, str) and _LOOKS_LIKE_SECRET_VALUE.match(value):
            out[key] = REDACTED
        else:
            out[key] = value
    return out


def redact_text(text: str) -> str:
    """Best-effort redaction of secret-shaped substrings inside free text (e.g. error messages)."""
    text = re.sub(r"sk-[A-Za-z0-9]{10,}", REDACTED, text)
    text = re.sub(r"gsk_[A-Za-z0-9]{10,}", REDACTED, text)
    text = re.sub(r"Bearer\s+[A-Za-z0-9._-]{10,}", f"Bearer {REDACTED}", text)
    return text
