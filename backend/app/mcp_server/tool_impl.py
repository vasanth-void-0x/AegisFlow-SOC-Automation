"""
Implementations for the 7 MCP security tools.

Design principles enforced here:
- No unrestricted shell execution anywhere in this module.
- No tool directly performs a destructive response action - the only
  response-related tool is create_response_proposal, which creates a
  PENDING record that still requires human approval via the Phase 7 API.
- Every DB session is scoped per-call and closed.
"""
from app.database.session import SessionLocal
from app.mcp_server import schemas
from app.models.incident import IncidentStatus, Severity
from app.models.response_proposal import ActionType, ResponseProposal
from app.rag.retriever import format_citation, retrieve_runbook
from app.services import enrichment_service, incident_service
from app.services.mitre_mapping import map_alert_to_techniques


async def check_ip_reputation(args: schemas.CheckIpReputationInput) -> dict:
    result = await enrichment_service.enrich_ip(args.ip)
    return result.model_dump(mode="json")


async def check_file_hash(args: schemas.CheckFileHashInput) -> dict:
    result = await enrichment_service.enrich_hash(args.file_hash)
    return result.model_dump(mode="json")


def search_incidents(args: schemas.SearchIncidentsInput) -> dict:
    db = SessionLocal()
    try:
        severity = args.severity.lower() if args.severity else None
        status = args.status.lower() if args.status else None

        if severity and severity not in {s.value for s in Severity}:
            raise ValueError(f"Invalid severity: {args.severity}")
        if status and status not in {s.value for s in IncidentStatus}:
            raise ValueError(f"Invalid status: {args.status}")

        items, total = incident_service.list_incidents(
            db, page=args.page, page_size=args.page_size, severity=severity, status=status
        )
        return {
            "total": total,
            "page": args.page,
            "page_size": args.page_size,
            "incidents": [
                {
                    "id": i.id,
                    "alert_name": i.alert_name,
                    "severity": i.severity.value,
                    "status": i.status.value,
                    "source": i.source,
                    "created_at": i.created_at.isoformat(),
                }
                for i in items
            ],
        }
    finally:
        db.close()


def get_incident(args: schemas.GetIncidentInput) -> dict:
    db = SessionLocal()
    try:
        incident = incident_service.get_incident(db, args.incident_id)
        if incident is None:
            raise ValueError(f"Incident {args.incident_id} not found")
        return {
            "id": incident.id,
            "source": incident.source,
            "alert_name": incident.alert_name,
            "severity": incident.severity.value,
            "status": incident.status.value,
            "description": incident.description,
            "source_ip": incident.source_ip,
            "destination_ip": incident.destination_ip,
            "hostname": incident.hostname,
            "username": incident.username,
            "event_time": incident.event_time.isoformat(),
            "indicators": incident.indicators,
            "created_at": incident.created_at.isoformat(),
        }
    finally:
        db.close()


def map_mitre_technique(args: schemas.MapMitreTechniqueInput) -> dict:
    techniques = map_alert_to_techniques(args.alert_text)
    return {
        "techniques": [
            {"technique_id": t.technique_id, "name": t.name, "tactic": t.tactic} for t in techniques
        ]
    }


def get_soc_runbook(args: schemas.GetSocRunbookInput) -> dict:
    result = retrieve_runbook(args.query, top_k=3)
    if not result["found"]:
        return {"found": False, "message": "No relevant runbook found", "results": []}
    return {
        "found": True,
        "provider": result["provider"],
        "results": [
            {
                "title": r["metadata"]["title"],
                "heading": r["metadata"]["heading"],
                "text": r["text"],
                "citation": format_citation(r),
                "score": r["score"],
            }
            for r in result["results"]
        ],
    }


def create_response_proposal(args: schemas.CreateResponseProposalInput) -> dict:
    from datetime import datetime, timedelta, timezone

    from app.core.config import get_settings
    from app.services.timeline_service import add_event

    db = SessionLocal()
    try:
        incident = incident_service.get_incident(db, args.incident_id)
        if incident is None:
            raise ValueError(f"Incident {args.incident_id} not found")

        if args.action_type not in {a.value for a in ActionType}:
            raise ValueError(f"Invalid action_type: {args.action_type}. Must be one of {[a.value for a in ActionType]}")

        settings = get_settings()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.approval_expiry_minutes)

        proposal = ResponseProposal(
            incident_id=args.incident_id,
            action_type=ActionType(args.action_type),
            target=args.target,
            justification=args.justification,
            proposed_by=args.proposed_by,
            expires_at=expires_at,
        )
        db.add(proposal)
        db.commit()
        db.refresh(proposal)

        add_event(
            db,
            incident.id,
            event_type="response_proposal_created",
            description=f"Response proposal created: {proposal.action_type.value} on {proposal.target}",
            actor=args.proposed_by,
            metadata={"proposal_id": proposal.id},
        )

        return {
            "id": proposal.id,
            "incident_id": proposal.incident_id,
            "action_type": proposal.action_type.value,
            "target": proposal.target,
            "status": proposal.status.value,
            "expires_at": proposal.expires_at.isoformat() if proposal.expires_at else None,
            "note": "Proposal created with status=pending. It requires human approval "
            "via the /approvals API before any action executes - no MCP tool can approve it.",
        }
    finally:
        db.close()
