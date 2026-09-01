"""Phase 3 API: AI triage."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.investigation_service import run_deep_investigation
from app.ai.triage_service import run_triage
from app.api.mcp_gateway import require_mcp_key
from app.database.session import get_db
from app.models.triage import TriageRecord
from app.rag.retriever import format_citation, retrieve_runbook
from app.schemas.triage import TriageRecordOut
from app.services.incident_service import get_incident

router = APIRouter(tags=["triage"])


@router.post(
    "/incidents/{incident_id}/investigate",
    response_model=TriageRecordOut,
    responses={404: {"description": "Incident not found"}},
    dependencies=[Depends(require_mcp_key)],
)
async def trigger_deep_investigation(
    incident_id: str, db: Session = Depends(get_db)
) -> TriageRecordOut:
    """Run the V3 evidence pipeline through audited MCP tools and Groq."""
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")
    record = await run_deep_investigation(db, incident)
    return TriageRecordOut.model_validate(record)


@router.post(
    "/incidents/{incident_id}/triage",
    response_model=TriageRecordOut,
    responses={404: {"description": "Incident not found"}},
)
async def trigger_triage(incident_id: str, db: Session = Depends(get_db)) -> TriageRecordOut:
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")

    # Best-effort enrichment context - reuse Phase 2 results if the caller
    # already enriched, otherwise triage proceeds with alert data only.
    enrichment_context = [
        f"{ind.get('type')}={ind.get('value')} (not yet enriched - call /enrichment first for IOC verdicts)"
        for ind in incident.indicators
    ]

    # Phase 4: retrieve the most relevant SOC runbook for this alert type.
    runbook_query = f"{incident.alert_name} {incident.description}"
    runbook_result = retrieve_runbook(runbook_query, top_k=1)
    runbook_excerpt = None
    if runbook_result["found"]:
        top = runbook_result["results"][0]
        runbook_excerpt = f"{format_citation(top)}\n{top['text']}"

    record = run_triage(
        db, incident, enrichment_context=enrichment_context, runbook_excerpt=runbook_excerpt
    )
    return TriageRecordOut.model_validate(record)


@router.get("/incidents/{incident_id}/triage", response_model=list[TriageRecordOut])
def list_triage_history(incident_id: str, db: Session = Depends(get_db)) -> list[TriageRecordOut]:
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")

    records = db.execute(
        select(TriageRecord).where(TriageRecord.incident_id == incident_id).order_by(TriageRecord.created_at.desc())
    ).scalars().all()
    return [TriageRecordOut.model_validate(r) for r in records]
