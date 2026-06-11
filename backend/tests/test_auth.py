"""Automated unit and integration tests for Phase 1 Authentication and Token Management.

Tests user registration, login, token refresh (including token rotation and revocation),
logout, and dependency checks.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User, UserType, RefreshToken
from app.services.auth import (
    AuthService,
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)


# ---------------------------------------------------------------------------
# Test Fixtures & Mocks
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_user() -> User:
    user = User(
        email="test.user@example.com",
        password_hash="hashed_password",
        display_name="Test User",
        user_type=UserType.PROFESSIONAL,
        is_active=True,
        onboarding_completed=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def mock_inactive_user() -> User:
    user = User(
        email="inactive@example.com",
        password_hash="hashed_password",
        display_name="Inactive User",
        user_type=UserType.PROFESSIONAL,
        is_active=False,
        onboarding_completed=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    user.id = uuid.uuid4()
    return user


# ---------------------------------------------------------------------------
# Route Handler / Endpoint Integration Tests
# ---------------------------------------------------------------------------

class TestAuthEndpoints:
    """Verifies authentication routes: register, login, refresh, logout, me."""

    @pytest.fixture(autouse=True)
    def setup_app_override(self, mock_user: User, mock_db: MagicMock) -> None:
        """Override dependencies for route testing."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        yield
        app.dependency_overrides.clear()

    @patch("app.services.auth.AuthService.register")
    def test_register_endpoint_success(self, mock_register: MagicMock, mock_user: User) -> None:
        from app.services.auth import AuthResult, TokenPair
        
        tokens = TokenPair(
            access_token="mock-access-token",
            refresh_token="mock-refresh-token",
            token_type="bearer",
            expires_in=900,
        )
        mock_register.return_value = AuthResult(user=mock_user, tokens=tokens)
        
        client = TestClient(app)
        payload = {
            "email": "test.user@example.com",
            "password": "StrongPass1!",
            "displayName": "Test User",
            "userType": "Professional",
        }
        
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["accessToken"] == "mock-access-token"
        assert body["refreshToken"] == "mock-refresh-token"
        assert body["user"]["email"] == mock_user.email
        mock_register.assert_called_once()

    @patch("app.services.auth.AuthService.register")
    def test_register_endpoint_duplicate_email(self, mock_register: MagicMock) -> None:
        mock_register.side_effect = EmailAlreadyRegisteredError("Email exists")
        
        client = TestClient(app)
        payload = {
            "email": "test.user@example.com",
            "password": "StrongPass1!",
            "displayName": "Test User",
            "userType": "Professional",
        }
        
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already registered" in response.json()["error"]["message"].lower()

    @patch("app.services.auth.AuthService.login")
    def test_login_endpoint_success(self, mock_login: MagicMock, mock_user: User) -> None:
        from app.services.auth import AuthResult, TokenPair
        
        tokens = TokenPair(
            access_token="mock-access-token",
            refresh_token="mock-refresh-token",
            token_type="bearer",
            expires_in=900,
        )
        mock_login.return_value = AuthResult(user=mock_user, tokens=tokens)
        
        client = TestClient(app)
        payload = {
            "email": "test.user@example.com",
            "password": "StrongPass1!",
        }
        
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["accessToken"] == "mock-access-token"
        assert body["refreshToken"] == "mock-refresh-token"

    @patch("app.services.auth.AuthService.login")
    def test_login_endpoint_invalid_credentials(self, mock_login: MagicMock) -> None:
        mock_login.side_effect = InvalidCredentialsError("Invalid")
        
        client = TestClient(app)
        payload = {
            "email": "test.user@example.com",
            "password": "WrongPassword",
        }
        
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid email or password" in response.json()["error"]["message"].lower()

    @patch("app.services.auth.AuthService.login")
    def test_login_endpoint_inactive_user(self, mock_login: MagicMock) -> None:
        mock_login.side_effect = InactiveUserError("Inactive")
        
        client = TestClient(app)
        payload = {
            "email": "inactive@example.com",
            "password": "StrongPass1!",
        }
        
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in response.json()["error"]["message"].lower()

    @patch("app.services.auth.AuthService.refresh_access_token")
    def test_refresh_endpoint_success(self, mock_refresh: MagicMock, mock_user: User) -> None:
        from app.services.auth import AuthResult, TokenPair
        
        tokens = TokenPair(
            access_token="new-access-token",
            refresh_token="new-refresh-token",
            token_type="bearer",
            expires_in=900,
        )
        mock_refresh.return_value = AuthResult(user=mock_user, tokens=tokens)
        
        client = TestClient(app)
        payload = {
            "refreshToken": "old-refresh-token-at-least-32-chars-long",
        }
        
        response = client.post("/api/v1/auth/refresh", json=payload)
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["accessToken"] == "new-access-token"
        assert body["refreshToken"] == "new-refresh-token"

    @patch("app.services.auth.AuthService.refresh_access_token")
    def test_refresh_endpoint_invalid_token(self, mock_refresh: MagicMock) -> None:
        mock_refresh.side_effect = InvalidRefreshTokenError("Invalid")
        
        client = TestClient(app)
        payload = {
            "refreshToken": "invalid-token-at-least-32-chars-long",
        }
        
        response = client.post("/api/v1/auth/refresh", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "refresh token is invalid" in response.json()["error"]["message"].lower()

    def test_me_endpoint_success(self, mock_user: User) -> None:
        client = TestClient(app)
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["email"] == mock_user.email
        assert body["displayName"] == mock_user.display_name

    @patch("app.services.auth.AuthService.logout")
    def test_logout_endpoint_success(self, mock_logout: MagicMock) -> None:
        client = TestClient(app)
        payload = {
            "refreshToken": "token-to-revoke-at-least-32-chars-long",
        }
        response = client.post("/api/v1/auth/logout", json=payload)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_logout.assert_called_once_with(refresh_token="token-to-revoke-at-least-32-chars-long")


# ---------------------------------------------------------------------------
# Business Service Logic Tests
# ---------------------------------------------------------------------------

class TestAuthService:
    """Verifies core AuthService functions: register, login, refresh, logout."""

    @patch("app.services.auth.UserRepository")
    @patch("app.services.auth.hash_password")
    def test_register_creates_user(self, mock_hash: MagicMock, mock_user_repo_cls: MagicMock, mock_db: MagicMock) -> None:
        mock_hash.return_value = "hashed_pwd"
        user_repo = mock_user_repo_cls.return_value
        user_repo.email_exists.return_value = False
        
        mock_new_user = User(
            email="new@example.com",
            password_hash="hashed_pwd",
            display_name="New User",
            user_type=UserType.PROFESSIONAL,
        )
        user_repo.create.return_value = mock_new_user
        
        service = AuthService(mock_db)
        
        # Stub token generation
        with patch.object(service, "_issue_token_pair") as mock_issue:
            from app.services.auth import TokenPair
            mock_issue.return_value = TokenPair("a", "r", "bearer", 900)
            
            res = service.register(
                email="new@example.com",
                password="Password1!",
                display_name="New User",
                user_type=UserType.PROFESSIONAL,
            )
            
            assert res.user == mock_new_user
            user_repo.email_exists.assert_called_once_with("new@example.com")
            user_repo.create.assert_called_once_with(
                email="new@example.com",
                password_hash="hashed_pwd",
                display_name="New User",
                user_type=UserType.PROFESSIONAL,
            )
            mock_db.commit.assert_called_once()

    @patch("app.services.auth.UserRepository")
    def test_register_duplicate_email_raises_error(self, mock_user_repo_cls: MagicMock, mock_db: MagicMock) -> None:
        user_repo = mock_user_repo_cls.return_value
        user_repo.email_exists.return_value = True
        
        service = AuthService(mock_db)
        with pytest.raises(EmailAlreadyRegisteredError):
            service.register(
                email="exists@example.com",
                password="Password1!",
                display_name="Duplicate User",
                user_type=UserType.PROFESSIONAL,
            )

    @patch("app.services.auth.UserRepository")
    @patch("app.services.auth.verify_password")
    def test_login_success(self, mock_verify: MagicMock, mock_user_repo_cls: MagicMock, mock_db: MagicMock, mock_user: User) -> None:
        user_repo = mock_user_repo_cls.return_value
        user_repo.get_by_email.return_value = mock_user
        mock_verify.return_value = True
        
        service = AuthService(mock_db)
        with patch.object(service, "_issue_token_pair") as mock_issue:
            from app.services.auth import TokenPair
            mock_issue.return_value = TokenPair("a", "r", "bearer", 900)
            
            res = service.login(email="test.user@example.com", password="StrongPass1!")
            assert res.user == mock_user
            mock_verify.assert_called_once_with("StrongPass1!", mock_user.password_hash)

    @patch("app.services.auth.UserRepository")
    def test_login_invalid_email_raises_error(self, mock_user_repo_cls: MagicMock, mock_db: MagicMock) -> None:
        user_repo = mock_user_repo_cls.return_value
        user_repo.get_by_email.return_value = None
        
        service = AuthService(mock_db)
        with pytest.raises(InvalidCredentialsError):
            service.login(email="wrong@example.com", password="Password1!")

    @patch("app.services.auth.UserRepository")
    @patch("app.services.auth.verify_password")
    def test_login_inactive_user_raises_error(self, mock_verify: MagicMock, mock_user_repo_cls: MagicMock, mock_db: MagicMock, mock_inactive_user: User) -> None:
        user_repo = mock_user_repo_cls.return_value
        user_repo.get_by_email.return_value = mock_inactive_user
        mock_verify.return_value = True
        
        service = AuthService(mock_db)
        with pytest.raises(InactiveUserError):
            service.login(email="inactive@example.com", password="Password1!")

    @patch("app.services.auth.RefreshTokenRepository")
    @patch("app.services.auth.hash_token")
    def test_logout_revokes_token(self, mock_hash: MagicMock, mock_token_repo_cls: MagicMock, mock_db: MagicMock) -> None:
        token_repo = mock_token_repo_cls.return_value
        mock_hash.return_value = "token_hash"
        
        mock_token = MagicMock(spec=RefreshToken)
        mock_token.revoked_at = None
        token_repo.get_by_hash.return_value = mock_token
        
        service = AuthService(mock_db)
        success = service.logout(refresh_token="active-token")
        
        assert success is True
        token_repo.get_by_hash.assert_called_once_with("token_hash")
        token_repo.revoke.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch("app.services.auth.RefreshTokenRepository")
    @patch("app.services.auth.hash_token")
    def test_logout_already_revoked_returns_false(self, mock_hash: MagicMock, mock_token_repo_cls: MagicMock, mock_db: MagicMock) -> None:
        token_repo = mock_token_repo_cls.return_value
        mock_token = MagicMock(spec=RefreshToken)
        mock_token.revoked_at = datetime.now(timezone.utc)
        token_repo.get_by_hash.return_value = mock_token
        
        service = AuthService(mock_db)
        success = service.logout(refresh_token="revoked-token")
        
        assert success is False
        token_repo.revoke.assert_not_called()
