"""
Tests for the MCP security server. Runs in the isolated .venv-mcp environment.

These test the tool implementation functions and server guardrails directly
(allowlist, audit logging, redaction) rather than spinning up a full stdio
MCP client/server pair, which is unnecessary for unit-level verification.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database.session import Base
from app.mcp_server import tool_impl
from app.mcp_server.redaction import redact_dict, redact_text
from app.mcp_server.schemas import (
    CreateResponseProposalInput,
    GetIncidentInput,
    GetSocRunbookInput,
    MapMitreTechniqueInput,
    SearchIncidentsInput,
)
from app.models.response_proposal import ProposalStatus
from app.schemas.incident import AlertIngest
from app.services.incident_service import create_incident_from_alert


@pytest.fixture()
def db_session(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    import app.mcp_server.audit as audit_module
    import app.mcp_server.tool_impl as tool_impl_module
    import app.database.session as session_module

    monkeypatch.setattr(session_module, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(audit_module, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(tool_impl_module, "SessionLocal", TestSessionLocal)

    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


ALERT = dict(
    source="wazuh",
    alert_name="SSH Brute Force Detected",
    severity="high",
    description="Multiple failed SSH logins",
    source_ip="203.0.113.7",
    event_time="2026-08-12T06:00:00Z",
    indicators=[{"type": "ip", "value": "203.0.113.7"}],
)


# ---- Redaction ----

def test_redact_dict_masks_key_named_like_secret():
    out = redact_dict({"api_key": "sk-abc123456789", "note": "hello"})
    assert out["api_key"] == "***REDACTED***"
    assert out["note"] == "hello"


def test_redact_dict_masks_value_shaped_like_secret():
    out = redact_dict({"config": "gsk_abcdefghijklmno"})
    assert out["config"] == "***REDACTED***"


def test_redact_text_masks_bearer_token():
    text = "Request failed with Bearer sk-abcdefghij1234567890"
    redacted = redact_text(text)
    assert "sk-abcdefghij1234567890" not in redacted


# ---- search_incidents / get_incident ----

def test_search_incidents_returns_created_incident(db_session):
    create_incident_from_alert(db_session, AlertIngest(**ALERT))
    result = tool_impl.search_incidents(SearchIncidentsInput(page=1, page_size=10))
    assert result["total"] == 1
    assert result["incidents"][0]["alert_name"] == "SSH Brute Force Detected"


def test_search_incidents_invalid_severity_raises(db_session):
    with pytest.raises(ValueError):
        tool_impl.search_incidents(SearchIncidentsInput(severity="super_bad"))


def test_get_incident_not_found_raises(db_session):
    with pytest.raises(ValueError):
        tool_impl.get_incident(GetIncidentInput(incident_id="INC-NOPE"))


def test_get_incident_returns_full_record(db_session):
    incident = create_incident_from_alert(db_session, AlertIngest(**ALERT))
    result = tool_impl.get_incident(GetIncidentInput(incident_id=incident.id))
    assert result["id"] == incident.id
    assert result["severity"] == "high"


# ---- map_mitre_technique / get_soc_runbook ----

def test_map_mitre_technique_finds_brute_force():
    result = tool_impl.map_mitre_technique(MapMitreTechniqueInput(alert_text="SSH Brute Force Detected"))
    assert any(t["technique_id"] == "T1110" for t in result["techniques"])


def test_get_soc_runbook_finds_relevant_runbook():
    result = tool_impl.get_soc_runbook(GetSocRunbookInput(query="brute force ssh login failed attempts"))
    assert result["found"] is True
    assert len(result["results"]) > 0


# ---- create_response_proposal (must never execute directly) ----

def test_create_response_proposal_stays_pending(db_session):
    incident = create_incident_from_alert(db_session, AlertIngest(**ALERT))
    result = tool_impl.create_response_proposal(
        CreateResponseProposalInput(
            incident_id=incident.id,
            action_type="block_ip",
            target="203.0.113.7",
            justification="Repeated brute force attempts from this IP address observed in logs.",
        )
    )
    assert result["status"] == ProposalStatus.pending.value
    assert "requires human approval" in result["note"]


def test_create_response_proposal_invalid_action_type_raises(db_session):
    incident = create_incident_from_alert(db_session, AlertIngest(**ALERT))
    with pytest.raises(ValueError):
        tool_impl.create_response_proposal(
            CreateResponseProposalInput(
                incident_id=incident.id,
                action_type="delete_entire_database",
                target="x",
                justification="this should never be accepted as a valid action type",
            )
        )


def test_create_response_proposal_unknown_incident_raises(db_session):
    with pytest.raises(ValueError):
        tool_impl.create_response_proposal(
            CreateResponseProposalInput(
                incident_id="INC-NOPE",
                action_type="block_ip",
                target="1.2.3.4",
                justification="test justification text long enough",
            )
        )


# ---- Async tools ----

@pytest.mark.asyncio
async def test_check_ip_reputation_tool(db_session):
    from app.mcp_server.schemas import CheckIpReputationInput

    result = await tool_impl.check_ip_reputation(CheckIpReputationInput(ip="8.8.8.8"))
    assert result["indicator_type"] == "ip"
    assert result["source"] == "demo"


@pytest.mark.asyncio
async def test_check_file_hash_tool(db_session):
    from app.mcp_server.schemas import CheckFileHashInput

    result = await tool_impl.check_file_hash(CheckFileHashInput(file_hash="a" * 64))
    assert result["indicator_type"] == "hash"


# ---- Server-level allowlist ----

def test_allowlist_contains_exactly_seven_tools():
    from app.mcp_server.server import ALLOWED_TOOLS

    assert len(ALLOWED_TOOLS) == 7
    assert ALLOWED_TOOLS == {
        "check_ip_reputation",
        "check_file_hash",
        "search_incidents",
        "get_incident",
        "map_mitre_technique",
        "get_soc_runbook",
        "create_response_proposal",
    }
