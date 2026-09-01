"""Lazy, serverless-safe SQLAlchemy engine and session management."""
from collections.abc import Generator
from functools import lru_cache
from threading import Lock

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create one engine per warm process, never during module import.

    PostgreSQL uses a deliberately small bounded pool: serverless instances can
    scale horizontally, so a large per-process pool can exhaust the provider.
    """
    url = get_settings().database_url
    if url.startswith("sqlite"):
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if url.endswith(":memory:"):
            kwargs["poolclass"] = StaticPool
    else:
        kwargs = {
            "pool_pre_ping": True,
            "pool_size": 1,
            "max_overflow": 2,
            "pool_timeout": 10,
            "pool_recycle": 300,
        }
    return create_engine(url, future=True, **kwargs)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False, future=True)


_schema_lock = Lock()
_schema_initialized = False


def initialize_schema() -> None:
    """Idempotently create missing tables once per warm serverless process."""
    global _schema_initialized
    if _schema_initialized:
        return
    with _schema_lock:
        if not _schema_initialized:
            Base.metadata.create_all(bind=get_engine())
            _schema_initialized = True


def SessionLocal() -> Session:  # noqa: N802 - compatibility with existing callers
    return get_session_factory()()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
