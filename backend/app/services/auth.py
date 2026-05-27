from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User, UserType
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository


class AuthServiceError(Exception):
    """Base class for auth service errors."""


class EmailAlreadyRegisteredError(AuthServiceError):
    """Raised when registering with an email that already exists."""


class InvalidCredentialsError(AuthServiceError):
    """Raised when login credentials are invalid."""


class InactiveUserError(AuthServiceError):
    """Raised when an inactive account attempts to authenticate."""


class InvalidRefreshTokenError(AuthServiceError):
    """Raised when a refresh token is missing, expired, or revoked."""


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


@dataclass(frozen=True)
class AuthResult:
    user: User
    tokens: TokenPair


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    def register(
        self,
        *,
        email: str,
        password: str,
        display_name: str,
        user_type: UserType,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthResult:
        normalized_email = self._normalize_email(email)
        if self.users.email_exists(normalized_email):
            raise EmailAlreadyRegisteredError("Email is already registered.")

        user = self.users.create(
            email=normalized_email,
            password_hash=hash_password(password),
            display_name=display_name.strip(),
            user_type=user_type,
        )

        try:
            self.db.flush()
            tokens = self._issue_token_pair(
                user,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.commit()
            self.db.refresh(user)
        except IntegrityError as exc:
            self.db.rollback()
            raise EmailAlreadyRegisteredError("Email is already registered.") from exc

        return AuthResult(user=user, tokens=tokens)

    def login(
        self,
        *,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthResult:
        normalized_email = self._normalize_email(email)
        user = self.users.get_by_email(normalized_email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")
        if not user.is_active:
            raise InactiveUserError("User account is inactive.")

        tokens = self._issue_token_pair(
            user,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()
        return AuthResult(user=user, tokens=tokens)

    def refresh_access_token(
        self,
        *,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthResult:
        token_hash = hash_token(refresh_token)
        stored_token = self.refresh_tokens.get_by_hash(token_hash)
        now = self._now()

        if stored_token is None:
            raise InvalidRefreshTokenError("Refresh token is invalid.")
        if stored_token.revoked_at is not None:
            raise InvalidRefreshTokenError("Refresh token has been revoked.")
        if self._is_expired(stored_token.expires_at, now):
            self.refresh_tokens.revoke(stored_token, revoked_at=now)
            self.db.commit()
            raise InvalidRefreshTokenError("Refresh token has expired.")
        if stored_token.user is None or not stored_token.user.is_active:
            raise InactiveUserError("User account is inactive.")

        user = stored_token.user
        raw_refresh_token = generate_refresh_token()
        new_refresh_token = self.refresh_tokens.create(
            user_id=user.id,
            token_hash=hash_token(raw_refresh_token),
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            created_by_ip=ip_address,
            user_agent=user_agent,
        )
        self.db.flush()
        self.refresh_tokens.revoke(
            stored_token,
            revoked_at=now,
            replaced_by_token_id=new_refresh_token.id,
        )

        access_token = create_access_token(str(user.id))
        self.db.commit()
        self.db.refresh(user)

        return AuthResult(
            user=user,
            tokens=TokenPair(
                access_token=access_token,
                refresh_token=raw_refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
        )

    def logout(self, *, refresh_token: str) -> bool:
        token_hash = hash_token(refresh_token)
        stored_token = self.refresh_tokens.get_by_hash(token_hash)
        if stored_token is None or stored_token.revoked_at is not None:
            return False

        self.refresh_tokens.revoke(stored_token, revoked_at=self._now())
        self.db.commit()
        return True

    def _issue_token_pair(
        self,
        user: User,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenPair:
        raw_refresh_token = generate_refresh_token()
        self.refresh_tokens.create(
            user_id=user.id,
            token_hash=hash_token(raw_refresh_token),
            expires_at=self._now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            created_by_ip=ip_address,
            user_agent=user_agent,
        )
        return TokenPair(
            access_token=create_access_token(str(user.id)),
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _is_expired(expires_at: datetime, now: datetime) -> bool:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at <= now
