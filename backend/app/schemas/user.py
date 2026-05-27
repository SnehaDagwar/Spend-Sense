import uuid
from datetime import datetime

from pydantic import EmailStr

from app.models.user import UserType
from app.schemas.base import APIModel


class UserPublic(APIModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str
    user_type: UserType
    onboarding_completed: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
