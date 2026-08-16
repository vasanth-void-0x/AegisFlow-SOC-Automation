"""Append-only incident timeline / audit trail service."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.timeline import TimelineEvent


def add_event(
    db: Session,
    incident_id: str,
    event_type: str,
    description: str,
    actor: str = "system",
    metadata: dict | None = None,
) -> TimelineEvent:
    event = TimelineEvent(
        incident_id=incident_id,
        event_type=event_type,
        description=description,
        actor=actor,
        event_metadata=metadata or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_timeline(db: Session, incident_id: str) -> list[TimelineEvent]:
    return list(
        db.execute(
            select(TimelineEvent).where(TimelineEvent.incident_id == incident_id).order_by(TimelineEvent.created_at.asc())
        ).scalars().all()
    )
