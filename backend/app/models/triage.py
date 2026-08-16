"""TriageRecord ORM model - persists every AI triage call for audit/eval purposes."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return f"TRG-{uuid.uuid4().hex[:12].upper()}"


class TriageRecord(Base):
    __tablename__ = "triage_records"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    incident_id: Mapped[str] = mapped_column(String(32), ForeignKey("incidents.id"), index=True, nullable=False)

    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)

    # Validated structured result, stored as JSON (None if triage failed entirely)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    token_usage_prompt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_usage_completion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
