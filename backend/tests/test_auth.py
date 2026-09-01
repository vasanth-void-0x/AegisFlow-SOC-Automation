from app.core.config import get_settings


def _enable_auth(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_secret", "test-secret-that-is-at-least-thirty-two-bytes")
    monkeypatch.setattr(settings, "auth_admin_password", "Admin-pass-123!")
    monkeypatch.setattr(settings, "auth_analyst_password", "Analyst-pass-123!")
    monkeypatch.setattr(settings, "auth_viewer_password", "Viewer-pass-123!")
    monkeypatch.setattr(settings, "environment", "development")


def test_login_me_logout(client, monkeypatch):
    _enable_auth(monkeypatch)
    assert client.get("/api/v1/incidents").status_code == 401
    login = client.post("/api/v1/auth/login", json={"username": "viewer", "password": "Viewer-pass-123!"})
    assert login.status_code == 200
    assert login.json()["role"] == "viewer"
    assert client.get("/api/v1/auth/me").json()["username"] == "viewer"
    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/auth/me").status_code == 401


def test_viewer_cannot_mutate_incident(client, monkeypatch):
    _enable_auth(monkeypatch)
    client.post("/api/v1/auth/login", json={"username": "viewer", "password": "Viewer-pass-123!"})
    response = client.post("/api/v1/alerts", json={})
    assert response.status_code == 403


def test_automation_key_can_poll(client, monkeypatch):
    _enable_auth(monkeypatch)
    monkeypatch.setattr(get_settings(), "automation_api_key", "n8n-test-key")
    response = client.get("/api/v1/incidents", headers={"X-BlueOrch-Automation-Key": "n8n-test-key"})
    assert response.status_code == 200
