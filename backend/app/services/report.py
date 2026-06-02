"""Service for compiling financial reports.

Integrates with repository, analytics, and goals services.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.report import ReportRepository
from app.repositories.analytics import AnalyticsRepository
from app.schemas.analytics import BudgetPerformanceFilters, BudgetPerformanceResponse
from app.schemas.report import (
    CategoryReportItem,
    CategoryReportResponse,
    GoalReportResponse,
    MonthlyReportResponse,
    ReportFilters,
)
from app.services.analytics import AnalyticsService
from app.services.goal import GoalService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _month_date_range(month: str) -> tuple[date, date]:
    """Return (first_day, last_day) for a YYYY-MM string."""
    year, mon = int(month[:4]), int(month[5:7])
    first = date(year, mon, 1)
    if mon == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, mon + 1, 1) - timedelta(days=1)
    return first, last


def _resolve_dates(filters: ReportFilters) -> tuple[date, date]:
    """Resolve start and end dates from report filters, defaulting to current month."""
    if filters.month:
        return _month_date_range(filters.month)
    elif filters.date_from and filters.date_to:
        return filters.date_from, filters.date_to
    else:
        # Default to current month
        today = date.today()
        month_str = today.strftime("%Y-%m")
        return _month_date_range(month_str)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class ReportService:
    """Orchestrates compilation of reports from multiple domain entities."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.report_repo = ReportRepository(db)
        self.analytics_service = AnalyticsService(db)
        self.goal_service = GoalService(db)

    def get_monthly_report(self, user_id: uuid.UUID, filters: ReportFilters) -> MonthlyReportResponse:
        """Compile overall monthly spending and budget performance report."""
        # 1. Resolve target month string
        if filters.month:
            month_str = filters.month
        elif filters.date_from:
            month_str = filters.date_from.strftime("%Y-%m")
        else:
            month_str = date.today().strftime("%Y-%m")

        # 2. Get budget performance details
        bp_filters = BudgetPerformanceFilters(month=month_str)
        perf: BudgetPerformanceResponse = self.analytics_service.get_budget_performance(
            user_id=user_id, filters=bp_filters
        )

        # 3. Calculate savings metrics
        savings = perf.income - perf.total_spent
        savings_rate = (
            (savings / perf.income) * 100
            if perf.income > 0
            else Decimal("0.00")
        )

        return MonthlyReportResponse(
            month=month_str,
            income=perf.income,
            total_planned=perf.total_planned,
            total_spent=perf.total_spent,
            savings=savings,
            savings_rate=savings_rate,
            categories=perf.categories,
        )

    def get_category_report(self, user_id: uuid.UUID, filters: ReportFilters) -> CategoryReportResponse:
        """Compile a highly detailed category spending report."""
        start_date, end_date = _resolve_dates(filters)

        # Query database aggregates
        db_items = self.report_repo.get_category_spending_report(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            category_id=filters.category_id,
        )

        # Calculate overall total spending in this report
        total_spending = sum(item[5] for item in db_items)

        items: list[CategoryReportItem] = []
        for cat_id, name, slug, icon, color, spent, count, avg_spent in db_items:
            pct = (
                (spent / total_spending) * 100
                if total_spending > 0
                else Decimal("0.00")
            )
            items.append(
                CategoryReportItem(
                    category_id=cat_id,
                    name=name,
                    slug=slug,
                    icon=icon,
                    color=color,
                    total_spent=spent,
                    percentage=pct,
                    transaction_count=count,
                    average_transaction_amount=avg_spent,
                )
            )

        return CategoryReportResponse(total_spending=total_spending, items=items)

    def get_budget_report(self, user_id: uuid.UUID, filters: ReportFilters) -> BudgetPerformanceResponse:
        """Get the budget performance report (direct analytical comparison)."""
        # Resolve target month
        if filters.month:
            month_str = filters.month
        elif filters.date_from:
            month_str = filters.date_from.strftime("%Y-%m")
        else:
            month_str = date.today().strftime("%Y-%m")

        bp_filters = BudgetPerformanceFilters(month=month_str)
        return self.analytics_service.get_budget_performance(user_id=user_id, filters=bp_filters)

    def get_goal_report(self, user_id: uuid.UUID) -> GoalReportResponse:
        """Fetch status and progress for all savings goals."""
        goals = self.goal_service.list_goals(user_id=user_id)
        return GoalReportResponse(items=goals)
