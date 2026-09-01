from app.core.config import get_settings


def test_n8n_status_update_accepts_scoped_key_in_body(client):
    settings = get_settings()
    old = (settings.auth_enabled, settings.auth_secret, settings.mcp_gateway_api_key)
    settings.auth_enabled = True
    settings.auth_secret = "test-secret-that-is-long-enough-for-hmac"
    settings.mcp_gateway_api_key = "test-mcp-service-key"
    try:
        created = client.post(
            "/api/v1/alerts",
            json={
                "source": "test",
                "alert_name": "n8n body auth",
                "description": "service authentication regression test",
                "severity": "high",
                "source_ip": "203.0.113.10",
                "event_time": "2026-01-01T00:00:00Z",
            },
        )
        incident_id = created.json()["id"]

        denied = client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "triaging"},
        )
        assert denied.status_code == 401

        accepted = client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "triaging", "service_key": "test-mcp-service-key"},
        )
        assert accepted.status_code == 200
        assert accepted.json()["status"] == "triaging"
    finally:
        settings.auth_enabled, settings.auth_secret, settings.mcp_gateway_api_key = old


def test_bootstrap_login_and_viewer_write_denial(client):
    settings=get_settings(); old=(settings.auth_enabled,settings.auth_secret,settings.auth_bootstrap_token)
    settings.auth_enabled=True; settings.auth_secret="test-secret-that-is-long-enough-for-hmac"; settings.auth_bootstrap_token="test-bootstrap-token-long"
    try:
        boot=client.post("/api/v1/auth/bootstrap",json={"setup_token":"test-bootstrap-token-long","username":"vasanth","password":"StrongPassword123!","display_name":"Vasanth"})
        assert boot.status_code==201 and boot.json()["role"]=="admin"
        assert client.post("/api/v1/auth/bootstrap",json={"setup_token":"test-bootstrap-token-long","username":"second","password":"StrongPassword123!","display_name":"Second"}).status_code==409
        assert client.post("/api/v1/auth/users",json={"username":"viewer","password":"ViewerPassword123!","display_name":"Read Only","role":"viewer"}).status_code==201
        client.post("/api/v1/auth/logout")
        assert client.get("/api/v1/auth/me").status_code==401
        assert client.post("/api/v1/auth/login",json={"username":"viewer","password":"ViewerPassword123!"}).status_code==200
        created=client.post("/api/v1/alerts",json={"source":"test","alert_name":"Test alert","description":"test","severity":"high","source_ip":"203.0.113.1","event_time":"2026-01-01T00:00:00Z"})
        denied=client.post(f"/api/v1/incidents/{created.json()['id']}/proposals",json={"action_type":"block_ip","target":"203.0.113.1","justification":"Evidence supports containment"})
        assert denied.status_code==403
    finally:
        settings.auth_enabled,settings.auth_secret,settings.auth_bootstrap_token=old
