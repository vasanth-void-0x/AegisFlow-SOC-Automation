"""
Minimal in-memory sliding-window rate limiter, keyed by client IP.

This is process-local (fine for the single-process dev/demo deployment this
project targets). For multi-worker production use, swap for a Redis-backed
limiter - the interface below is intentionally tiny to make that easy.
"""
import time
from collections import defaultdict, deque

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        limit = settings.rate_limit_per_minute
        if limit <= 0:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = self._hits[client_ip]

        # Drop hits older than 60s
        while window and now - window[0] > 60:
            window.popleft()

        if len(window) >= limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again shortly.", "error_code": "RATE_LIMITED"},
            )

        window.append(now)
        return await call_next(request)
