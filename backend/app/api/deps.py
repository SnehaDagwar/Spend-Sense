import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import TokenDecodeError, decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token, expected_type="access")
        user_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, TypeError, ValueError, TokenDecodeError) as exc:
        raise unauthorized from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise unauthorized
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user
