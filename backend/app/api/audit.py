"""API: MCP tool call audit log (read-only - the log itself is append-only,
written by the MCP server process), and the cross-incident timeline feed."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.mcp_audit import McpToolCallLog
from app.models.timeline import TimelineEvent

router = APIRouter(tags=["audit"])


class McpToolCallLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tool_name: str
    arguments: dict
    result_summary: dict | None
    success: bool
    error: str | None
    duration_ms: int | None
    created_at: str


class TimelineEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    event_type: str
    description: str
    actor: str
    event_metadata: dict
    created_at: str


@router.get("/audit/timeline", response_model=list[TimelineEventOut])
def list_recent_timeline_events(
    limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)
) -> list[TimelineEventOut]:
    """Cross-incident audit feed - every timeline event across the whole system, most recent first."""
    rows = db.execute(select(TimelineEvent).order_by(TimelineEvent.created_at.desc()).limit(limit)).scalars().all()
    return [
        TimelineEventOut(
            id=r.id,
            incident_id=r.incident_id,
            event_type=r.event_type,
            description=r.description,
            actor=r.actor,
            event_metadata=r.event_metadata,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/audit/mcp-calls", response_model=list[McpToolCallLogOut])
def list_mcp_tool_calls(
    limit: int = Query(default=50, ge=1, le=200),
    tool_name: str | None = None,
    db: Session = Depends(get_db),
) -> list[McpToolCallLogOut]:
    query = select(McpToolCallLog).order_by(McpToolCallLog.created_at.desc()).limit(limit)
    if tool_name:
        query = query.where(McpToolCallLog.tool_name == tool_name)
    rows = db.execute(query).scalars().all()
    return [
        McpToolCallLogOut(
            id=r.id,
            tool_name=r.tool_name,
            arguments=r.arguments,
            result_summary=r.result_summary,
            success=r.success,
            error=r.error,
            duration_ms=r.duration_ms,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]
