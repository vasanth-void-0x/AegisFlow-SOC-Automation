from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.deps import require_admin, require_operator
from app.models.user import User
from app.integrations.siem_clients import SiemError
from app.models.siem_connection import SiemConnection, SiemProvider
from app.schemas.siem import DashboardKpiOut, SiemConnectionOut, SiemConnectRequest, SiemSyncOut, SiemTestOut
from app.services.siem_service import connect, dashboard_kpis, sync, test_request

router = APIRouter(tags=["siem"])

@router.post("/siem/test", response_model=SiemTestOut)
async def test_siem(body: SiemConnectRequest, _: User = Depends(require_admin)):
    try: await test_request(body)
    except SiemError as exc: raise HTTPException(status_code=502, detail=str(exc)) from exc
    return SiemTestOut(provider=body.provider, connected=True, message=f"{body.provider.value.title()} connection successful")

@router.post("/siem/connect", response_model=SiemConnectionOut)
async def connect_siem(body: SiemConnectRequest, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    try:
        item = await connect(db, body)
        # A successful connection must immediately populate the real dashboard.
        # Later syncs remain available through /siem/{provider}/sync.
        await sync(db, item)
        db.refresh(item)
        return SiemConnectionOut.model_validate(item)
    except SiemError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

@router.get("/siem/status", response_model=list[SiemConnectionOut])
def status(db: Session = Depends(get_db)):
    return [SiemConnectionOut.model_validate(x) for x in db.execute(select(SiemConnection).order_by(SiemConnection.updated_at.desc())).scalars()]

@router.post("/siem/{provider}/sync", response_model=SiemSyncOut)
async def sync_siem(provider: SiemProvider, db: Session = Depends(get_db), _: User = Depends(require_operator)):
    item = db.execute(select(SiemConnection).where(SiemConnection.provider == provider, SiemConnection.enabled.is_(True))).scalar_one_or_none()
    if not item: raise HTTPException(status_code=404, detail=f"{provider.value.title()} is not connected")
    try: return await sync(db, item)
    except SiemError as exc: raise HTTPException(status_code=502, detail=str(exc)) from exc

@router.delete("/siem/{provider}", status_code=204)
def disconnect(provider: SiemProvider, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    item = db.execute(select(SiemConnection).where(SiemConnection.provider == provider)).scalar_one_or_none()
    if not item: raise HTTPException(status_code=404, detail="SIEM connection not found")
    db.delete(item); db.commit()

@router.get("/dashboard/kpis", response_model=DashboardKpiOut)
def kpis(db: Session = Depends(get_db)): return dashboard_kpis(db)
