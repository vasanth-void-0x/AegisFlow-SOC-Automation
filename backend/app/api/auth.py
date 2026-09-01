import hmac
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user, require_admin
from app.core.security import COOKIE_NAME, create_session_token, hash_password, verify_password
from app.database.session import get_db
from app.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=12, max_length=128)


class BootstrapRequest(Credentials):
    setup_token: str = Field(min_length=16)
    display_name: str = Field(min_length=1, max_length=128)


class CreateUserRequest(Credentials):
    display_name: str = Field(min_length=1, max_length=128)
    role: UserRole


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    display_name: str
    role: UserRole
    is_active: bool


def set_cookie(response: Response, user: User) -> None:
    settings = get_settings()
    response.set_cookie(COOKIE_NAME, create_session_token(user.id, user.role.value), httponly=True, secure=settings.environment == "production", samesite="strict", path="/", max_age=settings.auth_session_minutes * 60)


@router.get("/config")
def auth_config(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    initialized = db.execute(select(User.id).limit(1)).first() is not None if settings.auth_enabled else True
    return {"enabled": settings.auth_enabled, "initialized": initialized}


@router.post("/bootstrap", response_model=UserOut, status_code=201)
def bootstrap(body: BootstrapRequest, response: Response, db: Session = Depends(get_db)) -> UserOut:
    settings = get_settings()
    if not settings.auth_enabled or not settings.auth_bootstrap_token or not hmac.compare_digest(body.setup_token, settings.auth_bootstrap_token):
        raise HTTPException(status_code=403, detail="Invalid bootstrap token")
    if db.execute(select(User.id).limit(1)).first():
        raise HTTPException(status_code=409, detail="Authentication is already initialized")
    user = User(username=body.username.lower(), display_name=body.display_name, password_hash=hash_password(body.password), role=UserRole.admin)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Authentication is already initialized") from exc
    db.refresh(user); set_cookie(response, user)
    return UserOut.model_validate(user)


@router.post("/login", response_model=UserOut)
def login(body: Credentials, response: Response, db: Session = Depends(get_db)) -> UserOut:
    if not get_settings().auth_enabled:
        raise HTTPException(status_code=409, detail="Authentication is disabled")
    user = db.execute(select(User).where(User.username == body.username.lower())).scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    user.last_login_at = datetime.now(timezone.utc); db.commit(); set_cookie(response, user)
    return UserOut.model_validate(user)


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(body: CreateUserRequest, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> UserOut:
    user = User(username=body.username.lower(), display_name=body.display_name, password_hash=hash_password(body.password), role=body.role)
    db.add(user)
    try: db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Username already exists") from exc
    db.refresh(user); return UserOut.model_validate(user)
