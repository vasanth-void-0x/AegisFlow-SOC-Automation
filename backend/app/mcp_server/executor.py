"""Shared, audited MCP tool executor for stdio and remote HTTP callers."""
import asyncio
from typing import Any

from app.core.config import get_settings
from app.mcp_server import tool_impl
from app.mcp_server.audit import audit_tool_call
from app.mcp_server.schemas import (
    CheckFileHashInput,
    CheckIpReputationInput,
    CreateResponseProposalInput,
    GetIncidentInput,
    GetSocRunbookInput,
    MapMitreTechniqueInput,
    SearchIncidentsInput,
)

ALLOWED_TOOLS = {
    "check_ip_reputation",
    "check_file_hash",
    "search_incidents",
    "get_incident",
    "map_mitre_technique",
    "get_soc_runbook",
    "create_response_proposal",
}


def _summary(result: dict[str, Any]) -> dict[str, Any]:
    """Keep the audit useful without copying large runbook/evidence payloads."""
    if "results" in result and isinstance(result["results"], list):
        return {"found": result.get("found"), "result_count": len(result["results"])}
    if "incidents" in result and isinstance(result["incidents"], list):
        return {"total": result.get("total"), "returned": len(result["incidents"])}
    return result


async def _invoke(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "check_ip_reputation":
        return await tool_impl.check_ip_reputation(CheckIpReputationInput(**arguments))
    if tool_name == "check_file_hash":
        return await tool_impl.check_file_hash(CheckFileHashInput(**arguments))
    if tool_name == "search_incidents":
        return await asyncio.to_thread(tool_impl.search_incidents, SearchIncidentsInput(**arguments))
    if tool_name == "get_incident":
        return await asyncio.to_thread(tool_impl.get_incident, GetIncidentInput(**arguments))
    if tool_name == "map_mitre_technique":
        return await asyncio.to_thread(tool_impl.map_mitre_technique, MapMitreTechniqueInput(**arguments))
    if tool_name == "get_soc_runbook":
        return await asyncio.to_thread(tool_impl.get_soc_runbook, GetSocRunbookInput(**arguments))
    if tool_name == "create_response_proposal":
        return await asyncio.to_thread(
            tool_impl.create_response_proposal, CreateResponseProposalInput(**arguments)
        )
    raise PermissionError(f"Tool '{tool_name}' is not on the allowlist")


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate, time-limit, invoke, and audit one allowlisted tool call."""
    if tool_name not in ALLOWED_TOOLS:
        raise PermissionError(f"Tool '{tool_name}' is not on the allowlist")
    settings = get_settings()
    with audit_tool_call(tool_name, arguments) as record:
        result = await asyncio.wait_for(
            _invoke(tool_name, arguments), timeout=settings.mcp_tool_timeout_seconds
        )
        record["result_summary"] = _summary(result)
        return result
