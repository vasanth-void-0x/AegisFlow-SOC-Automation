"""Continuous direct-log ingestion for agents, webhooks, syslog relays, and files."""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import get_db
from app.schemas.direct_log import DirectLogBatchIn, DirectLogBatchOut, DirectLogIn
from app.schemas.incident import IncidentOut
from app.services.direct_log_service import normalize_direct_log
from app.services.incident_service import DuplicateAlertError, create_incident_from_alert

router = APIRouter(tags=["direct-logs"])


def verify_collector_key(x_blueorch_key: str | None = Header(default=None)) -> None:
    expected = get_settings().direct_log_api_key
    if expected and x_blueorch_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid collector API key")


def _create(body: DirectLogIn, db: Session) -> IncidentOut:
    try:
        incident = create_incident_from_alert(db, normalize_direct_log(body))
    except DuplicateAlertError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate log. Existing incident: {exc.existing_incident.id}",
            headers={"X-Existing-Incident-Id": exc.existing_incident.id},
        ) from exc
    return IncidentOut.model_validate(incident)


@router.post("/logs/ingest", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def ingest_direct_log(body: DirectLogIn, _: None = Depends(verify_collector_key), db: Session = Depends(get_db)) -> IncidentOut:
    return _create(body, db)


@router.post("/webhooks/logs", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def ingest_webhook_log(body: DirectLogIn, _: None = Depends(verify_collector_key), db: Session = Depends(get_db)) -> IncidentOut:
    return _create(body, db)


@router.post("/logs/bulk", response_model=DirectLogBatchOut)
def ingest_direct_log_batch(body: DirectLogBatchIn, _: None = Depends(verify_collector_key), db: Session = Depends(get_db)) -> DirectLogBatchOut:
    incidents = []
    duplicates = 0
    for log in body.logs:
        try:
            incidents.append(create_incident_from_alert(db, normalize_direct_log(log)))
        except DuplicateAlertError:
            duplicates += 1
    return DirectLogBatchOut(
        accepted=len(incidents),
        duplicates=duplicates,
        incidents=[IncidentOut.model_validate(item) for item in incidents],
    )
