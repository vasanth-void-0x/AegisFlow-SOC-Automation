"""Business logic for creating and retrieving incidents from alerts."""
import hashlib

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.incident import Incident
from app.schemas.incident import AlertIngest

logger = get_logger(__name__)


class DuplicateAlertError(Exception):
    """Raised when an alert with the same fingerprint already exists."""

    def __init__(self, existing_incident: Incident):
        self.existing_incident = existing_incident
        super().__init__(f"Duplicate alert, existing incident: {existing_incident.id}")


def compute_fingerprint(alert: AlertIngest) -> str:
    """
    Derive a stable fingerprint for de-duplication.

    Uses the client-supplied idempotency_key if present, otherwise derives
    one from the identifying fields of the alert. This means the *same*
    underlying event (e.g. re-delivered webhook) maps to the same incident.
    """
    if alert.idempotency_key:
        basis = f"idem:{alert.idempotency_key}"
    else:
        basis = "|".join(
            [
                alert.source,
                alert.alert_name,
                alert.source_ip or "",
                alert.destination_ip or "",
                alert.hostname or "",
                alert.username or "",
                alert.event_time.isoformat(),
            ]
        )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def create_incident_from_alert(db: Session, alert: AlertIngest) -> Incident:
    """
    Create a new incident from an ingested alert.

    Raises DuplicateAlertError if an incident with the same fingerprint
    already exists (idempotent ingestion / dedup protection).
    """
    fingerprint = compute_fingerprint(alert)

    existing = db.execute(
        select(Incident).where(Incident.fingerprint == fingerprint)
    ).scalar_one_or_none()
    if existing is not None:
        logger.info("Duplicate alert rejected, fingerprint=%s incident=%s", fingerprint, existing.id)
        raise DuplicateAlertError(existing)

    incident = Incident(
        fingerprint=fingerprint,
        source=alert.source,
        alert_name=alert.alert_name,
        severity=alert.severity,
        description=alert.description,
        source_ip=alert.source_ip,
        destination_ip=alert.destination_ip,
        hostname=alert.hostname,
        username=alert.username,
        event_time=alert.event_time,
        raw_event=alert.raw_event,
        indicators=[ind.model_dump() for ind in alert.indicators],
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    logger.info("Incident created id=%s severity=%s source=%s", incident.id, incident.severity, incident.source)

    from app.services.timeline_service import add_event

    add_event(
        db,
        incident.id,
        event_type="incident_created",
        description=f"Incident created from alert '{alert.alert_name}' (source: {alert.source})",
        actor=alert.source,
    )
    return incident


def get_incident(db: Session, incident_id: str) -> Incident | None:
    return db.execute(select(Incident).where(Incident.id == incident_id)).scalar_one_or_none()


def update_incident_status(db: Session, incident_id: str, new_status: str) -> Incident | None:
    incident = get_incident(db, incident_id)
    if incident is None:
        return None
    incident.status = new_status
    db.commit()
    db.refresh(incident)

    from app.services.timeline_service import add_event

    add_event(
        db,
        incident.id,
        event_type="status_changed",
        description=f"Incident status changed to '{new_status}'",
        actor="n8n_workflow",
    )
    return incident


def list_incidents(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    severity: str | None = None,
    minimum_severity: str | None = None,
    status: str | None = None,
    source: str | None = None,
) -> tuple[list[Incident], int]:
    query = select(Incident)
    count_query = select(func.count()).select_from(Incident)

    if severity:
        query = query.where(Incident.severity == severity)
        count_query = count_query.where(Incident.severity == severity)
    if minimum_severity:
        ranks = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        allowed = [name for name, rank in ranks.items() if rank >= ranks[minimum_severity]]
        query = query.where(Incident.severity.in_(allowed))
        count_query = count_query.where(Incident.severity.in_(allowed))
    if status:
        query = query.where(Incident.status == status)
        count_query = count_query.where(Incident.status == status)
    if source:
        query = query.where(Incident.source == source)
        count_query = count_query.where(Incident.source == source)

    total = db.execute(count_query).scalar_one()

    query = query.order_by(Incident.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list(db.execute(query).scalars().all())

    return items, total
