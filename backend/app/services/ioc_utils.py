"""Indicator-of-compromise parsing and classification utilities."""
import ipaddress
import re

_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$"
)
_HASH_LENGTHS = {32: "md5", 40: "sha1", 64: "sha256"}


def classify_ip(value: str) -> dict:
    """Return IP version and public/private classification, or raise ValueError."""
    ip = ipaddress.ip_address(value)
    return {
        "version": ip.version,
        "is_private": ip.is_private,
        "is_public": not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved),
    }


def is_domain(value: str) -> bool:
    return bool(_DOMAIN_RE.match(value)) and not is_ip(value)


def is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_url(value: str) -> bool:
    return value.lower().startswith(("http://", "https://"))


def detect_hash_algo(value: str) -> str | None:
    if re.fullmatch(r"[a-fA-F0-9]+", value or ""):
        return _HASH_LENGTHS.get(len(value))
    return None


def normalize_indicator_type(indicator_type: str, value: str) -> str:
    """Validate that the declared type matches the value's actual shape."""
    t = indicator_type.lower()
    if t == "ip" and not is_ip(value):
        raise ValueError(f"'{value}' is not a valid IP address")
    if t == "domain" and not is_domain(value):
        raise ValueError(f"'{value}' is not a valid domain")
    if t == "url" and not is_url(value):
        raise ValueError(f"'{value}' is not a valid URL")
    if t == "hash" and detect_hash_algo(value) is None:
        raise ValueError(f"'{value}' is not a recognized hash (md5/sha1/sha256)")
    return t
