from app.core.config import get_settings


def test_direct_log_is_normalized_and_creates_incident(client):
    response = client.post("/api/v1/logs/ingest", json={
        "message": "Failed login brute force from 203.0.113.10 to 10.0.0.5",
        "source_type": "agent",
        "source_name": "windows-lab",
        "hostname": "LAB-PC",
        "event_id": "evt-1001",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "direct:agent:windows-lab"
    assert body["severity"] == "high"
    assert body["source_ip"] == "203.0.113.10"
    assert body["destination_ip"] == "10.0.0.5"
    assert body["indicators"][0]["value"] == "203.0.113.10"


def test_direct_log_deduplication(client):
    payload = {"message": "Suspicious access denied", "event_id": "same-event"}
    assert client.post("/api/v1/logs/ingest", json=payload).status_code == 201
    duplicate = client.post("/api/v1/logs/ingest", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.headers["x-existing-incident-id"].startswith("INC-")


def test_direct_log_api_key_when_configured(client):
    settings = get_settings()
    original = settings.direct_log_api_key
    settings.direct_log_api_key = "collector-secret"
    try:
        assert client.post("/api/v1/logs/ingest", json={"message": "test"}).status_code == 401
        assert client.post(
            "/api/v1/logs/ingest",
            headers={"X-BlueOrch-Key": "collector-secret"},
            json={"message": "test", "event_id": "authorized"},
        ).status_code == 201
    finally:
        settings.direct_log_api_key = original


def test_bulk_direct_logs_and_final_report(client):
    response = client.post("/api/v1/logs/bulk", json={"logs": [
        {"message": "warning authentication failure", "event_id": "bulk-1"},
        {"message": "ransomware detected", "event_id": "bulk-2"},
    ]})
    assert response.status_code == 200
    assert response.json()["accepted"] == 2
    incident_id = response.json()["incidents"][1]["id"]
    report = client.get(f"/api/v1/incidents/{incident_id}/report")
    assert report.status_code == 200
    assert report.json()["report_version"] == "blueorch-1.0"
