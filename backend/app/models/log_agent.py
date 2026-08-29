"""Registered endpoint collector and its operational state."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class LogAgent(Base):
    __tablename__ = "log_agents"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: f"AGT-{uuid.uuid4().hex[:12].upper()}")
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    platform: Mapped[str] = mapped_column(String(32), default="windows")
    profile: Mapped[str] = mapped_column(String(32), default="security")
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hostname: Mapped[str | None] = mapped_column(String(256), nullable=True)
    agent_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    events_received: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

