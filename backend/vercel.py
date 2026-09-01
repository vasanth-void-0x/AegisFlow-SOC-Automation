"""Vercel Services entrypoint for the BlueOrch FastAPI API.

Keep a small diagnostic fallback here: an import-time exception would otherwise
be replaced by Vercel's generic FUNCTION_INVOCATION_FAILED page, which makes a
configuration problem impossible to identify remotely.
"""
import logging

from fastapi import FastAPI

try:
    from app.main import app
except Exception as exc:  # pragma: no cover - only exercised by a broken deployment
    logging.exception("BlueOrch failed during application startup")
    startup_error_type = type(exc).__name__
    startup_error_detail = str(exc)[:300]
    app = FastAPI(title="BlueOrch recovery endpoint")

    @app.get("/api/v1/auth/config")
    def startup_diagnostic() -> dict:
        return {
            "enabled": False,
            "ready": False,
            "error_type": startup_error_type,
            "detail": startup_error_detail,
        }

    @app.get("/api/v1/health")
    def startup_health() -> dict:
        return {"status": "error", "error_type": startup_error_type}

__all__ = ["app"]
