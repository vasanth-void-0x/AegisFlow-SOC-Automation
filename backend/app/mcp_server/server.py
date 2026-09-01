"""
BlueOrch MCP Security Server.

Run standalone (separate venv - see backend/requirements-mcp.txt):
    ./.venv-mcp/bin/python -m app.mcp_server.server

Exposes 7 typed, allowlisted tools over stdio. Every call is timed,
timeout-enforced, and written to the audit log with secrets redacted.
"""
try:
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:  # Main API venv intentionally excludes the isolated MCP SDK.
    class FastMCP:  # type: ignore[no-redef]
        def __init__(self, *_args, **_kwargs):
            pass

        def tool(self, *_args, **_kwargs):
            return lambda function: function

        def run(self, *_args, **_kwargs):
            raise RuntimeError("Install backend/requirements-mcp.txt before running the MCP server")

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.session import Base, engine
from app.mcp_server.executor import ALLOWED_TOOLS, execute_tool
import app.models  # noqa: F401 - registers all ORM tables

configure_logging()
logger = get_logger(__name__)
settings = get_settings()

mcp = FastMCP("blueorch-security")


@mcp.tool()
async def check_ip_reputation(ip: str) -> dict:
    """Check an IP address's reputation via threat intelligence (VirusTotal + GeoIP)."""
    args = {"ip": ip}
    return await execute_tool("check_ip_reputation", args)


@mcp.tool()
async def check_file_hash(file_hash: str) -> dict:
    """Check a file hash (MD5/SHA1/SHA256) against threat intelligence."""
    args = {"file_hash": file_hash}
    return await execute_tool("check_file_hash", args)


@mcp.tool()
async def search_incidents(
    severity: str | None = None, status: str | None = None, page: int = 1, page_size: int = 10
) -> dict:
    """Search/filter SOC incidents by severity and status, with pagination."""
    args = {"severity": severity, "status": status, "page": page, "page_size": page_size}
    return await execute_tool("search_incidents", args)


@mcp.tool()
async def get_incident(incident_id: str) -> dict:
    """Fetch full details for a single incident by ID."""
    args = {"incident_id": incident_id}
    return await execute_tool("get_incident", args)


@mcp.tool()
async def map_mitre_technique(alert_text: str) -> dict:
    """Map alert text to relevant MITRE ATT&CK techniques."""
    args = {"alert_text": alert_text}
    return await execute_tool("map_mitre_technique", args)


@mcp.tool()
async def get_soc_runbook(query: str) -> dict:
    """Retrieve the most relevant SOC runbook excerpt(s) for a given alert/scenario, with citations."""
    args = {"query": query}
    return await execute_tool("get_soc_runbook", args)


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
    return await execute_tool("create_response_proposal", args)


def main() -> None:
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    logger.info("Starting BlueOrch MCP server with %d allowlisted tools", len(ALLOWED_TOOLS))
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
