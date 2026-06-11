"""Automated unit and integration tests for Phase 11 Permission checks, RBAC, and Family operations.

Tests FamilyPermissionGuard, FamilyService business rules, and family route access controls.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import FamilyRole
from app.models.family import Family, FamilyMember
from app.models.user import User
from app.services.family import (
    FamilyConflictError,
    FamilyMemberNotFoundError,
    FamilyNotFoundError,
    FamilyPermissionError,
    FamilyPermissionGuard,
    FamilyService,
    InvitationError,
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
        email="owner@example.com",
        display_name="Owner User",
        is_active=True,
    )
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def mock_admin_user() -> User:
    user = User(
        email="admin@example.com",
        display_name="Admin User",
        is_active=True,
    )
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def mock_member_user() -> User:
    user = User(
        email="member@example.com",
        display_name="Member User",
        is_active=True,
    )
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def mock_child_user() -> User:
    user = User(
        email="child@example.com",
        display_name="Child User",
        is_active=True,
    )
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def mock_family(mock_user: User) -> Family:
    fam = Family(
        owner_user_id=mock_user.id,
        name="The Elite Household",
        currency="INR",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    fam.id = uuid.uuid4()
    return fam


@pytest.fixture
def mock_owner_member(mock_family: Family, mock_user: User) -> FamilyMember:
    member = FamilyMember(
        family_id=mock_family.id,
        user_id=mock_user.id,
        name="Owner User",
        email="owner@example.com",
        role=FamilyRole.OWNER,
        is_active=True,
    )
    member.id = uuid.uuid4()
    return member


@pytest.fixture
def mock_admin_member(mock_family: Family, mock_admin_user: User) -> FamilyMember:
    member = FamilyMember(
        family_id=mock_family.id,
        user_id=mock_admin_user.id,
        name="Admin User",
        email="admin@example.com",
        role=FamilyRole.ADMIN,
        is_active=True,
    )
    member.id = uuid.uuid4()
    return member


@pytest.fixture
def mock_plain_member(mock_family: Family, mock_member_user: User) -> FamilyMember:
    member = FamilyMember(
        family_id=mock_family.id,
        user_id=mock_member_user.id,
        name="Member User",
        email="member@example.com",
        role=FamilyRole.MEMBER,
        is_active=True,
    )
    member.id = uuid.uuid4()
    return member


@pytest.fixture
def mock_child_member(mock_family: Family, mock_child_user: User) -> FamilyMember:
    member = FamilyMember(
        family_id=mock_family.id,
        user_id=mock_child_user.id,
        name="Child User",
        email="child@example.com",
        role=FamilyRole.CHILD,
        is_active=True,
    )
    member.id = uuid.uuid4()
    return member


# ---------------------------------------------------------------------------
# FamilyPermissionGuard Unit Tests
# ---------------------------------------------------------------------------

class TestFamilyPermissionGuard:
    """Verifies that FamilyPermissionGuard enforces correct role-based access rules."""

    def test_member_is_none_raises_permission_error(self) -> None:
        guard = FamilyPermissionGuard()
        with pytest.raises(FamilyPermissionError) as exc_info:
            guard.require(None, "view_family")
        assert "not a member" in str(exc_info.value).lower()

    def test_owner_only_actions(self, mock_owner_member: FamilyMember, mock_admin_member: FamilyMember) -> None:
        guard = FamilyPermissionGuard()
        
        # Owner should succeed
        guard.require(mock_owner_member, "delete_family")
        guard.require(mock_owner_member, "promote_to_admin")
        
        # Admin should fail
        with pytest.raises(FamilyPermissionError) as exc_info:
            guard.require(mock_admin_member, "delete_family")
        assert "only the family owner" in str(exc_info.value).lower()

    def test_admin_or_above_actions(
        self, mock_owner_member: FamilyMember, mock_admin_member: FamilyMember, mock_plain_member: FamilyMember
    ) -> None:
        guard = FamilyPermissionGuard()
        
        # Owner & Admin should succeed
        guard.require(mock_owner_member, "invite_member")
        guard.require(mock_admin_member, "invite_member")
        
        # Member should fail
        with pytest.raises(FamilyPermissionError) as exc_info:
            guard.require(mock_plain_member, "invite_member")
        assert "owner or admin role is required" in str(exc_info.value).lower()

    def test_member_actions(self, mock_plain_member: FamilyMember, mock_child_member: FamilyMember) -> None:
        guard = FamilyPermissionGuard()
        
        # Any active member is implicitly allowed member-level actions
        guard.require(mock_plain_member, "view_family")
        guard.require(mock_child_member, "view_family")
        guard.require(mock_plain_member, "leave_family")


# ---------------------------------------------------------------------------
# FamilyService Logic Tests
# ---------------------------------------------------------------------------

class TestFamilyServiceRules:
    """Verifies service-level validations and permission checks."""

    @patch("app.services.family.FamilyRepository")
    def test_create_family_already_owns_family_raises_conflict(
        self, mock_repo_cls: MagicMock, mock_db: MagicMock, mock_user: User, mock_family: Family
    ) -> None:
        repo = mock_repo_cls.return_value
        repo.get_by_owner.return_value = mock_family
        
        service = FamilyService(mock_db)
        from app.schemas.family import FamilyCreate
        payload = FamilyCreate(name="My New Family", currency="USD")
        
        with pytest.raises(FamilyConflictError):
            service.create_family(user=mock_user, payload=payload)

    @patch("app.services.family.FamilyRepository")
    def test_remove_member_owner_raises_error(
        self, mock_repo_cls: MagicMock, mock_db: MagicMock, mock_user: User, mock_owner_member: FamilyMember
    ) -> None:
        repo = mock_repo_cls.return_value
        repo.get_by_id.return_value = mock_owner_member
        repo.get_member_by_user.return_value = mock_owner_member
        repo.get_member_by_id.return_value = mock_owner_member
        
        service = FamilyService(mock_db)
        
        # Attempt to remove owner member by the owner themselves (should raise guard check error or remove owner rule)
        with pytest.raises(FamilyPermissionError) as exc_info:
            service.remove_member(
                user_id=mock_user.id,
                family_id=mock_owner_member.family_id,
                member_id=mock_owner_member.id,
            )
        assert "owner cannot be removed" in str(exc_info.value).lower()

    @patch("app.services.family.FamilyRepository")
    def test_remove_member_admin_cannot_remove_another_admin(
        self, mock_repo_cls: MagicMock, mock_db: MagicMock, mock_admin_user: User, mock_admin_member: FamilyMember
    ) -> None:
        repo = mock_repo_cls.return_value
        repo.get_by_id.return_value = MagicMock()
        repo.get_member_by_user.return_value = mock_admin_member
        
        other_admin = FamilyMember(
            family_id=mock_admin_member.family_id,
            user_id=uuid.uuid4(),
            name="Other Admin",
            role=FamilyRole.ADMIN,
            is_active=True,
        )
        other_admin.id = uuid.uuid4()
        repo.get_member_by_id.return_value = other_admin
        
        service = FamilyService(mock_db)
        
        with pytest.raises(FamilyPermissionError) as exc_info:
            service.remove_member(
                user_id=mock_admin_user.id,
                family_id=mock_admin_member.family_id,
                member_id=other_admin.id,
            )
        assert "only the family owner can remove an admin" in str(exc_info.value).lower()

    @patch("app.services.family.FamilyRepository")
    def test_leave_family_owner_cannot_leave(
        self, mock_repo_cls: MagicMock, mock_db: MagicMock, mock_user: User, mock_owner_member: FamilyMember
    ) -> None:
        repo = mock_repo_cls.return_value
        repo.get_by_id.return_value = MagicMock()
        repo.get_member_by_user.return_value = mock_owner_member
        
        service = FamilyService(mock_db)
        
        with pytest.raises(FamilyPermissionError) as exc_info:
            service.leave_family(user_id=mock_user.id, family_id=mock_owner_member.family_id)
        assert "owner cannot leave" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Route Handler / Endpoint Integration Tests
# ---------------------------------------------------------------------------

class TestFamilyEndpoints:
    """Verifies route protection, correct HTTP responses, and RBAC mapping."""

    @pytest.fixture(autouse=True)
    def setup_app_override(self, mock_user: User, mock_db: MagicMock) -> None:
        """Override dependencies for route testing."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        yield
        app.dependency_overrides.clear()

    @patch("app.services.family.FamilyService.create_family")
    def test_create_family_endpoint(self, mock_create: MagicMock, mock_family: Family, mock_owner_member: FamilyMember) -> None:
        from app.schemas.family import FamilyDetailPublic, FamilyMemberPublic
        
        public_member = FamilyMemberPublic(
            id=mock_owner_member.id,
            family_id=mock_family.id,
            user_id=mock_owner_member.user_id,
            name=mock_owner_member.name,
            role=mock_owner_member.role,
            email=mock_owner_member.email,
            avatar_url=None,
            spending_limit=None,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        mock_create.return_value = FamilyDetailPublic(
            id=mock_family.id,
            owner_user_id=mock_family.owner_user_id,
            name=mock_family.name,
            currency=mock_family.currency,
            members=[public_member],
            created_at=mock_family.created_at,
            updated_at=mock_family.updated_at,
        )
        
        client = TestClient(app)
        payload = {"name": "The Elite Household", "currency": "INR"}
        
        response = client.post("/api/v1/family", json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["name"] == "The Elite Household"
        assert body["ownerUserId"] == str(mock_family.owner_user_id)
        assert len(body["members"]) == 1

    @patch("app.services.family.FamilyService.delete_family")
    def test_delete_family_endpoint_success(self, mock_delete: MagicMock, mock_family: Family) -> None:
        client = TestClient(app)
        response = client.delete(f"/api/v1/family/{mock_family.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_delete.assert_called_once_with(user_id=mock_delete.call_args[1]["user_id"], family_id=mock_family.id)

    @patch("app.services.family.FamilyService.delete_family")
    def test_delete_family_endpoint_permission_denied(self, mock_delete: MagicMock, mock_family: Family) -> None:
        mock_delete.side_effect = FamilyPermissionError("Permission Denied")
        
        client = TestClient(app)
        response = client.delete(f"/api/v1/family/{mock_family.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "permission denied" in response.json()["error"]["message"].lower()

    @patch("app.services.family.FamilyService.invite_member")
    def test_invite_member_endpoint_success(self, mock_invite: MagicMock, mock_family: Family) -> None:
        from app.schemas.family import InviteResponse
        
        mock_invite.return_value = InviteResponse(
            invitation_id=uuid.uuid4(),
            family_id=mock_family.id,
            email="invitee@example.com",
            role=FamilyRole.MEMBER,
            invitation_token="opaque-token-string",
            expires_at=datetime.now() + timedelta(hours=72),
            created_at=datetime.now(),
        )
        
        client = TestClient(app)
        payload = {"email": "invitee@example.com", "role": "Member"}
        
        response = client.post(f"/api/v1/family/{mock_family.id}/invite", json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["email"] == "invitee@example.com"
        assert body["invitationToken"] == "opaque-token-string"

    @patch("app.services.family.FamilyService.get_shared_analytics")
    def test_get_family_analytics_endpoint(self, mock_analytics: MagicMock, mock_family: Family) -> None:
        from app.schemas.family import FamilyAnalytics, SharedExpenseSummary, SharedBudgetSummary, SharedGoalSummary
        
        mock_analytics.return_value = FamilyAnalytics(
            family_id=mock_family.id,
            family_name=mock_family.name,
            expenses=SharedExpenseSummary(total_amount=Decimal("500.00"), expense_count=5, top_category="Food", current_month_total=Decimal("300.00")),
            budget=SharedBudgetSummary(total_planned=Decimal("1000.00"), total_spent=Decimal("500.00"), total_remaining=Decimal("500.00"), member_count=2),
            goals=SharedGoalSummary(total_goals=2, active_goals=2, completed_goals=0, total_saved=Decimal("150.00"), total_target=Decimal("1000.00")),
            generated_at=datetime.now(timezone.utc),
        )
        
        client = TestClient(app)
        response = client.get(f"/api/v1/family/{mock_family.id}/analytics")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["familyName"] == mock_family.name
        assert float(body["expenses"]["totalAmount"]) == 500.0
