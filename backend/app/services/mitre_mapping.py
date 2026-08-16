"""
Lightweight local MITRE ATT&CK technique reference.

This is a small curated subset (not the full ATT&CK STIX bundle, which is
too heavy for an 8GB dev laptop) covering techniques relevant to the SOC
alert types this project ships runbooks for. Keyed by simple keyword match
against alert_name/description - good enough for a portfolio-scale mapping,
clearly not a substitute for a full CTI platform.
"""
from app.schemas.enrichment import MitreTechnique

_KEYWORD_MAP: list[tuple[list[str], MitreTechnique]] = [
    (
        ["brute force", "brute-force", "failed login", "failed ssh"],
        MitreTechnique(technique_id="T1110", name="Brute Force", tactic="Credential Access"),
    ),
    (
        ["powershell", "encoded command", "-enc"],
        MitreTechnique(technique_id="T1059.001", name="PowerShell", tactic="Execution"),
    ),
    (
        ["malware", "trojan", "ransomware", "malicious hash"],
        MitreTechnique(technique_id="T1204", name="User Execution", tactic="Execution"),
    ),
    (
        ["phishing", "suspicious link", "phishing email"],
        MitreTechnique(technique_id="T1566", name="Phishing", tactic="Initial Access"),
    ),
    (
        ["impossible travel", "geo-anomaly", "anomalous login location"],
        MitreTechnique(technique_id="T1078", name="Valid Accounts", tactic="Defense Evasion"),
    ),
    (
        ["outbound connection", "c2", "command and control", "beacon"],
        MitreTechnique(technique_id="T1071", name="Application Layer Protocol", tactic="Command and Control"),
    ),
]


def map_alert_to_techniques(alert_name: str, description: str = "") -> list[MitreTechnique]:
    text = f"{alert_name} {description}".lower()
    matches = []
    for keywords, technique in _KEYWORD_MAP:
        if any(kw in text for kw in keywords):
            matches.append(technique)
    return matches


def get_technique_by_id(technique_id: str) -> MitreTechnique | None:
    for _, technique in _KEYWORD_MAP:
        if technique.technique_id == technique_id:
            return technique
    return None
