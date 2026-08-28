"""
BlueOrch MCP Security Server.

Run standalone (separate venv - see backend/requirements-mcp.txt):
    ./.venv-mcp/bin/python -m app.mcp_server.server

Exposes 7 typed, allowlisted tools over stdio. Every call is timed,
timeout-enforced, and written to the audit log with secrets redacted.
"""
import asyncio

from mcp.server.fastmcp import FastMCP

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.session import Base, engine
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
import app.models  # noqa: F401 - registers all ORM tables

configure_logging()
logger = get_logger(__name__)
settings = get_settings()

# Explicit allowlist - defense in depth. Only these tool names may execute,
# even though FastMCP itself only ever exposes what's registered below.
ALLOWED_TOOLS = {
    "check_ip_reputation",
    "check_file_hash",
    "search_incidents",
    "get_incident",
    "map_mitre_technique",
    "get_soc_runbook",
    "create_response_proposal",
}

mcp = FastMCP("aegisflow-security")


def _guarded(tool_name: str, async_call):
    """Wrap an async tool call with allowlist check, timeout, and audit logging.

    `async_call` must be a zero-arg async callable (e.g. a closure) that
    performs the actual work and returns a JSON-serializable dict.
    """

    async def wrapper(args_dict: dict) -> dict:
        if tool_name not in ALLOWED_TOOLS:
            raise PermissionError(f"Tool '{tool_name}' is not on the allowlist")

        with audit_tool_call(tool_name, args_dict) as record:
            result = await asyncio.wait_for(async_call(), timeout=settings.mcp_tool_timeout_seconds)
            record["result_summary"] = result
            return result

    return wrapper


@mcp.tool()
async def check_ip_reputation(ip: str) -> dict:
    """Check an IP address's reputation via threat intelligence (VirusTotal + GeoIP)."""
    args = {"ip": ip}
    guarded = _guarded("check_ip_reputation", lambda: tool_impl.check_ip_reputation(CheckIpReputationInput(**args)))
    return await guarded(args)


@mcp.tool()
async def check_file_hash(file_hash: str) -> dict:
    """Check a file hash (MD5/SHA1/SHA256) against threat intelligence."""
    args = {"file_hash": file_hash}
    guarded = _guarded("check_file_hash", lambda: tool_impl.check_file_hash(CheckFileHashInput(**args)))
    return await guarded(args)


@mcp.tool()
async def search_incidents(
    severity: str | None = None, status: str | None = None, page: int = 1, page_size: int = 10
) -> dict:
    """Search/filter SOC incidents by severity and status, with pagination."""
    args = {"severity": severity, "status": status, "page": page, "page_size": page_size}
    guarded = _guarded(
        "search_incidents",
        lambda: asyncio.to_thread(tool_impl.search_incidents, SearchIncidentsInput(**args)),
    )
    return await guarded(args)


@mcp.tool()
async def get_incident(incident_id: str) -> dict:
    """Fetch full details for a single incident by ID."""
    args = {"incident_id": incident_id}
    guarded = _guarded(
        "get_incident", lambda: asyncio.to_thread(tool_impl.get_incident, GetIncidentInput(**args))
    )
    return await guarded(args)


@mcp.tool()
async def map_mitre_technique(alert_text: str) -> dict:
    """Map alert text to relevant MITRE ATT&CK techniques."""
    args = {"alert_text": alert_text}
    guarded = _guarded(
        "map_mitre_technique",
        lambda: asyncio.to_thread(tool_impl.map_mitre_technique, MapMitreTechniqueInput(**args)),
    )
    return await guarded(args)


@mcp.tool()
async def get_soc_runbook(query: str) -> dict:
    """Retrieve the most relevant SOC runbook excerpt(s) for a given alert/scenario, with citations."""
    args = {"query": query}
    guarded = _guarded(
        "get_soc_runbook", lambda: asyncio.to_thread(tool_impl.get_soc_runbook, GetSocRunbookInput(**args))
    )
    return await guarded(args)


@mcp.tool()
async def create_response_proposal(
    incident_id: str, action_type: str, target: str, justification: str, proposed_by: str = "mcp_tool"
) -> dict:
    """
    Create a PENDING response proposal (e.g. block_ip, isolate_host). This
    tool NEVER executes an action directly - it only creates a proposal that
    a human analyst must approve via the /approvals API before anything runs.
    """
    args = {
        "incident_id": incident_id,
        "action_type": action_type,
        "target": target,
        "justification": justification,
        "proposed_by": proposed_by,
    }
    guarded = _guarded(
        "create_response_proposal",
        lambda: asyncio.to_thread(tool_impl.create_response_proposal, CreateResponseProposalInput(**args)),
    )
    return await guarded(args)


def main() -> None:
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    logger.info("Starting BlueOrch MCP server with %d allowlisted tools", len(ALLOWED_TOOLS))
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
