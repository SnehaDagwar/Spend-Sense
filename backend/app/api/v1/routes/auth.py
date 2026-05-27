from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
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


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    service = AuthService(db)
    try:
        result = service.register(
            email=str(payload.email),
            password=payload.password,
            display_name=payload.display_name,
            user_type=payload.user_type,
            ip_address=_client_host(request),
            user_agent=request.headers.get("user-agent"),
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        ) from exc

    return _auth_response(result.user, result.tokens)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    service = AuthService(db)
    try:
        result = service.login(
            email=str(payload.email),
            password=payload.password,
            ip_address=_client_host(request),
            user_agent=request.headers.get("user-agent"),
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        ) from exc

    return _auth_response(result.user, result.tokens)


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    service = AuthService(db)
    try:
        result = service.refresh_access_token(
            refresh_token=payload.refresh_token,
            ip_address=_client_host(request),
            user_agent=request.headers.get("user-agent"),
        )
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        ) from exc

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
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    AuthService(db).logout(refresh_token=payload.refresh_token)
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
    return request.client.host if request.client else None
