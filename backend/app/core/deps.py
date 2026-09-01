import hmac
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import COOKIE_NAME, decode_session_token
from app.database.session import get_db
from app.models.user import User, UserRole


def get_current_user(session: str | None = Cookie(default=None, alias=COOKIE_NAME), db: Session = Depends(get_db)) -> User:
    if not get_settings().auth_enabled:
        return User(id="AUTH-DISABLED", username="local", display_name="Local Operator", password_hash="", role=UserRole.admin, is_active=True)
    payload = decode_session_token(session or "")
    user = db.get(User, payload.get("sub")) if payload else None
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def require_roles(*roles: UserRole):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return dependency


require_operator = require_roles(UserRole.admin, UserRole.analyst)
require_admin = require_roles(UserRole.admin)


def resolve_operator_or_mcp(
    *,
    session: str | None,
    mcp_key: str | None,
    db: Session,
) -> User:
    """Resolve a human operator or the scoped n8n/MCP service identity."""
    settings = get_settings()
    if (
        settings.mcp_gateway_api_key
        and mcp_key
        and hmac.compare_digest(mcp_key, settings.mcp_gateway_api_key)
    ):
        return User(id="MCP-SERVICE", username="n8n_mcp", display_name="n8n MCP", password_hash="", role=UserRole.analyst, is_active=True)
    user = get_current_user(session=session, db=db)
    if user.role not in (UserRole.admin, UserRole.analyst):
        raise HTTPException(status_code=403, detail="Insufficient role")
    return user


def require_operator_or_mcp(
    session: str | None = Cookie(default=None, alias=COOKIE_NAME),
    x_blueorch_mcp_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Allow a human operator session or the scoped n8n/MCP service key."""
    return resolve_operator_or_mcp(session=session, mcp_key=x_blueorch_mcp_key, db=db)
