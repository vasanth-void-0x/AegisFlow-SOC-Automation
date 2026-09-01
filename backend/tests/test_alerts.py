"""Tests for Phase 1: alert ingestion & incident retrieval."""

VALID_ALERT = {
    "source": "wazuh",
    "alert_name": "SSH Brute Force Detected",
    "severity": "high",
    "description": "Multiple failed SSH logins from a single source IP",
    "source_ip": "203.0.113.7",
    "destination_ip": "10.0.0.5",
    "hostname": "web-prod-01",
    "username": "root",
    "event_time": "2026-08-12T06:00:00Z",
    "raw_event": {"attempts": 15, "window_seconds": 60},
    "indicators": [{"type": "ip", "value": "203.0.113.7"}],
}


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_ingest_valid_alert_returns_201(client):
    resp = client.post("/api/v1/alerts", json=VALID_ALERT)
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"].startswith("INC-")
    assert body["severity"] == "high"
    assert body["status"] == "new"
    assert body["source_ip"] == "203.0.113.7"


def test_ingest_invalid_severity_returns_422(client):
    bad_alert = dict(VALID_ALERT)
    bad_alert["severity"] = "super_critical"  # not a valid enum value
    resp = client.post("/api/v1/alerts", json=bad_alert)
    assert resp.status_code == 422


def test_ingest_missing_required_field_returns_422(client):
    bad_alert = dict(VALID_ALERT)
    del bad_alert["alert_name"]
    resp = client.post("/api/v1/alerts", json=bad_alert)
    assert resp.status_code == 422


def test_duplicate_alert_returns_409(client):
    first = client.post("/api/v1/alerts", json=VALID_ALERT)
    assert first.status_code == 201
    second = client.post("/api/v1/alerts", json=VALID_ALERT)
    assert second.status_code == 409
    assert "X-Existing-Incident-Id" in second.headers
    assert second.headers["X-Existing-Incident-Id"] == first.json()["id"]


def test_duplicate_via_idempotency_key(client):
    alert_a = dict(VALID_ALERT, idempotency_key="webhook-evt-123", event_time="2026-08-12T06:05:00Z")
    alert_b = dict(VALID_ALERT, idempotency_key="webhook-evt-123", event_time="2026-08-12T06:06:00Z")
    first = client.post("/api/v1/alerts", json=alert_a)
    assert first.status_code == 201
    second = client.post("/api/v1/alerts", json=alert_b)
    assert second.status_code == 409


def test_get_incident_by_id(client):
    created = client.post("/api/v1/alerts", json=VALID_ALERT).json()
    resp = client.get(f"/api/v1/incidents/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_incident_not_found_returns_404(client):
    resp = client.get("/api/v1/incidents/INC-DOESNOTEXIST")
    assert resp.status_code == 404


def test_list_incidents_pagination(client):
    for i in range(3):
        alert = dict(VALID_ALERT, idempotency_key=f"evt-{i}", alert_name=f"Alert {i}")
        client.post("/api/v1/alerts", json=alert)

    resp = client.get("/api/v1/incidents?page=1&page_size=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["page"] == 1


def test_list_incidents_filter_by_severity(client):
    high = dict(VALID_ALERT, idempotency_key="evt-high", severity="high")
    low = dict(VALID_ALERT, idempotency_key="evt-low", severity="low")
    client.post("/api/v1/alerts", json=high)
    client.post("/api/v1/alerts", json=low)

    resp = client.get("/api/v1/incidents?severity=low")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["severity"] == "low"


def test_list_incidents_filter_by_minimum_severity(client):
    for severity in ("low", "medium", "high", "critical"):
        alert = dict(
            VALID_ALERT,
            idempotency_key=f"evt-minimum-{severity}",
            alert_name=f"{severity.title()} event",
            severity=severity,
        )
        client.post("/api/v1/alerts", json=alert)

    resp = client.get("/api/v1/incidents?status=new&minimum_severity=medium&page_size=10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert {item["severity"] for item in body["items"]} == {"medium", "high", "critical"}


def test_ingest_alert_with_invalid_indicator_type_returns_422(client):
    bad_alert = dict(VALID_ALERT, indicators=[{"type": "carrier_pigeon", "value": "x"}])
    resp = client.post("/api/v1/alerts", json=bad_alert)
    assert resp.status_code == 422


def test_oversized_payload_rejected(client):
    huge_description = "A" * 2_000_000  # ~2MB, exceeds MAX_REQUEST_BODY_BYTES default 1MB
    bad_alert = dict(VALID_ALERT, description=huge_description)
    resp = client.post("/api/v1/alerts", json=bad_alert)
    assert resp.status_code in (413, 422)


def test_patch_incident_status(client):
    created = client.post("/api/v1/alerts", json=VALID_ALERT).json()
    resp = client.patch(f"/api/v1/incidents/{created['id']}/status", json={"status": "triaging"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "triaging"


def test_patch_incident_status_not_found(client):
    resp = client.patch("/api/v1/incidents/INC-NOPE/status", json={"status": "triaging"})
    assert resp.status_code == 404


def test_patch_incident_status_invalid_value(client):
    created = client.post("/api/v1/alerts", json=VALID_ALERT).json()
    resp = client.patch(f"/api/v1/incidents/{created['id']}/status", json={"status": "banana"})
    assert resp.status_code == 422
