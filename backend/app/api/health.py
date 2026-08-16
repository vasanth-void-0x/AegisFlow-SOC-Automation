"""Health check endpoint used by Docker/orchestration and monitoring."""
from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.database.session import SessionLocal

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    settings = get_settings()
    db_status = "ok"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as exc:  # noqa: BLE001 - health check must never crash
        db_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "demo_mode": settings.demo_mode,
        "database": db_status,
    }
