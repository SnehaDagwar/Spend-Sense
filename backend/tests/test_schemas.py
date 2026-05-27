import pytest
from pydantic import ValidationError

from app.models.user import UserType
from app.schemas.auth import RegisterRequest


def test_register_request_rejects_weak_password() -> None:
    with pytest.raises(ValidationError) as exc_info:
        RegisterRequest(
            email="alex@example.com",
            password="weakpass",
            displayName="Alex",
            userType=UserType.PROFESSIONAL,
        )

    assert "password" in str(exc_info.value).lower()


def test_register_request_accepts_valid_payload() -> None:
    payload = RegisterRequest(
        email="alex@example.com",
        password="StrongPass1!",
        displayName="Alex",
        userType=UserType.PROFESSIONAL,
    )
    assert payload.display_name == "Alex"
    assert payload.user_type == UserType.PROFESSIONAL
