"""Authenticated remote gateway for BlueOrch's allowlisted MCP tools."""
import hmac
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.mcp_server.executor import ALLOWED_TOOLS, execute_tool

router = APIRouter(tags=["mcp-gateway"])


class RemoteToolCallIn(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


class RemoteToolCallOut(BaseModel):
    tool: str
    success: bool
    result: dict[str, Any]


def require_mcp_key(x_blueorch_mcp_key: str | None = Header(default=None)) -> None:
    expected = get_settings().mcp_gateway_api_key
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCP_GATEWAY_API_KEY is not configured",
        )
    if not x_blueorch_mcp_key or not hmac.compare_digest(x_blueorch_mcp_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MCP gateway key")


@router.get("/mcp/tools", dependencies=[Depends(require_mcp_key)])
def list_remote_tools() -> dict:
    return {"server": "blueorch-security", "transport": "https-gateway", "tools": sorted(ALLOWED_TOOLS)}


@router.post(
    "/mcp/tools/{tool_name}",
    response_model=RemoteToolCallOut,
    dependencies=[Depends(require_mcp_key)],
)
async def invoke_remote_tool(tool_name: str, body: RemoteToolCallIn) -> RemoteToolCallOut:
    if tool_name not in ALLOWED_TOOLS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown or disallowed MCP tool")
    try:
        result = await execute_tool(tool_name, body.arguments)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return RemoteToolCallOut(tool=tool_name, success=True, result=result)
