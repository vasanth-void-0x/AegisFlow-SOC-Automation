"""Remote MCP gateway authentication and allowlist tests."""
from app.api import mcp_gateway
from app.core.config import Settings


def _settings():
    return Settings(mcp_gateway_api_key="test-mcp-gateway-key")


def test_remote_gateway_requires_key(client, monkeypatch):
    monkeypatch.setattr(mcp_gateway, "get_settings", _settings)
    response = client.get("/api/v1/mcp/tools")
    assert response.status_code == 401


def test_remote_gateway_lists_allowlisted_tools(client, monkeypatch):
    monkeypatch.setattr(mcp_gateway, "get_settings", _settings)
    response = client.get(
        "/api/v1/mcp/tools", headers={"X-BlueOrch-MCP-Key": "test-mcp-gateway-key"}
    )
    assert response.status_code == 200
    assert len(response.json()["tools"]) == 7


def test_remote_gateway_rejects_unknown_tool(client, monkeypatch):
    monkeypatch.setattr(mcp_gateway, "get_settings", _settings)
    response = client.post(
        "/api/v1/mcp/tools/run_shell",
        headers={"X-BlueOrch-MCP-Key": "test-mcp-gateway-key"},
        json={"arguments": {"command": "whoami"}},
    )
    assert response.status_code == 404


def test_remote_gateway_invokes_safe_tool(client, monkeypatch):
    monkeypatch.setattr(mcp_gateway, "get_settings", _settings)

    async def fake_execute(tool_name, arguments):
        return {"techniques": [{"technique_id": "T1110"}]}

    monkeypatch.setattr(mcp_gateway, "execute_tool", fake_execute)
    response = client.post(
        "/api/v1/mcp/tools/map_mitre_technique",
        headers={"X-BlueOrch-MCP-Key": "test-mcp-gateway-key"},
        json={"arguments": {"alert_text": "SSH brute force"}},
    )
    assert response.status_code == 200
    assert response.json()["result"]["techniques"][0]["technique_id"] == "T1110"
