"""Small, dependency-free session authentication and role authorization layer."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import get_settings

COOKIE_NAME = "blueorch_session"
ROLE_RANK = {"viewer": 10, "analyst": 20, "admin": 30}


@dataclass(frozen=True)
class Principal:
    username: str
    role: str
    kind: str = "user"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _secret() -> bytes:
    settings = get_settings()
    if settings.auth_enabled and len(settings.auth_secret) < 32:
        raise HTTPException(status_code=503, detail="Authentication is enabled but AUTH_SECRET is not configured")
    return settings.auth_secret.encode()


def create_session_token(username: str, role: str) -> str:
    settings = get_settings()
    payload = _b64(json.dumps({"sub": username, "role": role, "exp": int(time.time()) + settings.auth_session_hours * 3600}, separators=(",", ":")).encode())
    signature = _b64(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def decode_session_token(token: str) -> Principal | None:
    try:
        payload, signature = token.split(".", 1)
        expected = _b64(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(_unb64(payload))
        if int(data["exp"]) <= int(time.time()) or data["role"] not in ROLE_RANK:
            return None
        return Principal(username=str(data["sub"]), role=str(data["role"]))
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def authenticate(username: str, password: str) -> Principal | None:
    settings = get_settings()
    users = (
        (settings.auth_admin_username, settings.auth_admin_password, "admin"),
        (settings.auth_analyst_username, settings.auth_analyst_password, "analyst"),
        (settings.auth_viewer_username, settings.auth_viewer_password, "viewer"),
    )
    for expected_user, expected_password, role in users:
        if expected_password and hmac.compare_digest(username, expected_user) and hmac.compare_digest(password, expected_password):
            return Principal(username=expected_user, role=role)
    return None


def current_principal(
    request: Request,
    x_blueorch_automation_key: str | None = Header(default=None),
) -> Principal:
    settings = get_settings()
    if not settings.auth_enabled:
        return Principal(username="local-admin", role="admin")
    if settings.automation_api_key and x_blueorch_automation_key and hmac.compare_digest(x_blueorch_automation_key, settings.automation_api_key):
        return Principal(username="n8n-automation", role="analyst", kind="service")
    token = request.cookies.get(COOKIE_NAME)
    principal = decode_session_token(token) if token else None
    if principal is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return principal


def require_role(minimum_role: str) -> Callable:
    def dependency(principal: Principal = Depends(current_principal)) -> Principal:
        if ROLE_RANK[principal.role] < ROLE_RANK[minimum_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{minimum_role.title()} role required")
        return principal
    return dependency


require_viewer = require_role("viewer")
require_analyst = require_role("analyst")
require_admin = require_role("admin")
