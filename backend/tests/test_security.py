from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    hash_token,
    password_validation_errors,
    verify_password,
)


def test_password_validation_requires_complexity() -> None:
    errors = password_validation_errors("short")
    assert any("8 characters" in message for message in errors)
    assert any("uppercase" in message for message in errors)


def test_hash_and_verify_password_round_trip() -> None:
    hashed = hash_password("StrongPass1!")
    assert verify_password("StrongPass1!", hashed)
    assert not verify_password("WrongPass1!", hashed)


def test_hash_token_is_stable() -> None:
    assert hash_token("opaque-token") == hash_token("opaque-token")
    assert hash_token("opaque-token") != hash_token("other-token")


def test_access_token_decode_requires_access_type() -> None:
    token = create_access_token("user-id", expires_delta=timedelta(minutes=5))
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "user-id"
    assert payload["type"] == "access"

    with pytest.raises(Exception):
        decode_token(token, expected_type="refresh")
