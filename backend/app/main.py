"""BlueOrch FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.approvals import router as approvals_router
from app.api.audit import router as audit_router
from app.api.enrichment import router as enrichment_router
from app.api.direct_logs import router as direct_logs_router
from app.api.health import router as health_router
from app.api.incidents import router as incidents_router
from app.api.runbooks import router as runbooks_router
from app.api.triage import router as triage_router
from app.api.siem import router as siem_router
from app.api.reports import router as reports_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import RateLimitMiddleware
from app.database.session import Base, engine
import app.models  # noqa: F401 - ensures all ORM models are registered on Base.metadata

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bootstrap the schema for both local SQLite and managed PostgreSQL.
    # SQLAlchemy emits idempotent CREATE TABLE statements for missing tables.
    Base.metadata.create_all(bind=engine)
    logger.info("BlueOrch started | demo_mode=%s | env=%s", settings.demo_mode, settings.environment)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Agentic AI SOC Investigation & Response Orchestrator",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)

    @app.middleware("http")
    async def limit_body_size(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_body_bytes:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request body too large"},
            )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": jsonable_encoder(exc.errors()), "error_code": "VALIDATION_ERROR"},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )

    app.include_router(health_router)
    app.include_router(incidents_router, prefix="/api/v1")
    app.include_router(enrichment_router, prefix="/api/v1")
    app.include_router(triage_router, prefix="/api/v1")
    app.include_router(runbooks_router, prefix="/api/v1")
    app.include_router(approvals_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")
    app.include_router(siem_router, prefix="/api/v1")
    app.include_router(direct_logs_router, prefix="/api/v1")
    app.include_router(reports_router, prefix="/api/v1")

    return app


app = create_app()
