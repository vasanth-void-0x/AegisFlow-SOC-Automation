"""Normalize heterogeneous direct logs into BlueOrch's canonical alert schema."""
import re
from datetime import datetime, timezone

from app.models.incident import Severity
from app.schemas.direct_log import DirectLogIn
from app.schemas.incident import AlertIngest, Indicator

IP_PATTERN = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
CRITICAL_TERMS = ("ransomware", "data exfiltration", "domain admin", "malware executed")
HIGH_TERMS = ("brute force", "credential theft", "mimikatz", "powershell encoded", "reverse shell", "blocked attack")
MEDIUM_TERMS = ("failed login", "authentication failure", "access denied", "suspicious", "warning")


def infer_severity(message: str) -> Severity:
    text = message.lower()
    if any(term in text for term in CRITICAL_TERMS):
        return Severity.critical
    if any(term in text for term in HIGH_TERMS):
        return Severity.high
    if any(term in text for term in MEDIUM_TERMS):
        return Severity.medium
    return Severity.low


def _valid_ipv4(value: str) -> bool:
    try:
        parts = value.split(".")
        return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def normalize_direct_log(log: DirectLogIn) -> AlertIngest:
    ips = [value for value in IP_PATTERN.findall(log.message) if _valid_ipv4(value)]
    source_ip = log.source_ip or (ips[0] if ips else None)
    destination_ip = log.destination_ip or (ips[1] if len(ips) > 1 else None)
    severity = log.severity or infer_severity(log.message)
    title = str(log.fields.get("alert_name") or log.fields.get("event_name") or "Direct log security event")[:256]
    indicators = [Indicator(type="ip", value=value) for value in dict.fromkeys(ips[:10])]
    return AlertIngest(
        source=f"direct:{log.source_type}:{log.source_name}"[:128],
        alert_name=title,
        severity=severity,
        description=log.message,
        source_ip=source_ip,
        destination_ip=destination_ip,
        hostname=log.hostname or log.fields.get("hostname") or log.fields.get("host"),
        username=log.username or log.fields.get("username") or log.fields.get("user"),
        event_time=log.timestamp or datetime.now(timezone.utc),
        raw_event={"message": log.message, "source_type": log.source_type, **log.fields},
        indicators=indicators,
        idempotency_key=log.event_id or str(log.fields.get("event_id") or "") or None,
    )
