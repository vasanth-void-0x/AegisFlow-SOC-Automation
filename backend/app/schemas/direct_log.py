"""Schemas for SIEM-less endpoint, webhook, and syslog-style ingestion."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.incident import Severity
from app.schemas.incident import IncidentOut


class DirectLogIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    message: str = Field(..., min_length=1, max_length=20_000)
    source_type: str = Field(default="agent", pattern="^(agent|webhook|syslog|file)$")
    source_name: str = Field(default="direct-log", min_length=1, max_length=128)
    timestamp: datetime | None = None
    severity: Severity | None = None
    hostname: str | None = Field(default=None, max_length=256)
    username: str | None = Field(default=None, max_length=256)
    source_ip: str | None = Field(default=None, max_length=64)
    destination_ip: str | None = Field(default=None, max_length=64)
    event_id: str | None = Field(default=None, max_length=128)
    fields: dict[str, Any] = Field(default_factory=dict)


class DirectLogBatchIn(BaseModel):
    logs: list[DirectLogIn] = Field(..., min_length=1, max_length=500)


class DirectLogBatchOut(BaseModel):
    accepted: int
    duplicates: int
    filtered: int = 0
    incidents: list[IncidentOut]


class AgentRegisterIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., min_length=3, max_length=128)
    platform: str = Field(default="windows", pattern="^(windows|linux)$")
    profile: str = Field(default="security", pattern="^(security|system|full)$")


class AgentRegisteredOut(BaseModel):
    id: str
    name: str
    platform: str
    profile: str
    api_key: str
    ingest_path: str = "/api/v1/agents/logs/bulk"
    heartbeat_path: str = "/api/v1/agents/heartbeat"


class AgentHeartbeatIn(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=256)
    agent_version: str = Field(default="1.0.0", max_length=32)


class AgentStatusOut(BaseModel):
    id: str
    name: str
    platform: str
    profile: str
    hostname: str | None
    agent_version: str | None
    status: str
    last_seen_at: datetime | None
    events_received: int
    created_at: datetime
