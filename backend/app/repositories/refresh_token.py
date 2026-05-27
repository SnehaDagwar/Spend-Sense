import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.user import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        created_by_ip: str | None = None,
        user_agent: str | None = None,
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by_ip=created_by_ip,
            user_agent=user_agent,
        )
        self.db.add(refresh_token)
        return refresh_token

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        statement = (
            select(RefreshToken)
            .options(joinedload(RefreshToken.user))
            .where(RefreshToken.token_hash == token_hash)
        )
        return self.db.scalar(statement)

    def revoke(
        self,
        refresh_token: RefreshToken,
        *,
        revoked_at: datetime,
        replaced_by_token_id: uuid.UUID | None = None,
    ) -> RefreshToken:
        refresh_token.revoked_at = revoked_at
        refresh_token.replaced_by_token_id = replaced_by_token_id
        return refresh_token
