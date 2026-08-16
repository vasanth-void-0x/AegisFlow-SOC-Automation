"""Tests for the audit API (MCP tool call log + global timeline feed)."""

ALERT = {
    "source": "wazuh",
    "alert_name": "SSH Brute Force Detected",
    "severity": "high",
    "description": "test",
    "source_ip": "203.0.113.7",
    "event_time": "2026-08-12T06:00:00Z",
    "indicators": [{"type": "ip", "value": "203.0.113.7"}],
}


def test_mcp_calls_empty_initially(client):
    resp = client.get("/api/v1/audit/mcp-calls")
    assert resp.status_code == 200
    assert resp.json() == []


def test_global_timeline_shows_incident_creation_event(client):
    client.post("/api/v1/alerts", json=ALERT)
    resp = client.get("/api/v1/audit/timeline")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 1
    assert any(e["event_type"] == "incident_created" for e in events)


def test_global_timeline_respects_limit(client):
    for i in range(3):
        alert = dict(ALERT, idempotency_key=f"evt-{i}")
        client.post("/api/v1/alerts", json=alert)
    resp = client.get("/api/v1/audit/timeline?limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) <= 2
