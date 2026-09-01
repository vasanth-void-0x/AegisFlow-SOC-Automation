"""Deep investigation orchestration tests."""
from types import SimpleNamespace

import pytest

from app.ai import investigation_service
from app.schemas.incident import AlertIngest
from app.services.incident_service import create_incident_from_alert


@pytest.mark.asyncio
async def test_deep_investigation_collects_mcp_evidence(db_session, monkeypatch):
    incident = create_incident_from_alert(
        db_session,
        AlertIngest(
            source="direct:agent:BLUEORCH-WIN-02",
            alert_name="Encoded PowerShell Execution",
            severity="high",
            description="PowerShell launched with an encoded command",
            source_ip="203.0.113.99",
            hostname="BLUEORCH-WIN-02",
            event_time="2026-09-01T10:00:00Z",
            indicators=[{"type": "ip", "value": "203.0.113.99"}],
        ),
    )
    calls = []

    async def fake_tool(name, arguments):
        calls.append(name)
        fixtures = {
            "get_incident": {"id": incident.id},
            "map_mitre_technique": {"techniques": [{"technique_id": "T1059.001"}]},
            "get_soc_runbook": {"found": True, "results": [{"citation": "runbook", "text": "isolate if confirmed"}]},
            "search_incidents": {"incidents": []},
            "check_ip_reputation": {"indicator_type": "ip", "value": "203.0.113.99", "provider_status": "live"},
        }
        return fixtures[name]

    captured = {}

    def fake_triage(db, selected_incident, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id="TRG-DEEP-TEST")

    monkeypatch.setattr(investigation_service, "execute_tool", fake_tool)
    monkeypatch.setattr(investigation_service, "run_triage", fake_triage)

    record = await investigation_service.run_deep_investigation(db_session, incident)
    assert record.id == "TRG-DEEP-TEST"
    assert calls == [
        "get_incident",
        "map_mitre_technique",
        "get_soc_runbook",
        "search_incidents",
        "check_ip_reputation",
    ]
    assert captured["mitre_context"][0]["technique_id"] == "T1059.001"
    assert captured["enrichment_context"][0]["provider_status"] == "live"
