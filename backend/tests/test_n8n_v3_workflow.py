import json
from pathlib import Path


WORKFLOW_PATH = Path(__file__).parents[2] / "n8n" / "blueorch-incident-automation-v3.json"


def _workflow_nodes() -> dict[str, dict]:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    return {node["name"]: node for node in workflow["nodes"]}


def test_high_risk_approval_is_policy_driven() -> None:
    code = _workflow_nodes()["Build Evidence-Based Response"]["parameters"]["jsCode"]
    assert "classification === 'true_positive'" in code
    assert "['high','critical'].includes(severity)" in code
    assert "Boolean(result.requires_human_approval)" not in code


def test_protected_status_updates_use_mcp_service_key() -> None:
    nodes = _workflow_nodes()
    for name in (
        "Claim Incident - Triaging",
        "Send to Human Approval Centre",
        "Release Incident for Retry",
    ):
        headers = nodes[name]["parameters"]["headerParameters"]["parameters"]
        assert {
            "name": "X-BlueOrch-MCP-Key",
            "value": "={{$env.BLUEORCH_MCP_KEY}}",
        } in headers
        assert "service_key: $env.BLUEORCH_MCP_KEY" in nodes[name]["parameters"]["jsonBody"]
