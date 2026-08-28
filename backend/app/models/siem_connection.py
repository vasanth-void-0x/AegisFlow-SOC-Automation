import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base

def _utcnow(): return datetime.now(timezone.utc)

class SiemProvider(str, enum.Enum):
    splunk = "splunk"
    wazuh = "wazuh"

class SiemConnection(Base):
    __tablename__ = "siem_connections"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: f"SIEM-{uuid.uuid4().hex[:12].upper()}")
    provider: Mapped[SiemProvider] = mapped_column(Enum(SiemProvider), unique=True, nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=False)
    index_name: Mapped[str | None] = mapped_column(String(256))
    verify_ssl: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)
