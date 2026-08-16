"""Phase 1 API: alert ingestion and incident retrieval."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.incident import IncidentStatus, Severity
from app.schemas.incident import AlertIngest, IncidentListOut, IncidentOut
from app.services.incident_service import (
    DuplicateAlertError,
    create_incident_from_alert,
    get_incident,
    list_incidents,
    update_incident_status,
)

router = APIRouter(tags=["incidents"])


class UpdateStatusRequest(BaseModel):
    status: IncidentStatus


@router.post(
    "/alerts",
    response_model=IncidentOut,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Duplicate alert"}, 422: {"description": "Validation error"}},
)
def ingest_alert(alert: AlertIngest, response: Response, db: Session = Depends(get_db)) -> IncidentOut:
    """Ingest a new security alert and create an incident record."""
    try:
        incident = create_incident_from_alert(db, alert)
    except DuplicateAlertError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate alert. Existing incident: {exc.existing_incident.id}",
            headers={"X-Existing-Incident-Id": exc.existing_incident.id},
        ) from exc
    return IncidentOut.model_validate(incident)


@router.get("/incidents", response_model=IncidentListOut)
def get_incidents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    severity: Severity | None = Query(default=None),
    status_filter: IncidentStatus | None = Query(default=None, alias="status"),
    source: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> IncidentListOut:
    """List incidents with pagination and optional filters."""
    items, total = list_incidents(
        db,
        page=page,
        page_size=page_size,
        severity=severity.value if severity else None,
        status=status_filter.value if status_filter else None,
        source=source,
    )
    return IncidentListOut(
        items=[IncidentOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentOut,
    responses={404: {"description": "Incident not found"}},
)
def get_incident_by_id(incident_id: str, db: Session = Depends(get_db)) -> IncidentOut:
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")
    return IncidentOut.model_validate(incident)


@router.patch(
    "/incidents/{incident_id}/status",
    response_model=IncidentOut,
    responses={404: {"description": "Incident not found"}},
)
def patch_incident_status(incident_id: str, body: UpdateStatusRequest, db: Session = Depends(get_db)) -> IncidentOut:
    """Update an incident's status. Used by the n8n orchestration workflow."""
    incident = update_incident_status(db, incident_id, body.status.value)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")
    return IncidentOut.model_validate(incident)
