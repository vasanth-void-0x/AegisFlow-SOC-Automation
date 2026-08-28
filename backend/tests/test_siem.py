from unittest.mock import AsyncMock, patch
from app.integrations.siem_clients import SiemError

SPLUNK = {"provider": "splunk", "base_url": "https://splunk.example:8089", "token": "secret-token", "index_name": "security", "verify_ssl": True}

def test_dashboard_is_empty_without_siem(client):
    body = client.get("/api/v1/dashboard/kpis").json()
    assert body["connection_status"] == "not_configured"
    assert body["total_alerts"] == 0

def test_splunk_token_is_required(client):
    body = dict(SPLUNK); del body["token"]
    assert client.post("/api/v1/siem/test", json=body).status_code == 422

def test_wazuh_credentials_are_required(client):
    assert client.post("/api/v1/siem/test", json={"provider": "wazuh", "base_url": "https://wazuh.example:55000"}).status_code == 422

@patch("app.services.siem_service.make_client")
def test_connect_and_status_never_expose_secret(make_client, client):
    make_client.return_value.test = AsyncMock(return_value=None)
    response = client.post("/api/v1/siem/connect", json=SPLUNK)
    assert response.status_code == 200
    assert response.json()["connected"] is True
    status = client.get("/api/v1/siem/status").json()[0]
    assert "token" not in status and "encrypted_credentials" not in status

@patch("app.services.siem_service.make_client")
def test_failed_connection_is_not_saved(make_client, client):
    make_client.return_value.test = AsyncMock(side_effect=SiemError("authentication failed"))
    assert client.post("/api/v1/siem/connect", json=SPLUNK).status_code == 502
    assert client.get("/api/v1/siem/status").json() == []
