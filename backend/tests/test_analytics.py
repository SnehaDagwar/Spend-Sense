"""Unit and integration tests for Phase 4: Analytics and Dashboard System.

Tests all service aggregations, trend padding, budget zipping, and route handlers.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.category import SpendingCategory
from app.models.budget import MonthlyBudget, BudgetCategoryAllocation
from app.models.expense import Expense
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsFilters,
    SpendingTrendFilters,
    BudgetPerformanceFilters,
    MonthlyComparisonFilters,
)
from app.services.analytics import AnalyticsService


# ---------------------------------------------------------------------------
# Test Fixtures & Mocks
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_user() -> User:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.display_name = "Test User"
    return user


@pytest.fixture
def mock_db() -> Session:
    return MagicMock(spec=Session)


# ---------------------------------------------------------------------------
# Route Handler / Endpoint Integration Tests
# ---------------------------------------------------------------------------

class TestAnalyticsEndpoints:
    """Verifies route protection, routing, and query parameters."""

    @pytest.fixture(autouse=True)
    def setup_app_override(self, mock_user: User, mock_db: Session) -> None:
        """Override current user and DB dependencies for route testing."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        yield
        app.dependency_overrides.clear()

    @patch("app.services.analytics.AnalyticsService.get_summary")
    def test_get_summary_endpoint(self, mock_get_summary: MagicMock) -> None:
        from app.schemas.analytics import SummaryResponse
        mock_get_summary.return_value = SummaryResponse(
            total_spending_current_month=Decimal("0.00"),
            total_spending_custom_range=Decimal("0.00"),
            budget_utilization=Decimal("0.00"),
            remaining_budget=Decimal("0.00"),
            top_categories=[],
            recent_transactions=[],
        )
        client = TestClient(app)

        response = client.get("/api/v1/analytics/summary?month=2026-05")
        assert response.status_code == 200
        mock_get_summary.assert_called_once()
        # Verify filtering parameters passed
        args, kwargs = mock_get_summary.call_args
        assert kwargs["filters"].month == "2026-05"

    @patch("app.services.analytics.AnalyticsService.get_category_breakdown")
    def test_get_category_breakdown_endpoint(
        self, mock_get_breakdown: MagicMock
    ) -> None:
        from app.schemas.analytics import CategoryBreakdownResponse
        mock_get_breakdown.return_value = CategoryBreakdownResponse(items=[])
        client = TestClient(app)

        response = client.get(
            "/api/v1/analytics/category-breakdown?dateFrom=2026-05-01&dateTo=2026-05-15"
        )
        assert response.status_code == 200
        mock_get_breakdown.assert_called_once()
        args, kwargs = mock_get_breakdown.call_args
        assert kwargs["filters"].date_from == date(2026, 5, 1)
        assert kwargs["filters"].date_to == date(2026, 5, 15)

    @patch("app.services.analytics.AnalyticsService.get_spending_trend")
    def test_get_spending_trend_endpoint(self, mock_get_trend: MagicMock) -> None:
        from app.schemas.analytics import SpendingTrendResponse
        mock_get_trend.return_value = SpendingTrendResponse(
            items=[],
            highest_spending_day=None,
            average_daily_spending=Decimal("0.00"),
        )
        client = TestClient(app)

        response = client.get("/api/v1/analytics/spending-trend?interval=weekly")
        assert response.status_code == 200
        mock_get_trend.assert_called_once()
        args, kwargs = mock_get_trend.call_args
        assert kwargs["filters"].interval == "weekly"

    @patch("app.services.analytics.AnalyticsService.get_budget_performance")
    def test_get_budget_performance_endpoint(
        self, mock_get_performance: MagicMock
    ) -> None:
        from app.schemas.analytics import BudgetPerformanceResponse
        mock_get_performance.return_value = BudgetPerformanceResponse(
            budget_id=None,
            month="2026-05",
            income=Decimal("0.00"),
            total_planned=Decimal("0.00"),
            total_spent=Decimal("0.00"),
            remaining=Decimal("0.00"),
            pct_used=Decimal("0.00"),
            is_over_budget=False,
            categories=[],
        )
        client = TestClient(app)

        response = client.get("/api/v1/analytics/budget-performance?month=2026-05")
        assert response.status_code == 200
        mock_get_performance.assert_called_once()

    @patch("app.services.analytics.AnalyticsService.get_monthly_comparison")
    def test_get_monthly_comparison_endpoint(
        self, mock_get_comparison: MagicMock
    ) -> None:
        from app.schemas.analytics import MonthlyComparisonResponse
        mock_get_comparison.return_value = MonthlyComparisonResponse(items=[])
        client = TestClient(app)

        response = client.get("/api/v1/analytics/monthly-comparison?months=12")
        assert response.status_code == 200
        mock_get_comparison.assert_called_once()
        args, kwargs = mock_get_comparison.call_args
        assert kwargs["filters"].months == 12

    def test_invalid_filter_combinations_error(self) -> None:
        client = TestClient(app)
        # Passing both month and date range shortcut is not allowed
        response = client.get(
            "/api/v1/analytics/summary?month=2026-05&dateFrom=2026-05-01"
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Business Service logic Tests
# ---------------------------------------------------------------------------

class TestAnalyticsService:
    """Verifies calculations, padding trend logic, budget mapping, and empty states."""

    def test_summary_calculation_math(
        self, mock_user: User, mock_db: Session
    ) -> None:
        service = AnalyticsService(mock_db)

        # Mock repository returns
        service.repo.get_total_spending = MagicMock(return_value=Decimal("15000.00"))
        
        mock_budget = MagicMock(spec=MonthlyBudget)
        mock_budget.income = Decimal("50000.00")
        service.repo.get_budget_by_month = MagicMock(return_value=mock_budget)

        service.repo.get_spending_by_category = MagicMock(return_value=[])
        service.expense_repo.list_for_user = MagicMock(return_value=([], None))

        filters = AnalyticsFilters(month="2026-05")
        res = service.get_summary(mock_user.id, filters)

        assert res.total_spending_current_month == Decimal("15000.00")
        assert res.total_spending_custom_range == Decimal("15000.00")
        # utilization: 15000 / 50000 * 100 = 30.0%
        assert res.budget_utilization == Decimal("30.00")
        # remaining: 50000 - 15000 = 35000
        assert res.remaining_budget == Decimal("35000.00")

    def test_summary_empty_dataset_graceful_handling(
        self, mock_user: User, mock_db: Session
    ) -> None:
        service = AnalyticsService(mock_db)

        # Mocking empty database aggregates
        service.repo.get_total_spending = MagicMock(return_value=Decimal("0.00"))
        service.repo.get_budget_by_month = MagicMock(return_value=None)
        service.repo.get_spending_by_category = MagicMock(return_value=[])
        service.expense_repo.list_for_user = MagicMock(return_value=([], None))

        filters = AnalyticsFilters(month="2026-05")
        res = service.get_summary(mock_user.id, filters)

        assert res.total_spending_current_month == Decimal("0.00")
        assert res.budget_utilization == Decimal("0.00")
        assert res.remaining_budget == Decimal("0.00")
        assert res.top_categories == []
        assert res.recent_transactions == []

    def test_category_breakdown_percentages(
        self, mock_user: User, mock_db: Session
    ) -> None:
        service = AnalyticsService(mock_db)

        cat1_id = uuid.uuid4()
        cat2_id = uuid.uuid4()

        service.repo.get_total_spending = MagicMock(return_value=Decimal("1000.00"))
        service.repo.get_spending_by_category = MagicMock(
            return_value=[
                (cat1_id, "Food", "food", "icon1", "color1", Decimal("600.00")),
                (cat2_id, "Rent", "rent", "icon2", "color2", Decimal("400.00")),
            ]
        )

        filters = AnalyticsFilters(month="2026-05")
        res = service.get_category_breakdown(mock_user.id, filters)

        assert len(res.items) == 2
        assert res.items[0].name == "Food"
        assert res.items[0].percentage == Decimal("60.00")
        assert res.items[1].name == "Rent"
        assert res.items[1].percentage == Decimal("40.00")

    def test_spending_trend_padded_dates_and_averages(
        self, mock_user: User, mock_db: Session
    ) -> None:
        service = AnalyticsService(mock_db)

        # 3 days of range: May 1 to May 3
        start_date = date(2026, 5, 1)
        end_date = date(2026, 5, 3)

        # Aggregated result only contains spending on May 2
        service.repo.get_spending_trend = MagicMock(
            return_value=[
                (date(2026, 5, 2), Decimal("150.00"), 2),
            ]
        )

        filters = SpendingTrendFilters(
            date_from=start_date, date_to=end_date, interval="daily"
        )
        res = service.get_spending_trend(mock_user.id, filters)

        assert len(res.items) == 3
        
        # Verify padded points
        assert res.items[0].date == date(2026, 5, 1)
        assert res.items[0].total_spent == Decimal("0.00")
        assert res.items[0].transaction_count == 0

        assert res.items[1].date == date(2026, 5, 2)
        assert res.items[1].total_spent == Decimal("150.00")
        assert res.items[1].transaction_count == 2

        assert res.items[2].date == date(2026, 5, 3)
        assert res.items[2].total_spent == Decimal("0.00")

        # Verify averages
        assert res.highest_spending_day == date(2026, 5, 2)
        # Average: 150 / 3 days = 50.00
        assert res.average_daily_spending == Decimal("50.00")

    def test_budget_performance_calculations(
        self, mock_user: User, mock_db: Session
    ) -> None:
        service = AnalyticsService(mock_db)

        # Setup mock entities
        cat_id = uuid.uuid4()
        category = MagicMock(spec=SpendingCategory)
        category.id = cat_id
        category.name = "Food"
        category.slug = "food"
        category.icon = "icon"
        category.color = "color"

        alloc = MagicMock(spec=BudgetCategoryAllocation)
        alloc.category = category
        alloc.planned_amount = Decimal("100.00")

        budget = MagicMock(spec=MonthlyBudget)
        budget.id = uuid.uuid4()
        budget.income = Decimal("1000.00")
        budget.category_allocations = [alloc]

        service.repo.get_budget_by_month = MagicMock(return_value=budget)
        service.repo.get_spending_by_category = MagicMock(
            return_value=[
                (cat_id, "Food", "food", "icon", "color", Decimal("80.00"))
            ]
        )
        service.repo.get_total_spending = MagicMock(return_value=Decimal("80.00"))

        filters = BudgetPerformanceFilters(month="2026-05")
        res = service.get_budget_performance(mock_user.id, filters)

        assert res.income == Decimal("1000.00")
        assert res.total_planned == Decimal("100.00")
        assert res.total_spent == Decimal("80.00")
        assert res.pct_used == Decimal("80.00")
        assert not res.is_over_budget

        # Category performance
        assert len(res.categories) == 1
        assert res.categories[0].actual_spent == Decimal("80.00")
        assert res.categories[0].remaining == Decimal("20.00")
        assert res.categories[0].pct_used == Decimal("80.00")
        assert not res.categories[0].is_over_budget

    def test_monthly_comparison_rates(
        self, mock_user: User, mock_db: Session
    ) -> None:
        service = AnalyticsService(mock_db)

        m1 = date(2026, 5, 1)
        m2 = date(2026, 4, 1)

        b1 = MagicMock(spec=MonthlyBudget)
        b1.month = m1
        b1.income = Decimal("1000.00")
        b1.category_allocations = []

        b2 = MagicMock(spec=MonthlyBudget)
        b2.month = m2
        b2.income = Decimal("2000.00")
        b2.category_allocations = []

        service.repo.get_budgets_for_months = MagicMock(return_value=[b1, b2])
        
        # Spent 300 in May, 600 in April
        def total_spending_mock(user_id, start_date, end_date):
            if start_date.month == 5:
                return Decimal("300.00")
            elif start_date.month == 4:
                return Decimal("600.00")
            return Decimal("0.00")

        service.repo.get_total_spending = MagicMock(side_effect=total_spending_mock)

        filters = MonthlyComparisonFilters(months=2)
        
        # Create a custom class that behaves like date but overrides today
        class MockDate(date):
            @classmethod
            def today(cls):
                return date(2026, 5, 31)

        # Patch date class with our Custom class behavior
        with patch("app.services.analytics.date", MockDate):
            res = service.get_monthly_comparison(mock_user.id, filters)

        assert len(res.items) == 2
        # Chronological sort: April first, then May
        assert res.items[0].month == "2026-04"
        assert res.items[0].income == Decimal("2000.00")
        assert res.items[0].total_spent == Decimal("600.00")
        assert res.items[0].savings == Decimal("1400.00")
        # savings rate: 1400 / 2000 * 100 = 70.00
        assert res.items[0].savings_rate == Decimal("70.00")

        assert res.items[1].month == "2026-05"
        assert res.items[1].income == Decimal("1000.00")
        assert res.items[1].total_spent == Decimal("300.00")
        # savings rate: 700 / 1000 * 100 = 70.00
        assert res.items[1].savings_rate == Decimal("70.00")
