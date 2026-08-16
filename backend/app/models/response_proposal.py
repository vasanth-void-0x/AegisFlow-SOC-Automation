"""
Response proposal model.

Created by MCP's create_response_proposal tool (Phase 5) or the AI triage
flow, then acted on by a human via the approval API (Phase 7). No action
tool exists that bypasses this approval gate - see Phase 7 for enforcement.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return f"RSP-{uuid.uuid4().hex[:12].upper()}"


class ActionType(str, enum.Enum):
    block_ip = "block_ip"
    isolate_host = "isolate_host"
    disable_account = "disable_account"
    rollback = "rollback"


class ProposalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"
    executed = "executed"
    rolled_back = "rolled_back"


class ResponseProposal(Base):
    __tablename__ = "response_proposals"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    incident_id: Mapped[str] = mapped_column(String(32), ForeignKey("incidents.id"), index=True, nullable=False)

    action_type: Mapped[ActionType] = mapped_column(Enum(ActionType), nullable=False)
    target: Mapped[str] = mapped_column(String(256), nullable=False)  # e.g. IP address or hostname
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_by: Mapped[str] = mapped_column(String(64), nullable=False, default="ai_triage")

    status: Mapped[ProposalStatus] = mapped_column(Enum(ProposalStatus), default=ProposalStatus.pending, nullable=False)

    approver: Mapped[str | None] = mapped_column(String(256), nullable=True)
    approval_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    execution_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
