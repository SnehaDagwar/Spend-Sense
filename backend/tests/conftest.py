"""Shared pytest fixtures for all backend tests.

Centralises the most commonly used mocks and eliminates duplication
across test modules.  Import these in any test file automatically
through pytest's conftest discovery.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.category import SpendingCategory
from app.models.enums import (
    FamilyRole,
    SavingsGoalStatus,
    UserType,
    ChallengeStatus,
    ChallengeType,
    BadgeCategory,
)
from app.models.expense import Expense
from app.models.family import Family, FamilyMember
from app.models.goal import SavingsGoal
from app.models.user import User, RefreshToken
from app.models.budget import MonthlyBudget, BudgetCategoryAllocation


# ---------------------------------------------------------------------------
# Core Infrastructure Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db() -> MagicMock:
    """A lightweight SQLAlchemy-session mock."""
    return MagicMock()


# ---------------------------------------------------------------------------
# User Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_user() -> User:
    """A fully-initialised active user model."""
    user = User(
        email="ninja@spend-sense.app",
        password_hash="hashed_password_123",
        display_name="Finance Ninja",
        user_type=UserType.PROFESSIONAL,
        is_active=True,
        onboarding_completed=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def mock_other_user() -> User:
    """A second user for ownership-check tests."""
    user = User(
        email="rival@spend-sense.app",
        password_hash="another_hash",
        display_name="Rival User",
        user_type=UserType.STUDENT,
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
        email="inactive@spend-sense.app",
        password_hash="hashed",
        display_name="Inactive",
        user_type=UserType.PROFESSIONAL,
        is_active=False,
        onboarding_completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    user.id = uuid.uuid4()
    return user


# ---------------------------------------------------------------------------
# Category Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_system_category() -> SpendingCategory:
    cat = SpendingCategory(
        slug="food",
        name="Food & Dining",
        icon="Utensils",
        color="#FF6B6B",
        is_system=True,
        is_archived=False,
        display_order=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    cat.id = uuid.uuid4()
    cat.user_id = None
    return cat


@pytest.fixture
def mock_custom_category(mock_user: User) -> SpendingCategory:
    cat = SpendingCategory(
        slug="my-coffee",
        name="Coffee",
        icon="Coffee",
        color="#6B8EFF",
        is_system=False,
        is_archived=False,
        display_order=10,
        user_id=mock_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    cat.id = uuid.uuid4()
    return cat


# ---------------------------------------------------------------------------
# Expense Fixtures
# ---------------------------------------------------------------------------


def _make_expense(user_id: uuid.UUID, category: SpendingCategory, amount: Decimal, note: str = "Test") -> Expense:
    exp = Expense(
        user_id=user_id,
        category_id=category.id,
        amount=amount,
        currency="INR",
        expense_date=date.today(),
        note=note,
        payment_method="upi",
        tags=[],
        is_recurring=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    exp.id = uuid.uuid4()
    exp.category = category
    return exp


@pytest.fixture
def mock_expense(mock_user: User, mock_system_category: SpendingCategory) -> Expense:
    return _make_expense(mock_user.id, mock_system_category, Decimal("450.00"), "Lunch")


# ---------------------------------------------------------------------------
# Budget Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_budget(mock_user: User) -> MonthlyBudget:
    budget = MonthlyBudget(
        user_id=mock_user.id,
        month=date(2026, 6, 1),
        income=Decimal("50000.00"),
        warning_threshold=Decimal("0.80"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    budget.id = uuid.uuid4()
    budget.category_allocations = []
    return budget


# ---------------------------------------------------------------------------
# Goal Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_goal(mock_user: User) -> SavingsGoal:
    goal = SavingsGoal(
        user_id=mock_user.id,
        name="Emergency Fund",
        icon="shield",
        color="#22C55E",
        target_amount=Decimal("100000.00"),
        current_amount=Decimal("30000.00"),
        monthly_contribution=Decimal("5000.00"),
        target_date=datetime.now() + timedelta(days=365),
        status=SavingsGoalStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    goal.id = uuid.uuid4()
    return goal


# ---------------------------------------------------------------------------
# Family Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_family(mock_user: User) -> Family:
    fam = Family(
        owner_user_id=mock_user.id,
        name="The Ninja Household",
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
        name="Finance Ninja",
        email="ninja@spend-sense.app",
        role=FamilyRole.OWNER,
        is_active=True,
    )
    member.id = uuid.uuid4()
    return member
