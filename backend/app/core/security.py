"""JWT, password, and token utilities.

JWT hardening (Phase 12):
- jti  — unique JWT ID (token-level identity for future blocklist support)
- iss  — issuer claim (APP_NAME)
- aud  — audience claim (JWT_AUDIENCE)
Both iss and aud are validated on decode.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError
from jose import jwt

from app.core.config import settings

REFRESH_TOKEN_BYTES = 64
MAX_BCRYPT_PASSWORD_BYTES = 72


class TokenDecodeError(ValueError):
    """Raised when a JWT cannot be decoded or is the wrong token type."""


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": now,
        "nbf": now,
        "type": "access",
        "jti": secrets.token_urlsafe(16),
        "iss": settings.APP_NAME,
        "aud": settings.JWT_AUDIENCE,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.APP_NAME,
        )
    except JWTError as exc:
        raise TokenDecodeError("Could not validate credentials.") from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise TokenDecodeError("Unexpected token type.")
    if not payload.get("sub"):
        raise TokenDecodeError("Token subject is missing.")

    return payload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (TypeError, ValueError):
        return False


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def password_validation_errors(password: str) -> list[str]:
    errors: list[str] = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if len(password.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
        errors.append("Password must be 72 bytes or fewer for bcrypt.")
    if not any(char.islower() for char in password):
        errors.append("Password must include a lowercase letter.")
    if not any(char.isupper() for char in password):
        errors.append("Password must include an uppercase letter.")
    if not any(char.isdigit() for char in password):
        errors.append("Password must include a number.")
    if not any(not char.isalnum() for char in password):
        errors.append("Password must include a symbol.")
    return errors


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(REFRESH_TOKEN_BYTES)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
