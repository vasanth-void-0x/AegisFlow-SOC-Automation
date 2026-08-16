"""
Phase 7: Human approval and response enforcement.

The one rule this entire module exists to enforce:

    AI recommends -> Human reviews -> Human approves -> System executes

No function in this module (or anywhere else in the codebase) executes a
response action without first checking status == approved. Expired or
rejected proposals can never be executed.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.response_proposal import ProposalStatus, ResponseProposal
from app.services import response_adapters
from app.services.timeline_service import add_event

logger = get_logger(__name__)


class ProposalNotFoundError(Exception):
    pass


class InvalidProposalStateError(Exception):
    """Raised when an action is attempted on a proposal in the wrong state
    (e.g. approving an already-executed proposal, executing a rejected one)."""


def _expire_if_needed(db: Session, proposal: ResponseProposal) -> ResponseProposal:
    expires_at = proposal.expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        # SQLite drops tzinfo on round-trip even for TIMESTAMP(timezone=True) columns.
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if proposal.status == ProposalStatus.pending and expires_at is not None and expires_at < datetime.now(timezone.utc):
        proposal.status = ProposalStatus.expired
        db.commit()
        db.refresh(proposal)
        add_event(
            db,
            proposal.incident_id,
            event_type="response_proposal_expired",
            description=f"Response proposal {proposal.id} expired without a decision",
            actor="system",
            metadata={"proposal_id": proposal.id},
        )
    return proposal


def get_proposal(db: Session, proposal_id: str) -> ResponseProposal:
    proposal = db.execute(
        select(ResponseProposal).where(ResponseProposal.id == proposal_id)
    ).scalar_one_or_none()
    if proposal is None:
        raise ProposalNotFoundError(f"Proposal {proposal_id} not found")
    return _expire_if_needed(db, proposal)


def list_proposals(db: Session, status: str | None = None, incident_id: str | None = None) -> list[ResponseProposal]:
    query = select(ResponseProposal)
    if status:
        query = query.where(ResponseProposal.status == status)
    if incident_id:
        query = query.where(ResponseProposal.incident_id == incident_id)
    query = query.order_by(ResponseProposal.created_at.desc())

    proposals = list(db.execute(query).scalars().all())
    return [_expire_if_needed(db, p) for p in proposals]


def approve_proposal(db: Session, proposal_id: str, approver: str, reason: str) -> ResponseProposal:
    """
    Approve a proposal AND execute the (simulated, by default) action.
    This is the only path in the codebase that calls response_adapters.execute_action.
    """
    proposal = get_proposal(db, proposal_id)

    if proposal.status != ProposalStatus.pending:
        raise InvalidProposalStateError(
            f"Cannot approve proposal {proposal_id} in state '{proposal.status.value}' (must be 'pending')"
        )

    proposal.status = ProposalStatus.approved
    proposal.approver = approver
    proposal.approval_reason = reason
    proposal.decided_at = datetime.now(timezone.utc)
    db.commit()

    add_event(
        db,
        proposal.incident_id,
        event_type="response_proposal_approved",
        description=f"Proposal {proposal.id} ({proposal.action_type.value} on {proposal.target}) approved by {approver}: {reason}",
        actor=approver,
        metadata={"proposal_id": proposal.id},
    )

    # Execute immediately upon approval (demo/simulated by default - see response_adapters.py)
    execution_result = response_adapters.execute_action(proposal.action_type, proposal.target)
    proposal.status = ProposalStatus.executed
    proposal.execution_result = execution_result
    db.commit()
    db.refresh(proposal)

    add_event(
        db,
        proposal.incident_id,
        event_type="response_proposal_executed",
        description=f"Proposal {proposal.id} executed: {execution_result.get('message')}",
        actor="system",
        metadata={"proposal_id": proposal.id, "execution_result": execution_result},
    )

    logger.info("Proposal %s approved by %s and executed", proposal.id, approver)
    return proposal


def reject_proposal(db: Session, proposal_id: str, approver: str, reason: str) -> ResponseProposal:
    proposal = get_proposal(db, proposal_id)

    if proposal.status != ProposalStatus.pending:
        raise InvalidProposalStateError(
            f"Cannot reject proposal {proposal_id} in state '{proposal.status.value}' (must be 'pending')"
        )

    proposal.status = ProposalStatus.rejected
    proposal.approver = approver
    proposal.approval_reason = reason
    proposal.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(proposal)

    add_event(
        db,
        proposal.incident_id,
        event_type="response_proposal_rejected",
        description=f"Proposal {proposal.id} ({proposal.action_type.value} on {proposal.target}) rejected by {approver}: {reason}",
        actor=approver,
        metadata={"proposal_id": proposal.id},
    )

    logger.info("Proposal %s rejected by %s", proposal.id, approver)
    return proposal


def rollback_proposal(db: Session, proposal_id: str, approver: str, reason: str) -> ResponseProposal:
    proposal = get_proposal(db, proposal_id)

    if proposal.status != ProposalStatus.executed:
        raise InvalidProposalStateError(
            f"Cannot roll back proposal {proposal_id} in state '{proposal.status.value}' (must be 'executed')"
        )

    rollback_result = response_adapters.execute_rollback(proposal.action_type, proposal.target, proposal.execution_result)
    proposal.status = ProposalStatus.rolled_back
    proposal.execution_result = {**(proposal.execution_result or {}), "rollback": rollback_result}
    db.commit()
    db.refresh(proposal)

    add_event(
        db,
        proposal.incident_id,
        event_type="response_proposal_rolled_back",
        description=f"Proposal {proposal.id} rolled back by {approver}: {reason}",
        actor=approver,
        metadata={"proposal_id": proposal.id, "rollback_result": rollback_result},
    )

    logger.info("Proposal %s rolled back by %s", proposal.id, approver)
    return proposal
