"""Structured final reports assembled from incident evidence and audit history."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_viewer
from app.database.session import get_db
from app.services.approval_service import list_proposals
from app.services.incident_service import get_incident
from app.services.timeline_service import get_timeline

router = APIRouter(tags=["reports"], dependencies=[Depends(require_viewer)])


@router.get("/incidents/{incident_id}/report")
def incident_report(incident_id: str, db: Session = Depends(get_db)) -> dict:
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")
    return {
        "report_version": "blueorch-1.0",
        "incident": {
            "id": incident.id, "title": incident.alert_name, "severity": incident.severity.value,
            "status": incident.status.value, "source": incident.source, "event_time": incident.event_time,
            "description": incident.description,
            "assets": {"hostname": incident.hostname, "username": incident.username},
            "network": {"source_ip": incident.source_ip, "destination_ip": incident.destination_ip},
            "indicators": incident.indicators,
        },
        "response_actions": [
            {"id": item.id, "action": item.action_type.value, "target": item.target, "status": item.status.value,
             "approver": item.approver, "result": item.execution_result}
            for item in list_proposals(db, incident_id=incident_id)
        ],
        "timeline": [
            {"time": item.created_at, "type": item.event_type, "description": item.description, "actor": item.actor}
            for item in get_timeline(db, incident_id)
        ],
    }
