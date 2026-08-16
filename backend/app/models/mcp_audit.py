"""Audit log for every MCP tool invocation - append-only, for compliance/traceability."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return f"MCP-{uuid.uuid4().hex[:12].upper()}"


class McpToolCallLog(Base):
    __tablename__ = "mcp_tool_call_log"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    tool_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)

    # Arguments/result are stored with secrets redacted (see redaction.py) -
    # this table must never contain API keys, tokens, or passwords.
    arguments: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
