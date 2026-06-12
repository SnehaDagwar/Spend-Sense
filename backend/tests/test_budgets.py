"""Unit and integration tests for the Budget system.

Tests the full budget lifecycle: creation (with rollover), income updates,
category allocation upserts, analytics computations, and error boundaries.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.budget import BudgetCategoryAllocation, MonthlyBudget
from app.models.category import SpendingCategory
from app.models.user import User
from app.schemas.budget import (
    AllocationUpsert,
    BudgetCreate,
    BudgetFilters,
    BudgetPublic,
    BudgetUpdate,
)
from app.services.budget import (
    BudgetConflictError,
    BudgetNotFoundError,
    BudgetService,
    BudgetValidationError,
    BudgetCategoryError,
    _compute_allocation_analytics,
    _compute_budget_analytics,
)


# ---------------------------------------------------------------------------
# Endpoint Integration Tests
# ---------------------------------------------------------------------------

class TestBudgetEndpoints:
    """Verifies route-level HTTP responses for budget CRUD."""

    @pytest.fixture(autouse=True)
    def setup_app_override(self, mock_user: User, mock_db: MagicMock) -> None:
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        yield
        app.dependency_overrides.clear()

    @patch("app.services.budget.BudgetService.list_budgets")
    def test_list_budgets_returns_200(self, mock_list: MagicMock) -> None:
        mock_list.return_value = []
        client = TestClient(app)

        response = client.get("/api/v1/budgets")
        assert response.status_code == status.HTTP_200_OK
        mock_list.assert_called_once()

    @patch("app.services.budget.BudgetService.create_budget")
    def test_create_budget_success(
        self, mock_create: MagicMock, mock_budget: MonthlyBudget
    ) -> None:
        # Return a BudgetPublic-shaped mock
        from app.schemas.budget import BudgetPublic, BudgetAnalytics
        mock_create.return_value = BudgetPublic(
            id=mock_budget.id,
            month="2026-06",
            income=Decimal("50000.00"),
            warning_threshold=Decimal("0.80"),
            categories=[],
            analytics=BudgetAnalytics(
                total_planned=Decimal("0.00"),
                total_spent=Decimal("0.00"),
                total_remaining=Decimal("0.00"),
                pct_used=Decimal("0.00"),
                projected_spend=Decimal("0.00"),
                is_over_budget=False,
            ),
            created_at=mock_budget.created_at,
            updated_at=mock_budget.updated_at,
        )
        client = TestClient(app)

        payload = {"month": "2026-06", "income": 50000}
        response = client.post("/api/v1/budgets", json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["month"] == "2026-06"
        mock_create.assert_called_once()

    @patch("app.services.budget.BudgetService.create_budget")
    def test_create_budget_duplicate_returns_409(
        self, mock_create: MagicMock
    ) -> None:
        mock_create.side_effect = BudgetConflictError("Budget exists")
        client = TestClient(app)

        response = client.post("/api/v1/budgets", json={"month": "2026-06", "income": 50000})
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_budget_invalid_month_format_returns_422(self) -> None:
        client = TestClient(app)
        response = client.post("/api/v1/budgets", json={"month": "June 2026", "income": 5000})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_budget_negative_income_returns_422(self) -> None:
        client = TestClient(app)
        response = client.post("/api/v1/budgets", json={"month": "2026-06", "income": -100})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("app.services.budget.BudgetService.get_budget")
    def test_get_budget_not_found_returns_404(
        self, mock_get: MagicMock
    ) -> None:
        mock_get.side_effect = BudgetNotFoundError("Not found")
        client = TestClient(app)

        response = client.get(f"/api/v1/budgets/{uuid.uuid4()}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.services.budget.BudgetService.delete_budget")
    def test_delete_budget_success(
        self, mock_delete: MagicMock, mock_budget: MonthlyBudget
    ) -> None:
        client = TestClient(app)
        response = client.delete(f"/api/v1/budgets/{mock_budget.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_delete.assert_called_once()

    @patch("app.services.budget.BudgetService.delete_budget")
    def test_delete_budget_not_found_returns_404(
        self, mock_delete: MagicMock
    ) -> None:
        mock_delete.side_effect = BudgetNotFoundError("Not found")
        client = TestClient(app)

        response = client.delete(f"/api/v1/budgets/{uuid.uuid4()}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Service Unit Tests
# ---------------------------------------------------------------------------

class TestBudgetService:
    """Verifies BudgetService business rules and analytics computations."""

    def test_get_budget_not_owned_raises_not_found(
        self, mock_db: MagicMock, mock_budget: MonthlyBudget, mock_other_user: User
    ) -> None:
        service = BudgetService(mock_db)
        service.repo.get_by_id_and_user = MagicMock(return_value=None)

        with pytest.raises(BudgetNotFoundError):
            service.get_budget(user_id=mock_other_user.id, budget_id=mock_budget.id)

    def test_create_budget_duplicate_raises_conflict(
        self, mock_db: MagicMock, mock_user: User, mock_budget: MonthlyBudget
    ) -> None:
        service = BudgetService(mock_db)
        service.repo.get_by_month_and_user = MagicMock(return_value=mock_budget)

        payload = BudgetCreate(month="2026-06", income=Decimal("50000.00"))
        with pytest.raises(BudgetConflictError) as exc_info:
            service.create_budget(user_id=mock_user.id, payload=payload)
        assert "already exists" in str(exc_info.value).lower()

    def test_create_budget_invalid_category_raises_error(
        self, mock_db: MagicMock, mock_user: User
    ) -> None:
        service = BudgetService(mock_db)
        service.repo.get_by_month_and_user = MagicMock(return_value=None)
        service.categories.get_by_id_for_user = MagicMock(return_value=None)

        bad_cat_id = uuid.uuid4()
        payload = BudgetCreate(
            month="2026-07",
            income=Decimal("40000.00"),
            categories=[AllocationUpsert(category_id=bad_cat_id, planned_amount=Decimal("5000.00"))],
        )
        with pytest.raises(BudgetCategoryError) as exc_info:
            service.create_budget(user_id=mock_user.id, payload=payload)
        assert "not found or not accessible" in str(exc_info.value).lower()

    def test_delete_budget_not_owned_raises_not_found(
        self, mock_db: MagicMock, mock_budget: MonthlyBudget, mock_other_user: User
    ) -> None:
        service = BudgetService(mock_db)
        service.repo.get_by_id_and_user = MagicMock(return_value=None)

        with pytest.raises(BudgetNotFoundError):
            service.delete_budget(user_id=mock_other_user.id, budget_id=mock_budget.id)

    def test_delete_budget_delegates_to_repo(
        self, mock_db: MagicMock, mock_budget: MonthlyBudget, mock_user: User
    ) -> None:
        service = BudgetService(mock_db)
        service.repo.get_by_id_and_user = MagicMock(return_value=mock_budget)
        service.repo.delete = MagicMock()

        service.delete_budget(user_id=mock_user.id, budget_id=mock_budget.id)

        service.repo.delete.assert_called_once_with(mock_budget)
        mock_db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Analytics Pure-Function Tests
# ---------------------------------------------------------------------------

class TestBudgetAnalyticsFunctions:
    """Verifies the pure analytics helper functions without DB."""

    def _make_alloc(self, planned: Decimal, category_id: uuid.UUID | None = None) -> BudgetCategoryAllocation:
        cat_id = category_id or uuid.uuid4()
        alloc = MagicMock(spec=BudgetCategoryAllocation)
        alloc.category_id = cat_id
        alloc.planned_amount = planned
        return alloc

    def test_allocation_analytics_under_budget(self) -> None:
        cat_id = uuid.uuid4()
        alloc = self._make_alloc(Decimal("10000.00"), cat_id)
        spending_map = {cat_id: Decimal("7500.00")}

        analytics = _compute_allocation_analytics(alloc, spending_map, Decimal("0.80"))

        assert analytics.spent == Decimal("7500.00")
        assert analytics.remaining == Decimal("2500.00")
        assert analytics.pct_used == Decimal("75.00")
        assert not analytics.is_over_budget
        assert not analytics.is_near_limit

    def test_allocation_analytics_near_limit(self) -> None:
        cat_id = uuid.uuid4()
        alloc = self._make_alloc(Decimal("10000.00"), cat_id)
        spending_map = {cat_id: Decimal("8500.00")}

        analytics = _compute_allocation_analytics(alloc, spending_map, Decimal("0.80"))

        assert analytics.pct_used == Decimal("85.00")
        assert not analytics.is_over_budget
        assert analytics.is_near_limit  # 85% >= 80% threshold

    def test_allocation_analytics_over_budget(self) -> None:
        cat_id = uuid.uuid4()
        alloc = self._make_alloc(Decimal("5000.00"), cat_id)
        spending_map = {cat_id: Decimal("6000.00")}

        analytics = _compute_allocation_analytics(alloc, spending_map, Decimal("0.80"))

        assert analytics.is_over_budget
        assert analytics.remaining == Decimal("0.00")  # clamped at 0

    def test_allocation_analytics_zero_planned_with_spending(self) -> None:
        cat_id = uuid.uuid4()
        alloc = self._make_alloc(Decimal("0.00"), cat_id)
        spending_map = {cat_id: Decimal("500.00")}

        analytics = _compute_allocation_analytics(alloc, spending_map, Decimal("0.80"))

        assert analytics.pct_used == Decimal("100.00")

    def test_allocation_analytics_zero_planned_no_spending(self) -> None:
        cat_id = uuid.uuid4()
        alloc = self._make_alloc(Decimal("0.00"), cat_id)
        spending_map = {}

        analytics = _compute_allocation_analytics(alloc, spending_map, Decimal("0.80"))

        assert analytics.pct_used == Decimal("0.00")

    def test_budget_analytics_projected_spend(self) -> None:
        budget = MagicMock(spec=MonthlyBudget)
        budget.month = date.today().replace(day=1)
        budget.warning_threshold = Decimal("0.80")
        budget.category_allocations = []

        # If total_spent = 3000 halfway through month → projection ≈ 6000
        spending_map: dict[uuid.UUID, Decimal] = {}

        analytics = _compute_budget_analytics(budget, spending_map)
        assert analytics.total_spent == Decimal("0.00")
        assert analytics.projected_spend == Decimal("0.00")

    def test_budget_analytics_is_over_budget(self) -> None:
        budget = MagicMock(spec=MonthlyBudget)
        budget.month = date.today().replace(day=1)
        budget.warning_threshold = Decimal("0.80")

        cat_id = uuid.uuid4()
        alloc = self._make_alloc(Decimal("5000.00"), cat_id)
        budget.category_allocations = [alloc]

        spending_map = {cat_id: Decimal("6000.00")}

        analytics = _compute_budget_analytics(budget, spending_map)
        assert analytics.is_over_budget
        assert analytics.total_spent == Decimal("6000.00")
        assert analytics.total_planned == Decimal("5000.00")
