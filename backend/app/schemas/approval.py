"""Phase 7 schemas: approval requests/responses and timeline events."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApprovalDecisionRequest(BaseModel):
    approver: str = Field(..., min_length=1, max_length=256, description="Analyst identity")
    reason: str = Field(..., min_length=1, max_length=2000, description="Approval or rejection reason")


class ProposalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    action_type: str
    target: str
    justification: str
    proposed_by: str
    status: str
    approver: str | None
    approval_reason: str | None
    decided_at: datetime | None
    execution_result: dict | None
    expires_at: datetime | None
    created_at: datetime


class TimelineEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    event_type: str
    description: str
    actor: str
    event_metadata: dict
    created_at: datetime
