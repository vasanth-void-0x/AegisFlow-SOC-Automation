import base64, hashlib, json
from datetime import datetime, timezone
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.integrations.siem_clients import SiemError, build_client
from app.models.incident import Incident, IncidentStatus, Severity
from app.models.siem_connection import SiemConnection, SiemProvider
from app.schemas.siem import DashboardKpiOut, SiemConnectRequest, SiemSyncOut
from app.services.incident_service import DuplicateAlertError, create_incident_from_alert

settings = get_settings()
def fernet():
    if not settings.siem_encryption_key: raise SiemError("SIEM_ENCRYPTION_KEY is required before saving credentials")
    key = settings.siem_encryption_key.encode()
    try: return Fernet(key)
    except ValueError: return Fernet(base64.urlsafe_b64encode(hashlib.sha256(key).digest()))
def encrypt(data): return fernet().encrypt(json.dumps(data).encode()).decode()
def decrypt(value):
    try: return json.loads(fernet().decrypt(value.encode()).decode())
    except (InvalidToken, ValueError, json.JSONDecodeError) as exc: raise SiemError("Stored SIEM credentials cannot be decrypted") from exc
def credentials(body): return {"token": body.token} if body.provider == SiemProvider.splunk else {"username": body.username, "password": body.password}
def make_client(body): return build_client(body.provider, credentials(body), str(body.base_url).rstrip("/"), body.index_name, body.verify_ssl, settings.siem_request_timeout_seconds)

async def test_request(body): await make_client(body).test()
async def connect(db: Session, body: SiemConnectRequest):
    await test_request(body)
    item = db.execute(select(SiemConnection).where(SiemConnection.provider == body.provider)).scalar_one_or_none()
    if item is None:
        item = SiemConnection(provider=body.provider, base_url=str(body.base_url).rstrip("/"), encrypted_credentials=encrypt(credentials(body))); db.add(item)
    else: item.base_url, item.encrypted_credentials = str(body.base_url).rstrip("/"), encrypt(credentials(body))
    item.index_name, item.verify_ssl, item.enabled, item.connected = body.index_name, body.verify_ssl, True, True
    item.last_error, item.last_checked_at = None, datetime.now(timezone.utc)
    db.commit(); db.refresh(item); return item
async def sync(db: Session, connection):
    now = datetime.now(timezone.utc); created = duplicates = failed = 0
    try:
        client = build_client(connection.provider, decrypt(connection.encrypted_credentials), connection.base_url, connection.index_name, connection.verify_ssl, settings.siem_request_timeout_seconds)
        alerts = await client.fetch_alerts(settings.siem_sync_limit)
        for alert in alerts:
            try: create_incident_from_alert(db, alert); created += 1
            except DuplicateAlertError: duplicates += 1
            except Exception: db.rollback(); failed += 1
        connection.connected, connection.last_error, connection.last_checked_at, connection.last_synced_at = True, None, now, now
        db.commit(); return SiemSyncOut(provider=connection.provider, fetched=len(alerts), created=created, duplicates=duplicates, failed=failed, synced_at=now)
    except SiemError as exc:
        connection.connected, connection.last_error, connection.last_checked_at = False, str(exc), now; db.commit(); raise
def dashboard_kpis(db: Session):
    conn = db.execute(select(SiemConnection).where(SiemConnection.enabled.is_(True)).order_by(SiemConnection.updated_at.desc())).scalars().first()
    def count(*filters): return db.execute(select(func.count()).select_from(Incident).where(*filters)).scalar_one()
    return DashboardKpiOut(connection_status="not_configured" if not conn else ("connected" if conn.connected else "disconnected"), provider=conn.provider if conn else None, last_synced_at=conn.last_synced_at if conn else None, total_alerts=count(), critical_alerts=count(Incident.severity == Severity.critical), high_alerts=count(Incident.severity == Severity.high), active_incidents=count(Incident.status.in_([IncidentStatus.new, IncidentStatus.triaging, IncidentStatus.pending_approval])), contained_threats=count(Incident.status == IncidentStatus.contained))
