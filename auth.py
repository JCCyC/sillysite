import hashlib
import hmac
import secrets
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

import config
import models
from database import get_db

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16
CHALLENGE_BYTES = 32
TOKEN_BYTES = 32
DEFAULT_LOGIN_TIMEOUT_SECONDS = 60
DEFAULT_SESSION_TTL_SECONDS = 3600

ADMIN_USER_ID = 0
ADMIN_USERNAME = "admin"


def hash_password(password: str) -> tuple[str, str, int]:
    """Returns (salt_hex, hash_hex, iterations) for a new password."""
    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PBKDF2_ITERATIONS, dklen=32
    )
    return salt.hex(), derived.hex(), PBKDF2_ITERATIONS


def generate_challenge() -> str:
    return secrets.token_hex(CHALLENGE_BYTES)


def generate_token() -> str:
    return secrets.token_hex(TOKEN_BYTES)


def compute_challenge_response(password_hash_hex: str, challenge_hex: str) -> str:
    key = bytes.fromhex(password_hash_hex)
    message = bytes.fromhex(challenge_hex)
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def get_current_user(
    request: Request,
    api_key: str | None = Security(api_key_header),
    db: Session = Depends(get_db),
) -> models.User | None:
    """Resolves the caller's user, or None if unauthenticated."""
    if api_key is None:
        return None

    if config.API_KEY and secrets.compare_digest(api_key, config.API_KEY):
        return db.get(models.User, ADMIN_USER_ID)

    session = db.query(models.UserSession).filter(models.UserSession.token == api_key).first()
    if session is None:
        return None

    now = datetime.now(timezone.utc)
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        return None

    if client_ip(request) != session.source_ip:
        return None

    return session.user


def require_user(user: models.User | None = Depends(get_current_user)) -> models.User:
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return user


def require_admin(user: models.User = Depends(require_user)) -> models.User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
