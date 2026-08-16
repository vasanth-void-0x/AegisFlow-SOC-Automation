"""Incident ORM model - the core record created from an ingested alert."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return f"INC-{uuid.uuid4().hex[:12].upper()}"


class Severity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IncidentStatus(str, enum.Enum):
    new = "new"
    triaging = "triaging"
    pending_approval = "pending_approval"
    contained = "contained"
    resolved = "resolved"
    closed = "closed"


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_incident_fingerprint"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)

    # Idempotency / dedup key - hash of source+alert_name+src_ip+dst_ip+host+user+event_time
    fingerprint: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    source: Mapped[str] = mapped_column(String(128), nullable=False)
    alert_name: Mapped[str] = mapped_column(String(256), nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(256), nullable=True)
    username: Mapped[str | None] = mapped_column(String(256), nullable=True)

    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    raw_event: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    indicators: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), nullable=False, default=IncidentStatus.new, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
