# MCP Server Setup Guide

AegisFlow's MCP security server exposes 7 typed tools that let any MCP client (Claude Desktop, Claude
Code, a custom agent, etc.) interact with the SOC platform directly.

## Why a separate environment?

The official `mcp` Python SDK (specifically `mcp.server.fastmcp.FastMCP`) requires `starlette>=0.46` in
recent releases, while FastAPI 0.115.x pins `starlette<0.42`. Rather than downgrade the SDK or force an
incompatible starlette version onto the main backend, the MCP server runs in its own virtual environment
(`backend/.venv-mcp`) and shares the same SQLite database file as the main API.

## Setup

```bash
cd backend
python3 -m venv .venv-mcp
source .venv-mcp/bin/activate   # or .venv-mcp\Scripts\Activate.ps1 on Windows
pip install -r requirements-mcp.txt
```

## Running standalone

```bash
python -m app.mcp_server.server
```

This starts the server over **stdio** transport — the standard way MCP clients like Claude Desktop
connect to local tools.

## Connecting Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "aegisflow-security": {
      "command": "/absolute/path/to/backend/.venv-mcp/bin/python",
      "args": ["-m", "app.mcp_server.server"],
      "cwd": "/absolute/path/to/backend",
      "env": {
        "DATABASE_URL": "sqlite:////absolute/path/to/backend/aegisflow.db",
        "VIRUSTOTAL_API_KEY": ""
      }
    }
  }
}
```

Restart Claude Desktop, and the 7 tools become available in any conversation.

## The 7 tools

| Tool | Purpose |
|---|---|
| `check_ip_reputation` | IOC enrichment for an IP (VirusTotal + GeoIP, demo fallback) |
| `check_file_hash` | IOC enrichment for a file hash |
| `search_incidents` | Filter/paginate incidents by severity/status |
| `get_incident` | Full details for one incident |
| `map_mitre_technique` | Map alert text to MITRE ATT&CK techniques |
| `get_soc_runbook` | RAG retrieval of relevant SOC runbook excerpts, with citations |
| `create_response_proposal` | Create a **pending** response proposal — never executes directly |

## Security guardrails

- **Allowlist**: only the 7 tools above can execute, checked explicitly at call time (defense in depth
  beyond what FastMCP itself exposes).
- **Per-tool timeout**: configurable via `MCP_TOOL_TIMEOUT_SECONDS` (default 10s).
- **Audit logging**: every call — success or failure — is written to the `mcp_tool_call_log` table with
  arguments and results redacted of anything secret-shaped (API keys, bearer tokens).
- **No destructive action tool**: `create_response_proposal` only ever creates a `pending` record. The
  only way to move a proposal to `executed` is through the Phase 7 Approval API, by a human.

## Testing the MCP server

```bash
cd backend
pytest tests/test_mcp_server.py -v -o asyncio_mode=auto   # uses .venv-mcp
```

Or a manual smoke test:

```python
import asyncio
from app.mcp_server.server import mcp
from app.database.session import Base, engine
import app.models

Base.metadata.create_all(bind=engine)

async def main():
    tools = await mcp.list_tools()
    print([t.name for t in tools])

asyncio.run(main())
```
