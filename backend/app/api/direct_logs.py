"""Continuous direct-log ingestion and endpoint-agent lifecycle APIs."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import get_db
from app.models.log_agent import LogAgent
from app.schemas.direct_log import (
    AgentHeartbeatIn, AgentRegisterIn, AgentRegisteredOut, AgentStatusOut,
    DirectLogBatchIn, DirectLogBatchOut, DirectLogIn,
)
from app.schemas.incident import IncidentOut
from app.services.direct_log_service import normalize_direct_log
from app.services.incident_service import DuplicateAlertError, create_incident_from_alert

router = APIRouter(tags=["direct-logs"])


def _key_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_registration_token(x_blueorch_registration_token: str | None = Header(default=None)) -> None:
    expected = get_settings().direct_log_registration_token
    if not expected:
        raise HTTPException(status_code=503, detail="DIRECT_LOG_REGISTRATION_TOKEN is not configured")
    if not x_blueorch_registration_token or not hmac.compare_digest(x_blueorch_registration_token, expected):
        raise HTTPException(status_code=401, detail="Invalid registration token")


def get_agent(x_blueorch_agent_key: str | None = Header(default=None), db: Session = Depends(get_db)) -> LogAgent:
    if not x_blueorch_agent_key:
        raise HTTPException(status_code=401, detail="Missing agent API key")
    agent = db.query(LogAgent).filter(LogAgent.key_hash == _key_hash(x_blueorch_agent_key)).first()
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid agent API key")
    return agent


def _agent_status(agent: LogAgent) -> AgentStatusOut:
    last_seen = agent.last_seen_at
    if last_seen and last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    online = bool(last_seen and last_seen >= datetime.now(timezone.utc) - timedelta(minutes=3))
    return AgentStatusOut(
        id=agent.id, name=agent.name, platform=agent.platform, profile=agent.profile,
        hostname=agent.hostname, agent_version=agent.agent_version,
        status="online" if online else "offline", last_seen_at=last_seen,
        events_received=agent.events_received, created_at=agent.created_at,
    )


@router.post("/agents/register", response_model=AgentRegisteredOut, status_code=201, dependencies=[Depends(verify_registration_token)])
def register_agent(body: AgentRegisterIn, db: Session = Depends(get_db)) -> AgentRegisteredOut:
    if db.query(LogAgent).filter(LogAgent.name == body.name).first():
        raise HTTPException(status_code=409, detail="An agent with this name already exists")
    api_key = f"boa_{secrets.token_urlsafe(32)}"
    agent = LogAgent(name=body.name, platform=body.platform, profile=body.profile, key_hash=_key_hash(api_key))
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return AgentRegisteredOut(id=agent.id, name=agent.name, platform=agent.platform, profile=agent.profile, api_key=api_key)


@router.get("/agents", response_model=list[AgentStatusOut], dependencies=[Depends(verify_registration_token)])
def list_agents(db: Session = Depends(get_db)) -> list[AgentStatusOut]:
    return [_agent_status(item) for item in db.query(LogAgent).order_by(LogAgent.created_at.desc()).all()]


@router.post("/agents/heartbeat", response_model=AgentStatusOut)
def agent_heartbeat(body: AgentHeartbeatIn, request: Request, agent: LogAgent = Depends(get_agent), db: Session = Depends(get_db)) -> AgentStatusOut:
    agent.hostname = body.hostname
    agent.agent_version = body.agent_version
    agent.last_ip = request.client.host if request.client else None
    agent.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(agent)
    return _agent_status(agent)


@router.post("/agents/logs/bulk", response_model=DirectLogBatchOut)
def ingest_agent_batch(body: DirectLogBatchIn, agent: LogAgent = Depends(get_agent), db: Session = Depends(get_db)) -> DirectLogBatchOut:
    incidents, duplicates = [], 0
    for log in body.logs:
        log.source_type = "agent"
        log.source_name = agent.name
        try:
            incidents.append(create_incident_from_alert(db, normalize_direct_log(log)))
        except DuplicateAlertError:
            duplicates += 1
    agent.last_seen_at = datetime.now(timezone.utc)
    agent.events_received += len(body.logs)
    db.commit()
    return DirectLogBatchOut(accepted=len(incidents), duplicates=duplicates, incidents=[IncidentOut.model_validate(item) for item in incidents])


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
