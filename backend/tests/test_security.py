"""
Phase 9: security tests.

Covers: prompt injection (already deep-tested in test_triage.py, summarized
here), SQL injection attempts, secret leakage, oversized payloads, CORS/
security headers, rate limiting, unauthorized approval actions, invalid
JSON, and duplicate-event handling (dedup already covered in test_alerts.py).
"""
import json

ALERT = {
    "source": "wazuh",
    "alert_name": "SSH Brute Force Detected",
    "severity": "high",
    "description": "test",
    "source_ip": "203.0.113.7",
    "event_time": "2026-08-12T06:00:00Z",
    "indicators": [{"type": "ip", "value": "203.0.113.7"}],
}


# ---- SQL injection ----

def test_sql_injection_in_alert_name_is_stored_safely_not_executed(client):
    """SQLAlchemy's parameterized queries neutralize this - confirm the
    payload is stored as inert data and doesn't corrupt the DB or error out."""
    payload = "Robert'); DROP TABLE incidents;--"
    alert = dict(ALERT, alert_name=payload, idempotency_key="sqli-test-1")
    resp = client.post("/api/v1/alerts", json=alert)
    assert resp.status_code == 201
    assert resp.json()["alert_name"] == payload  # stored verbatim as data, not executed

    # Table must still exist and be queryable afterward
    list_resp = client.get("/api/v1/incidents")
    assert list_resp.status_code == 200


def test_sql_injection_in_search_query_param_is_safe(client):
    payload = "' OR '1'='1"
    resp = client.get(f"/api/v1/runbooks/search?query={payload}")
    assert resp.status_code == 200  # treated as an ordinary (low-relevance) search string


def test_sql_injection_in_incident_id_path_returns_404_not_error(client):
    payload = "INC-1' OR '1'='1"
    resp = client.get(f"/api/v1/incidents/{payload}")
    assert resp.status_code == 404


# ---- Secret leakage ----

def test_health_endpoint_never_leaks_api_keys(client):
    resp = client.get("/health")
    body_text = json.dumps(resp.json())
    assert "sk-" not in body_text
    assert "gsk_" not in body_text
    assert "api_key" not in body_text.lower() or "api_key" not in resp.json()


def test_validation_error_does_not_echo_request_secrets(client):
    """If a client accidentally puts a secret-shaped string in a bad field,
    the 422 response shouldn't need to (and doesn't) treat it specially -
    but we confirm the response body only contains what Pydantic reports,
    not raw request internals like headers/auth."""
    bad_alert = dict(ALERT, severity="not_a_real_severity")
    resp = client.post(
        "/api/v1/alerts",
        json=bad_alert,
        headers={"Authorization": "Bearer sk-should-never-be-echoed-back-1234567890"},
    )
    assert resp.status_code == 422
    body_text = json.dumps(resp.json())
    assert "sk-should-never-be-echoed-back" not in body_text


# ---- Oversized payloads ----

def test_oversized_description_rejected(client):
    huge = "A" * 2_000_000
    alert = dict(ALERT, description=huge)
    resp = client.post("/api/v1/alerts", json=alert)
    assert resp.status_code in (413, 422)


def test_oversized_raw_event_rejected(client):
    huge_raw_event = {"data": "B" * 2_000_000}
    alert = dict(ALERT, raw_event=huge_raw_event, idempotency_key="oversize-2")
    resp = client.post("/api/v1/alerts", json=alert)
    assert resp.status_code in (413, 422)


# ---- Invalid JSON ----

def test_malformed_json_body_returns_422_not_500(client):
    resp = client.post(
        "/api/v1/alerts", content=b"{not valid json!!", headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 422


# ---- Security headers / CORS ----

def test_security_headers_present(client):
    resp = client.get("/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"


# ---- Unauthorized / invalid approval actions ----

def test_cannot_approve_nonexistent_proposal(client):
    resp = client.post("/api/v1/approvals/RSP-DOESNOTEXIST/approve", json={"approver": "x", "reason": "test reason"})
    assert resp.status_code == 404


def test_cannot_approve_already_approved_proposal_twice(client):
    created = client.post("/api/v1/alerts", json=dict(ALERT, idempotency_key="approve-twice")).json()
    proposal = client.post(
        f"/api/v1/incidents/{created['id']}/proposals",
        json={"action_type": "block_ip", "target": "1.2.3.4", "justification": "confirmed malicious source"},
    ).json()
    first = client.post(f"/api/v1/approvals/{proposal['id']}/approve", json={"approver": "a", "reason": "confirmed"})
    assert first.status_code == 200
    second = client.post(f"/api/v1/approvals/{proposal['id']}/approve", json={"approver": "a", "reason": "confirmed again"})
    assert second.status_code == 409  # already decided, cannot re-approve


def test_reject_requires_a_reason(client):
    created = client.post("/api/v1/alerts", json=dict(ALERT, idempotency_key="reject-no-reason")).json()
    proposal = client.post(
        f"/api/v1/incidents/{created['id']}/proposals",
        json={"action_type": "isolate_host", "target": "host-1", "justification": "malware detected on this host"},
    ).json()
    resp = client.post(f"/api/v1/approvals/{proposal['id']}/reject", json={"approver": "a", "reason": ""})
    assert resp.status_code == 422


def test_invalid_action_type_rejected(client):
    created = client.post("/api/v1/alerts", json=dict(ALERT, idempotency_key="bad-action-type")).json()
    resp = client.post(
        f"/api/v1/incidents/{created['id']}/proposals",
        json={"action_type": "wipe_entire_disk", "target": "x", "justification": "this must never be accepted"},
    )
    assert resp.status_code == 422


# ---- Rate limiting ----

def test_rate_limit_blocks_excessive_requests(client, monkeypatch):
    from app.core.config import Settings
    import app.core.rate_limit as rl_module

    # Tight limit for a fast, deterministic test
    monkeypatch.setattr(rl_module, "get_settings", lambda: Settings(rate_limit_per_minute=3))

    statuses = [client.get("/health").status_code for _ in range(6)]
    assert 429 in statuses


def test_rate_limit_disabled_when_zero(client, monkeypatch):
    from app.core.config import Settings
    import app.core.rate_limit as rl_module

    monkeypatch.setattr(rl_module, "get_settings", lambda: Settings(rate_limit_per_minute=0))
    statuses = [client.get("/health").status_code for _ in range(10)]
    assert all(s == 200 for s in statuses)
