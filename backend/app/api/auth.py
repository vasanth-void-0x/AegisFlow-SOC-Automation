from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.core.auth import COOKIE_NAME, Principal, authenticate, create_session_token, current_principal
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


def _out(principal: Principal) -> dict:
    return {"username": principal.username, "role": principal.role, "kind": principal.kind}


@router.get("/config")
def auth_config() -> dict:
    return {"enabled": get_settings().auth_enabled}


@router.post("/login")
def login(body: LoginRequest, response: Response) -> dict:
    principal = authenticate(body.username, body.password)
    if principal is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    settings = get_settings()
    response.set_cookie(COOKIE_NAME, create_session_token(principal.username, principal.role), max_age=settings.auth_session_hours * 3600, httponly=True, secure=settings.environment == "production", samesite="strict", path="/")
    return _out(principal)


@router.get("/me")
def me(principal: Principal = Depends(current_principal)) -> dict:
    return _out(principal)


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")
