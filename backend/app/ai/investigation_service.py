"""Evidence-grounded investigation orchestrated through audited MCP tools."""
from typing import Any

from sqlalchemy.orm import Session

from app.ai.triage_service import run_triage
from app.core.logging import get_logger
from app.mcp_server.executor import execute_tool
from app.models.incident import Incident
from app.models.triage import TriageRecord

logger = get_logger(__name__)


async def _safe_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        return await execute_tool(tool_name, arguments)
    except Exception as exc:  # noqa: BLE001 - one provider/tool must not drop the incident
        logger.warning("Investigation tool failed tool=%s: %s", tool_name, exc)
        return {"tool": tool_name, "available": False, "error": str(exc)}


async def run_deep_investigation(db: Session, incident: Incident) -> TriageRecord:
    """Collect MCP evidence, then ask the model for one strict structured decision."""
    incident_context = await _safe_tool("get_incident", {"incident_id": incident.id})
    alert_text = f"{incident.alert_name} {incident.description}"
    mitre = await _safe_tool("map_mitre_technique", {"alert_text": alert_text})
    runbook = await _safe_tool("get_soc_runbook", {"query": alert_text})
    related = await _safe_tool(
        "search_incidents",
        {"severity": incident.severity.value, "status": None, "page": 1, "page_size": 10},
    )

    enrichment: list[dict[str, Any]] = []
    for indicator in incident.indicators:
        indicator_type = str(indicator.get("type", "")).lower()
        value = str(indicator.get("value", ""))
        if indicator_type == "ip":
            enrichment.append(await _safe_tool("check_ip_reputation", {"ip": value}))
        elif indicator_type == "hash":
            enrichment.append(await _safe_tool("check_file_hash", {"file_hash": value}))
        else:
            enrichment.append(
                {
                    "indicator_type": indicator_type,
                    "value": value,
                    "provider_status": "unsupported_by_mcp_tool",
                    "error": "No allowlisted reputation tool for this indicator type",
                }
            )

    runbook_excerpt = None
    if runbook.get("found") and runbook.get("results"):
        top = runbook["results"][0]
        runbook_excerpt = f"{top.get('citation')}\n{top.get('text')}"

    related_items = [
        item for item in related.get("incidents", []) if item.get("id") != incident.id
    ][:5]
    record = run_triage(
        db,
        incident,
        enrichment_context=enrichment,
        runbook_excerpt=runbook_excerpt,
        related_incidents=related_items,
        mitre_context=mitre.get("techniques", []),
    )

    from app.services.timeline_service import add_event

    add_event(
        db,
        incident.id,
        event_type="deep_ai_investigation_completed",
        description="Deep AI investigation completed using audited MCP evidence",
        actor="n8n_mcp_v3",
        metadata={
            "triage_record_id": record.id,
            "mcp_evidence_count": 4 + len(enrichment),
            "incident_context_available": incident_context.get("id") == incident.id,
        },
    )
    return record
