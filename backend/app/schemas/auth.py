from pydantic import EmailStr, Field, field_validator

from app.core.security import password_validation_errors
from app.models.user import UserType
from app.schemas.base import APIModel
from app.schemas.user import UserPublic


class RegisterRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    user_type: UserType = UserType.PROFESSIONAL

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Display name cannot be blank.")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        errors = password_validation_errors(value)
        if errors:
            raise ValueError(" ".join(errors))
        return value


class LoginRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshTokenRequest(APIModel):
    refresh_token: str = Field(min_length=32)


class LogoutRequest(APIModel):
    refresh_token: str = Field(min_length=32)


class TokenResponse(APIModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(TokenResponse):
    user: UserPublic
