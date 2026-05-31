"""Service for analytics and dashboard metrics.

Implements date expansions, trend filling, and entity zipping.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from app.repositories.analytics import AnalyticsRepository
from app.repositories.expense import ExpenseRepository
from app.schemas.analytics import (
    AnalyticsFilters,
    BudgetPerformanceCategory,
    BudgetPerformanceFilters,
    BudgetPerformanceResponse,
    CategorySpend,
    CategoryBreakdownResponse,
    MonthlyComparisonFilters,
    MonthlyComparisonItem,
    MonthlyComparisonResponse,
    SpendingTrendFilters,
    SpendingTrendItem,
    SpendingTrendResponse,
    SummaryResponse,
)
from app.schemas.expense import ExpensePublic


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_year_month(value: str) -> date:
    """Parse 'YYYY-MM' and return the first day of that month as a date."""
    year, month = int(value[:4]), int(value[5:7])
    return date(year, month, 1)


def _month_date_range(month: str) -> tuple[date, date]:
    """Return (first_day, last_day) for a YYYY-MM string."""
    year, mon = int(month[:4]), int(month[5:7])
    first = date(year, mon, 1)
    if mon == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, mon + 1, 1) - timedelta(days=1)
    return first, last


def _month_last_day(month_start: date) -> date:
    """Return the last day of the month given its first day."""
    year, mon = month_start.year, month_start.month
    if mon == 12:
        return date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, mon + 1, 1) - timedelta(days=1)


def _get_current_month_range() -> tuple[date, date]:
    """Return (first_day, last_day) for the current calendar month."""
    today = date.today()
    first = date(today.year, today.month, 1)
    return first, _month_last_day(first)


def _get_date_list(start: date, end: date) -> list[date]:
    """Return a list of all dates between start and end inclusive."""
    dates: list[date] = []
    curr = start
    while curr <= end:
        dates.append(curr)
        curr += timedelta(days=1)
    return dates


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AnalyticsService:
    """Business service for compiling Spend Sense financial analytics."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AnalyticsRepository(db)
        self.expense_repo = ExpenseRepository(db)

    def get_summary(
        self,
        user_id: uuid.UUID,
        filters: AnalyticsFilters,
    ) -> SummaryResponse:
        """Fetch dashboard summary metrics."""
        # 1. Date resolution
        cur_start, cur_end = _get_current_month_range()

        if filters.month:
            target_start, target_end = _month_date_range(filters.month)
        elif filters.date_from and filters.date_to:
            target_start, target_end = filters.date_from, filters.date_to
        else:
            target_start, target_end = cur_start, cur_end

        # 2. Query spends
        total_spending_current_month = self.repo.get_total_spending(
            user_id, cur_start, cur_end
        )
        total_spending_custom_range = self.repo.get_total_spending(
            user_id, target_start, target_end
        )

        # 3. Query budget & compute utilization/remaining
        target_budget_month = target_start.replace(day=1)
        budget = self.repo.get_budget_by_month(user_id, target_budget_month)

        if budget is not None:
            income = budget.income
            remaining_budget = income - total_spending_custom_range
            if income > 0:
                budget_utilization = (total_spending_custom_range / income) * 100
            else:
                budget_utilization = Decimal("0.00")
        else:
            income = Decimal("0.00")
            remaining_budget = Decimal("0.00")
            budget_utilization = Decimal("0.00")

        # 4. Top spending categories
        cat_spends = self.repo.get_spending_by_category(
            user_id, target_start, target_end
        )
        top_categories_list: list[CategorySpend] = []
        for cat_id, name, slug, icon, color, spent in cat_spends:
            pct = (
                (spent / total_spending_custom_range) * 100
                if total_spending_custom_range > 0
                else Decimal("0.00")
            )
            top_categories_list.append(
                CategorySpend(
                    category_id=cat_id,
                    name=name,
                    slug=slug,
                    icon=icon,
                    color=color,
                    total_spent=spent,
                    percentage=pct,
                )
            )
        # Limit dashboard view to top 5 categories
        top_categories_list = top_categories_list[:5]

        # 5. Recent transactions
        recent_expenses, _ = self.expense_repo.list_for_user(
            user_id=user_id, limit=5
        )
        recent_list = [ExpensePublic.model_validate(e) for e in recent_expenses]

        return SummaryResponse(
            total_spending_current_month=total_spending_current_month,
            total_spending_custom_range=total_spending_custom_range,
            budget_utilization=budget_utilization,
            remaining_budget=remaining_budget,
            top_categories=top_categories_list,
            recent_transactions=recent_list,
        )

    def get_category_breakdown(
        self,
        user_id: uuid.UUID,
        filters: AnalyticsFilters,
    ) -> CategoryBreakdownResponse:
        """Compile percentage breakdown of spending by category."""
        # 1. Date resolution
        if filters.month:
            target_start, target_end = _month_date_range(filters.month)
        elif filters.date_from and filters.date_to:
            target_start, target_end = filters.date_from, filters.date_to
        else:
            target_start, target_end = _get_current_month_range()

        # 2. Get totals and categories
        total_spending = self.repo.get_total_spending(
            user_id, target_start, target_end
        )
        cat_spends = self.repo.get_spending_by_category(
            user_id, target_start, target_end
        )

        items: list[CategorySpend] = []
        for cat_id, name, slug, icon, color, spent in cat_spends:
            pct = (
                (spent / total_spending) * 100
                if total_spending > 0
                else Decimal("0.00")
            )
            items.append(
                CategorySpend(
                    category_id=cat_id,
                    name=name,
                    slug=slug,
                    icon=icon,
                    color=color,
                    total_spent=spent,
                    percentage=pct,
                )
            )

        return CategoryBreakdownResponse(items=items)

    def get_spending_trend(
        self,
        user_id: uuid.UUID,
        filters: SpendingTrendFilters,
    ) -> SpendingTrendResponse:
        """Compile spending aggregates daily or weekly."""
        # 1. Date resolution
        if filters.month:
            target_start, target_end = _month_date_range(filters.month)
        elif filters.date_from and filters.date_to:
            target_start, target_end = filters.date_from, filters.date_to
        else:
            target_start, target_end = _get_current_month_range()

        # 2. Get database daily spending trend
        db_trend = self.repo.get_spending_trend(
            user_id, target_start, target_end
        )
        db_trend_map = {d: (spent, count) for d, spent, count in db_trend}

        # 3. Premium feature: pad missing dates to ensure smooth charts
        full_dates = _get_date_list(target_start, target_end)
        padded_daily_items: list[SpendingTrendItem] = []

        total_spent_sum = Decimal("0.00")
        highest_day: Optional[date] = None
        highest_amount = Decimal("0.00")

        for d in full_dates:
            spent, count = db_trend_map.get(d, (Decimal("0.00"), 0))
            padded_daily_items.append(
                SpendingTrendItem(
                    date=d,
                    total_spent=spent,
                    transaction_count=count,
                )
            )
            total_spent_sum += spent
            if spent > highest_amount:
                highest_amount = spent
                highest_day = d

        # Calculate average daily spending
        days_count = len(full_dates)
        avg_daily = (
            total_spent_sum / Decimal(str(days_count))
            if days_count > 0
            else Decimal("0.00")
        )

        # 4. Handle interval grouping
        if filters.interval == "weekly":
            # Group daily items by week start date (ISO week, starts Monday)
            weekly_map: dict[date, tuple[Decimal, int]] = {}
            for item in padded_daily_items:
                # Find start of the week (Monday)
                week_start = item.date - timedelta(days=item.date.weekday())
                existing_spent, existing_count = weekly_map.get(
                    week_start, (Decimal("0.00"), 0)
                )
                weekly_map[week_start] = (
                    existing_spent + item.total_spent,
                    existing_count + item.transaction_count,
                )

            # Sort weeks chronologically
            weekly_items: list[SpendingTrendItem] = []
            for w_start in sorted(weekly_map.keys()):
                spent, count = weekly_map[w_start]
                weekly_items.append(
                    SpendingTrendItem(
                        date=w_start,
                        total_spent=spent,
                        transaction_count=count,
                    )
                )
            trend_items = weekly_items
        else:
            trend_items = padded_daily_items

        return SpendingTrendResponse(
            items=trend_items,
            highest_spending_day=highest_day,
            average_daily_spending=avg_daily,
        )

    def get_budget_performance(
        self,
        user_id: uuid.UUID,
        filters: BudgetPerformanceFilters,
    ) -> BudgetPerformanceResponse:
        """Compare planned allocations against actual spends for a month."""
        # 1. Date resolution
        if filters.month:
            month_start = _parse_year_month(filters.month)
        else:
            today = date.today()
            month_start = date(today.year, today.month, 1)

        month_end = _month_last_day(month_start)
        month_str = month_start.strftime("%Y-%m")

        # 2. Query budget + actual spends
        budget = self.repo.get_budget_by_month(user_id, month_start)
        actual_spends = self.repo.get_spending_by_category(
            user_id, month_start, month_end
        )
        actual_spend_map = {
            cat_id: spent for cat_id, _, _, _, _, spent in actual_spends
        }

        # Calculate overall actual spent for the month
        overall_actual_spent = self.repo.get_total_spending(
            user_id, month_start, month_end
        )

        categories_perf: list[BudgetPerformanceCategory] = []

        if budget is None:
            # Empty dataset handles gracefully
            return BudgetPerformanceResponse(
                budget_id=None,
                month=month_str,
                income=Decimal("0.00"),
                total_planned=Decimal("0.00"),
                total_spent=overall_actual_spent,
                remaining=Decimal("0.00"),
                pct_used=Decimal("0.00"),
                is_over_budget=False,
                categories=[],
            )

        # 3. Zip planned with actual
        total_planned = Decimal("0.00")
        for alloc in budget.category_allocations:
            cat = alloc.category
            planned = alloc.planned_amount
            total_planned += planned

            actual = actual_spend_map.get(cat.id, Decimal("0.00"))
            remaining = planned - actual
            pct = (actual / planned) * 100 if planned > 0 else Decimal("0.00")
            over = actual > planned

            categories_perf.append(
                BudgetPerformanceCategory(
                    category_id=cat.id,
                    name=cat.name,
                    slug=cat.slug,
                    icon=cat.icon,
                    color=cat.color,
                    planned_amount=planned,
                    actual_spent=actual,
                    remaining=remaining,
                    pct_used=pct,
                    is_over_budget=over,
                )
            )

        # Budget level analytics
        remaining = budget.income - overall_actual_spent
        pct_used = (
            (overall_actual_spent / total_planned) * 100
            if total_planned > 0
            else Decimal("0.00")
        )
        is_over_budget = overall_actual_spent > total_planned

        return BudgetPerformanceResponse(
            budget_id=budget.id,
            month=month_str,
            income=budget.income,
            total_planned=total_planned,
            total_spent=overall_actual_spent,
            remaining=remaining,
            pct_used=pct_used,
            is_over_budget=is_over_budget,
            categories=categories_perf,
        )

    def get_monthly_comparison(
        self,
        user_id: uuid.UUID,
        filters: MonthlyComparisonFilters,
    ) -> MonthlyComparisonResponse:
        """Fetch comparative savings stats for past N months."""
        # 1. Resolve past N months
        today = date.today()
        current_first = date(today.year, today.month, 1)

        months_list: list[date] = []
        for i in range(filters.months):
            # Calculate past month starting date
            # Subtract month by rolling back the year/month manually
            year = current_first.year
            month = current_first.month - i
            while month <= 0:
                month += 12
                year -= 1
            months_list.append(date(year, month, 1))

        # Reverse to chronological order (oldest to newest)
        months_list.reverse()

        # 2. Bulk fetch budgets to avoid N+1 queries
        budgets = self.repo.get_budgets_for_months(user_id, months_list)
        budget_map = {b.month: b for b in budgets}

        # 3. For each month, calculate planned, income, spent
        items: list[MonthlyComparisonItem] = []
        for m_start in months_list:
            m_end = _month_last_day(m_start)
            m_str = m_start.strftime("%Y-%m")

            # Spent
            spent = self.repo.get_total_spending(user_id, m_start, m_end)

            # Budget details
            budget = budget_map.get(m_start)
            if budget is not None:
                income = budget.income
                planned = sum(
                    alloc.planned_amount for alloc in budget.category_allocations
                )
            else:
                income = Decimal("0.00")
                planned = Decimal("0.00")

            # Savings metrics
            savings = income - spent
            savings_rate = (
                (savings / income) * 100 if income > 0 else Decimal("0.00")
            )

            items.append(
                MonthlyComparisonItem(
                    month=m_str,
                    income=income,
                    total_planned=planned,
                    total_spent=spent,
                    savings=savings,
                    savings_rate=savings_rate,
                )
            )

        return MonthlyComparisonResponse(items=items)
