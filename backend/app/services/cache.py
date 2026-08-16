"""Minimal in-memory TTL cache (per-process). Good enough for an 8GB dev box.

For multi-worker/production deployment this should be swapped for Redis -
the interface is intentionally tiny so that's a drop-in replacement later.
"""
import time
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time() + self.ttl_seconds, value)

    def clear(self) -> None:
        self._store.clear()


_enrichment_cache: TTLCache | None = None


def get_enrichment_cache() -> TTLCache:
    global _enrichment_cache
    if _enrichment_cache is None:
        from app.core.config import get_settings

        _enrichment_cache = TTLCache(ttl_seconds=get_settings().enrichment_cache_ttl_seconds)
    return _enrichment_cache
