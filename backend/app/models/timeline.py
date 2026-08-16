"""
Immutable incident timeline. Every meaningful event in an incident's
lifecycle (created, enriched, triaged, proposal created/approved/rejected/
executed/rolled back) gets an append-only entry here. Rows are never
updated or deleted - only inserted - so this table doubles as the audit log.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return f"EVT-{uuid.uuid4().hex[:12].upper()}"


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    incident_id: Mapped[str] = mapped_column(String(32), ForeignKey("incidents.id"), index=True, nullable=False)

    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    event_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)
