import hashlib
import hmac
import secrets
import base64
import json
import time
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings

COOKIE_NAME = "blueorch_session"


def validate_auth_configuration() -> None:
    settings = get_settings()
    if settings.auth_enabled and settings.environment == "production" and len(settings.auth_secret) < 32:
        raise RuntimeError("AUTH_SECRET must contain at least 32 characters when AUTH_ENABLED=true in production")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1).hex()
    return f"scrypt${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt, expected = encoded.split("$", 2)
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_session_token(user_id: str, role: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": user_id, "role": role, "iss": "blueorch", "aud": "blueorch-web", "iat": int(now.timestamp()), "nbf": int(now.timestamp()), "exp": int((now + timedelta(minutes=settings.auth_session_minutes)).timestamp()), "jti": secrets.token_hex(16)}
    encoded = f"{_b64(json.dumps(header,separators=(',',':')).encode())}.{_b64(json.dumps(payload,separators=(',',':')).encode())}"
    signature = hmac.new(settings.auth_secret.encode(), encoded.encode(), hashlib.sha256).digest()
    return f"{encoded}.{_b64(signature)}"


def decode_session_token(token: str) -> dict | None:
    try:
        header_raw, payload_raw, signature = token.split(".")
        encoded = f"{header_raw}.{payload_raw}"
        expected = _b64(hmac.new(get_settings().auth_secret.encode(), encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected): return None
        header = json.loads(_unb64(header_raw)); payload = json.loads(_unb64(payload_raw))
        now = int(time.time())
        if header != {"alg":"HS256","typ":"JWT"} or payload.get("iss") != "blueorch" or payload.get("aud") != "blueorch-web" or int(payload.get("nbf", now + 1)) > now or int(payload.get("exp", 0)) <= now: return None
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
