"""Schemas for Phase 2 threat-intelligence enrichment."""
import enum
from typing import Any

from pydantic import BaseModel, Field


class ResultSource(str, enum.Enum):
    live = "live"          # fetched from a real external provider just now
    cached = "cached"       # served from local cache (previously fetched live)
    demo = "demo"          # provider unavailable/no key - deterministic mock data


class MitreTechnique(BaseModel):
    technique_id: str
    name: str
    tactic: str


class GeoInfo(BaseModel):
    country: str | None = None
    city: str | None = None
    asn: str | None = None
    org: str | None = None


class VirusTotalSummary(BaseModel):
    malicious: int = 0
    suspicious: int = 0
    harmless: int = 0
    undetected: int = 0
    total_engines: int = 0
    reputation: int | None = None


class EnrichmentResult(BaseModel):
    indicator_type: str
    value: str
    is_public: bool | None = None
    source: ResultSource
    provider: str
    virustotal: VirusTotalSummary | None = None
    geo: GeoInfo | None = None
    mitre_techniques: list[MitreTechnique] = Field(default_factory=list)
    error: str | None = None
    raw: dict[str, Any] | None = None
