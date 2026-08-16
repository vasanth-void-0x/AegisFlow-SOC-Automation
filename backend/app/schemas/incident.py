"""Pydantic v2 request/response schemas for Phase 1 (alert ingestion)."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.incident import IncidentStatus, Severity


class Indicator(BaseModel):
    """A single indicator of compromise supplied with an alert."""

    type: str = Field(..., description="ip | domain | url | hash")
    value: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"ip", "domain", "url", "hash"}
        if v.lower() not in allowed:
            raise ValueError(f"indicator type must be one of {allowed}")
        return v.lower()


class AlertIngest(BaseModel):
    """Incoming alert payload - this is what SIEM/EDR/webhook sources POST."""

    model_config = ConfigDict(str_strip_whitespace=True)

    source: str = Field(..., min_length=1, max_length=128, examples=["wazuh"])
    alert_name: str = Field(..., min_length=1, max_length=256, examples=["SSH Brute Force Detected"])
    severity: Severity
    description: str = Field(default="", max_length=5000)

    source_ip: str | None = Field(default=None, max_length=64)
    destination_ip: str | None = Field(default=None, max_length=64)
    hostname: str | None = Field(default=None, max_length=256)
    username: str | None = Field(default=None, max_length=256)

    event_time: datetime
    raw_event: dict[str, Any] = Field(default_factory=dict)
    indicators: list[Indicator] = Field(default_factory=list)

    # Optional client-supplied idempotency key. If omitted, a fingerprint is
    # derived server-side from the alert's identifying fields.
    idempotency_key: str | None = Field(default=None, max_length=128)


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fingerprint: str
    source: str
    alert_name: str
    severity: Severity
    description: str
    source_ip: str | None
    destination_ip: str | None
    hostname: str | None
    username: str | None
    event_time: datetime
    raw_event: dict[str, Any]
    indicators: list[dict[str, Any]]
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime


class IncidentListOut(BaseModel):
    items: list[IncidentOut]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
