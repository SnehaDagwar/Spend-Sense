import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.audit import AuditAction, record_audit
from app.core.config import settings
from app.core.limiter import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserPublic
from app.services.auth import (
    EmailAlreadyRegisteredError,
    AuthService,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    TokenPair,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_AUTH_LIMIT = f"{settings.RATE_LIMIT_AUTH_PER_MINUTE}/minute"


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(_AUTH_LIMIT)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    t0 = time.monotonic()
    service = AuthService(db)
    ip = _client_host(request)
    ua = request.headers.get("user-agent")
    try:
        result = service.register(
            email=str(payload.email),
            password=payload.password,
            display_name=payload.display_name,
            user_type=payload.user_type,
            ip_address=ip,
            user_agent=ua,
        )
    except EmailAlreadyRegisteredError as exc:
        record_audit(
            db,
            action=AuditAction.AUTH_REGISTER_FAILURE,
            outcome="failure",
            ip_address=ip,
            user_agent=ua,
            latency_ms=int((time.monotonic() - t0) * 1000),
            detail={"reason": "email_already_registered"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        ) from exc

    record_audit(
        db,
        action=AuditAction.AUTH_REGISTER_SUCCESS,
        outcome="success",
        user_id=result.user.id,
        ip_address=ip,
        user_agent=ua,
        latency_ms=int((time.monotonic() - t0) * 1000),
    )
    db.commit()
    return _auth_response(result.user, result.tokens)


@router.post("/login", response_model=AuthResponse)
@limiter.limit(_AUTH_LIMIT)
def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    t0 = time.monotonic()
    service = AuthService(db)
    ip = _client_host(request)
    ua = request.headers.get("user-agent")
    try:
        result = service.login(
            email=str(payload.email),
            password=payload.password,
            ip_address=ip,
            user_agent=ua,
        )
    except InvalidCredentialsError as exc:
        record_audit(
            db,
            action=AuditAction.AUTH_LOGIN_FAILURE,
            outcome="failure",
            ip_address=ip,
            user_agent=ua,
            latency_ms=int((time.monotonic() - t0) * 1000),
            detail={"reason": "invalid_credentials"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        record_audit(
            db,
            action=AuditAction.AUTH_LOGIN_FAILURE,
            outcome="failure",
            ip_address=ip,
            user_agent=ua,
            latency_ms=int((time.monotonic() - t0) * 1000),
            detail={"reason": "inactive_account"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        ) from exc

    record_audit(
        db,
        action=AuditAction.AUTH_LOGIN_SUCCESS,
        outcome="success",
        user_id=result.user.id,
        ip_address=ip,
        user_agent=ua,
        latency_ms=int((time.monotonic() - t0) * 1000),
    )
    db.commit()
    return _auth_response(result.user, result.tokens)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(_AUTH_LIMIT)
def refresh_access_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    t0 = time.monotonic()
    service = AuthService(db)
    ip = _client_host(request)
    ua = request.headers.get("user-agent")
    try:
        result = service.refresh_access_token(
            refresh_token=payload.refresh_token,
            ip_address=ip,
            user_agent=ua,
        )
    except InvalidRefreshTokenError as exc:
        record_audit(
            db,
            action=AuditAction.AUTH_REFRESH_FAILURE,
            outcome="failure",
            ip_address=ip,
            user_agent=ua,
            latency_ms=int((time.monotonic() - t0) * 1000),
            detail={"reason": "invalid_refresh_token"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        record_audit(
            db,
            action=AuditAction.AUTH_REFRESH_FAILURE,
            outcome="failure",
            ip_address=ip,
            user_agent=ua,
            latency_ms=int((time.monotonic() - t0) * 1000),
            detail={"reason": "inactive_account"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        ) from exc

    record_audit(
        db,
        action=AuditAction.AUTH_REFRESH_SUCCESS,
        outcome="success",
        user_id=result.user.id,
        ip_address=ip,
        user_agent=ua,
        latency_ms=int((time.monotonic() - t0) * 1000),
    )
    db.commit()
    return TokenResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
        token_type=result.tokens.token_type,
        expires_in=result.tokens.expires_in,
    )


@router.get("/me", response_model=UserPublic)
def current_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    t0 = time.monotonic()
    ip = _client_host(request)
    ua = request.headers.get("user-agent")
    AuthService(db).logout(refresh_token=payload.refresh_token)
    record_audit(
        db,
        action=AuditAction.AUTH_LOGOUT,
        outcome="success",
        ip_address=ip,
        user_agent=ua,
        latency_ms=int((time.monotonic() - t0) * 1000),
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _auth_response(user: User, tokens: TokenPair) -> AuthResponse:
    return AuthResponse(
        user=user,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
    )


def _client_host(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
