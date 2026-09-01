"""Phase 2 API: IOC enrichment."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_viewer
from app.database.session import get_db
from app.schemas.enrichment import EnrichmentResult
from app.services import ioc_utils
from app.services.enrichment_service import attach_mitre_techniques, enrich_indicator
from app.services.incident_service import get_incident

router = APIRouter(tags=["enrichment"], dependencies=[Depends(require_viewer)])


@router.get("/enrich", response_model=EnrichmentResult)
async def enrich_single_indicator(indicator_type: str, value: str) -> EnrichmentResult:
    """Enrich a single ad-hoc indicator (not tied to an incident)."""
    try:
        ioc_utils.normalize_indicator_type(indicator_type, value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    try:
        return await enrich_indicator(indicator_type, value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/incidents/{incident_id}/enrichment", response_model=list[EnrichmentResult])
async def enrich_incident_indicators(incident_id: str, db: Session = Depends(get_db)) -> list[EnrichmentResult]:
    """Enrich every indicator attached to a given incident."""
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")

    results = []
    for indicator in incident.indicators:
        try:
            result = await enrich_indicator(indicator["type"], indicator["value"])
            attach_mitre_techniques(result, incident.alert_name, incident.description)
            results.append(result)
        except ValueError as exc:
            results.append(
                EnrichmentResult(
                    indicator_type=indicator.get("type", "unknown"),
                    value=indicator.get("value", ""),
                    source="demo",
                    provider="error",
                    error=str(exc),
                )
            )
    return results
