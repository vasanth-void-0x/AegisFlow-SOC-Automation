"""Structured JSON-ish logging configuration for BlueOrch."""
import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    log_format = (
        '{"time":"%(asctime)s","level":"%(levelname)s",'
        '"logger":"%(name)s","message":"%(message)s"}'
    )
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format=log_format,
        stream=sys.stdout,
    )
    # Quiet down noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
