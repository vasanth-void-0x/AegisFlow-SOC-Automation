"""Tests for Phase 7: human approval and response enforcement."""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.response_proposal import ProposalStatus
from app.services import approval_service, response_adapters
from app.services.incident_service import create_incident_from_alert
from app.schemas.incident import AlertIngest

ALERT = dict(
    source="wazuh",
    alert_name="SSH Brute Force Detected",
    severity="high",
    description="test",
    source_ip="203.0.113.7",
    event_time="2026-08-12T06:00:00Z",
)


def _create_incident(db):
    return create_incident_from_alert(db, AlertIngest(**ALERT))


def _create_pending_proposal(db, incident_id, **overrides):
    from app.models.response_proposal import ActionType, ResponseProposal

    defaults = dict(
        incident_id=incident_id,
        action_type=ActionType.block_ip,
        target="203.0.113.7",
        justification="Repeated brute force attempts observed",
        proposed_by="ai_triage",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    defaults.update(overrides)
    proposal = ResponseProposal(**defaults)
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


# ---- Core enforcement: no execution without approval ----

def test_no_action_executes_on_creation(db_session):
    incident = _create_incident(db_session)
    proposal = _create_pending_proposal(db_session, incident.id)
    assert proposal.status == ProposalStatus.pending
    assert proposal.execution_result is None


def test_approve_executes_demo_action(db_session):
    incident = _create_incident(db_session)
    proposal = _create_pending_proposal(db_session, incident.id)

    result = approval_service.approve_proposal(db_session, proposal.id, approver="analyst_ravi", reason="Confirmed malicious")

    assert result.status == ProposalStatus.executed
    assert result.execution_result["simulated"] is True
    assert result.approver == "analyst_ravi"


def test_reject_never_executes(db_session):
    incident = _create_incident(db_session)
    proposal = _create_pending_proposal(db_session, incident.id)

    result = approval_service.reject_proposal(db_session, proposal.id, approver="analyst_ravi", reason="False positive")

    assert result.status == ProposalStatus.rejected
    assert result.execution_result is None


def test_cannot_approve_already_executed_proposal(db_session):
    incident = _create_incident(db_session)
    proposal = _create_pending_proposal(db_session, incident.id)
    approval_service.approve_proposal(db_session, proposal.id, approver="a1", reason="r1")

    with pytest.raises(approval_service.InvalidProposalStateError):
        approval_service.approve_proposal(db_session, proposal.id, approver="a2", reason="r2")


def test_cannot_approve_rejected_proposal(db_session):
    incident = _create_incident(db_session)
    proposal = _create_pending_proposal(db_session, incident.id)
    approval_service.reject_proposal(db_session, proposal.id, approver="a1", reason="r1")

    with pytest.raises(approval_service.InvalidProposalStateError):
        approval_service.approve_proposal(db_session, proposal.id, approver="a2", reason="r2")


def test_expired_proposal_cannot_be_approved(db_session):
    incident = _create_incident(db_session)
    proposal = _create_pending_proposal(
        db_session, incident.id, expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)
    )

    with pytest.raises(approval_service.InvalidProposalStateError):
        approval_service.approve_proposal(db_session, proposal.id, approver="a1", reason="too late")

    refreshed = approval_service.get_proposal(db_session, proposal.id)
    assert refreshed.status == ProposalStatus.expired


def test_rollback_only_allowed_after_execution(db_session):
    incident = _create_incident(db_session)
    proposal = _create_pending_proposal(db_session, incident.id)

    with pytest.raises(approval_service.InvalidProposalStateError):
        approval_service.rollback_proposal(db_session, proposal.id, approver="a1", reason="undo")


def test_rollback_after_execution_succeeds(db_session):
    incident = _create_incident(db_session)
    proposal = _create_pending_proposal(db_session, incident.id)
    approval_service.approve_proposal(db_session, proposal.id, approver="a1", reason="confirmed")

    result = approval_service.rollback_proposal(db_session, proposal.id, approver="a1", reason="was a mistake")
    assert result.status == ProposalStatus.rolled_back
    assert result.execution_result["rollback"]["simulated"] is True


