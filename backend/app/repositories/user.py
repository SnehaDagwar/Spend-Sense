import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User, UserType


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self.db.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(func.lower(User.email) == email.lower())
        return self.db.scalar(statement)

    def email_exists(self, email: str) -> bool:
        statement = select(User.id).where(func.lower(User.email) == email.lower())
        return self.db.scalar(statement) is not None

    def create(
        self,
        *,
        email: str,
        password_hash: str,
        display_name: str,
        user_type: UserType,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            user_type=user_type,
        )
        self.db.add(user)
        return user
