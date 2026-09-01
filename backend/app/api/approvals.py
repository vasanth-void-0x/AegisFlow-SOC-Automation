"""Phase 7 API: human approval and response actions."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_analyst, require_viewer
from app.core.config import get_settings
from app.database.session import get_db
from app.models.response_proposal import ActionType, ResponseProposal
from app.schemas.approval import ApprovalDecisionRequest, ProposalOut, TimelineEventOut
from app.services import approval_service
from app.services.incident_service import get_incident
from app.services.timeline_service import add_event, get_timeline

router = APIRouter(tags=["approvals"], dependencies=[Depends(require_viewer)])


class CreateProposalRequest(BaseModel):
    action_type: str = Field(..., description="block_ip|isolate_host|disable_account|rollback")
    target: str = Field(..., min_length=1, max_length=256)
    justification: str = Field(..., min_length=10, max_length=2000)
    proposed_by: str = Field(default="analyst")


@router.post(
    "/incidents/{incident_id}/proposals",
    response_model=ProposalOut,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"description": "Incident not found"}, 422: {"description": "Invalid action_type"}},
    dependencies=[Depends(require_analyst)],
)
def create_proposal(incident_id: str, body: CreateProposalRequest, db: Session = Depends(get_db)) -> ProposalOut:
    """Create a response proposal via HTTP (same semantics as the MCP create_response_proposal tool)."""
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")

    if body.action_type not in {a.value for a in ActionType}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid action_type. Must be one of {[a.value for a in ActionType]}",
        )

    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.approval_expiry_minutes)

    proposal = ResponseProposal(
        incident_id=incident_id,
        action_type=ActionType(body.action_type),
        target=body.target,
        justification=body.justification,
        proposed_by=body.proposed_by,
        expires_at=expires_at,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    add_event(
        db,
        incident_id,
        event_type="response_proposal_created",
        description=f"Response proposal created: {proposal.action_type.value} on {proposal.target}",
        actor=body.proposed_by,
        metadata={"proposal_id": proposal.id},
    )
    return ProposalOut.model_validate(proposal)


@router.get("/approvals", response_model=list[ProposalOut])
def list_approvals(
    status_filter: str | None = Query(default=None, alias="status"),
    incident_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ProposalOut]:
    proposals = approval_service.list_proposals(db, status=status_filter, incident_id=incident_id)
    return [ProposalOut.model_validate(p) for p in proposals]


@router.get("/approvals/{proposal_id}", response_model=ProposalOut)
def get_approval(proposal_id: str, db: Session = Depends(get_db)) -> ProposalOut:
    try:
        proposal = approval_service.get_proposal(db, proposal_id)
    except approval_service.ProposalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProposalOut.model_validate(proposal)


@router.post("/approvals/{proposal_id}/approve", response_model=ProposalOut)
def approve_proposal(proposal_id: str, body: ApprovalDecisionRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_analyst)) -> ProposalOut:
    try:
        proposal = approval_service.approve_proposal(db, proposal_id, approver=principal.username, reason=body.reason)
    except approval_service.ProposalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except approval_service.InvalidProposalStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ProposalOut.model_validate(proposal)


@router.post("/approvals/{proposal_id}/reject", response_model=ProposalOut)
def reject_proposal(proposal_id: str, body: ApprovalDecisionRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_analyst)) -> ProposalOut:
    try:
        proposal = approval_service.reject_proposal(db, proposal_id, approver=principal.username, reason=body.reason)
    except approval_service.ProposalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except approval_service.InvalidProposalStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ProposalOut.model_validate(proposal)


@router.post("/approvals/{proposal_id}/rollback", response_model=ProposalOut)
def rollback_proposal(proposal_id: str, body: ApprovalDecisionRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_analyst)) -> ProposalOut:
    try:
        proposal = approval_service.rollback_proposal(db, proposal_id, approver=principal.username, reason=body.reason)
    except approval_service.ProposalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except approval_service.InvalidProposalStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ProposalOut.model_validate(proposal)


@router.get("/incidents/{incident_id}/timeline", response_model=list[TimelineEventOut])
def get_incident_timeline(incident_id: str, db: Session = Depends(get_db)) -> list[TimelineEventOut]:
    events = get_timeline(db, incident_id)
    return [TimelineEventOut.model_validate(e) for e in events]