def test_proposal_not_found_raises(db_session):
    with pytest.raises(approval_service.ProposalNotFoundError):
        approval_service.get_proposal(db_session, "RSP-NOPE")


# ---- Real adapter safety boundary ----

def test_real_adapter_refuses_even_when_enabled(monkeypatch):
    from app.core.config import Settings
    import app.services.response_adapters as adapters_module

    monkeypatch.setattr(adapters_module, "get_settings", lambda: Settings(enable_real_response_adapter=True))

    from app.models.response_proposal import ActionType

    with pytest.raises(response_adapters.RealAdapterDisabledError):
        response_adapters.execute_action(ActionType.block_ip, "1.2.3.4")


def test_demo_adapter_never_makes_real_calls():
    from app.models.response_proposal import ActionType

    result = response_adapters.execute_action(ActionType.isolate_host, "web-prod-01")
    assert result["simulated"] is True
    assert result["mode"] == "demo"


# ---- Timeline / audit trail ----

def test_timeline_records_full_incident_lifecycle(db_session):
    from app.services.timeline_service import get_timeline

    incident = _create_incident(db_session)
    proposal = _create_pending_proposal(db_session, incident.id)
    approval_service.approve_proposal(db_session, proposal.id, approver="a1", reason="confirmed")

    events = get_timeline(db_session, incident.id)
    event_types = [e.event_type for e in events]
    assert "incident_created" in event_types
    assert "response_proposal_approved" in event_types
    assert "response_proposal_executed" in event_types


def test_timeline_is_append_only_ordering(db_session):
    from app.services.timeline_service import get_timeline

    incident = _create_incident(db_session)
    proposal = _create_pending_proposal(db_session, incident.id)
    approval_service.reject_proposal(db_session, proposal.id, approver="a1", reason="fp")

    events = get_timeline(db_session, incident.id)
    timestamps = [e.created_at for e in events]
    assert timestamps == sorted(timestamps)


# ---- API level ----

def test_approval_api_full_flow(client):
    created = client.post("/api/v1/alerts", json=ALERT).json()
    incident_id = created["id"]

    proposal_resp = client.post(
        f"/api/v1/incidents/{incident_id}/proposals",
        json={"action_type": "block_ip", "target": "203.0.113.7", "justification": "Confirmed brute force pattern in logs"},
    )
    assert proposal_resp.status_code == 201
    proposal = proposal_resp.json()
    assert proposal["status"] == "pending"

    approve_resp = client.post(
        f"/api/v1/approvals/{proposal['id']}/approve",
        json={"approver": "analyst_priya", "reason": "Confirmed via logs"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "executed"

    timeline_resp = client.get(f"/api/v1/incidents/{incident_id}/timeline")
    assert timeline_resp.status_code == 200
    assert len(timeline_resp.json()) >= 3  # created, proposal created, approved, executed


def test_unauthorized_double_approval_returns_409(client):
    created = client.post("/api/v1/alerts", json=ALERT).json()
    proposal = client.post(
        f"/api/v1/incidents/{created['id']}/proposals",
        json={"action_type": "block_ip", "target": "1.2.3.4", "justification": "test justification long enough here"},
    ).json()
    client.post(f"/api/v1/approvals/{proposal['id']}/approve", json={"approver": "a1", "reason": "r1"})
    second = client.post(f"/api/v1/approvals/{proposal['id']}/approve", json={"approver": "a2", "reason": "r2"})
    assert second.status_code == 409


def test_invalid_action_type_returns_422(client):
    created = client.post("/api/v1/alerts", json=ALERT).json()
    resp = client.post(
        f"/api/v1/incidents/{created['id']}/proposals",
        json={"action_type": "format_hard_drive", "target": "x", "justification": "should never be accepted at all"},
    )
    assert resp.status_code == 422


def test_approval_not_found_returns_404(client):
    resp = client.post("/api/v1/approvals/RSP-NOPE/approve", json={"approver": "a1", "reason": "r1"})
    assert resp.status_code == 404
