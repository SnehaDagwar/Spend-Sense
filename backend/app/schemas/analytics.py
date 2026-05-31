"""Pydantic schemas for analytics.

Covers request parameters and response models for:
- GET /analytics/summary
- GET /analytics/category-breakdown
- GET /analytics/spending-trend
- GET /analytics/budget-performance
- GET /analytics/monthly-comparison
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import Field, field_validator, model_validator

from app.schemas.base import APIModel
from app.schemas.expense import ExpensePublic


# ---------------------------------------------------------------------------
# Filter Query Schemas
# ---------------------------------------------------------------------------

class AnalyticsFilters(APIModel):
    """Common date range and shortcut month filters for analytics."""

    month: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    date_from: Optional[date] = Field(default=None, alias="dateFrom")
    date_to: Optional[date] = Field(default=None, alias="dateTo")

    @model_validator(mode="after")
    def validate_date_filters(self) -> "AnalyticsFilters":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("dateFrom must be on or before dateTo.")
        if self.month and (self.date_from or self.date_to):
            raise ValueError("Provide either 'month' or 'dateFrom'/'dateTo', not both.")
        return self


class SpendingTrendFilters(AnalyticsFilters):
    """Filters specifically for spending trend endpoint, adding interval."""

    interval: str = Field(default="daily", pattern=r"^(daily|weekly)$")


class BudgetPerformanceFilters(APIModel):
    """Filters for budget performance (only month is supported)."""

    month: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}$")


class MonthlyComparisonFilters(APIModel):
    """Filters for monthly comparison query."""

    months: int = Field(default=6, ge=1, le=12)


# ---------------------------------------------------------------------------
# Response Sub-schemas
# ---------------------------------------------------------------------------

class CategorySpend(APIModel):
    """Item indicating spending detail for one category."""

    category_id: uuid.UUID
    name: str
    slug: str
    icon: str
    color: str
    total_spent: Decimal
    percentage: Decimal = Field(
        description="Percentage of total spent in this group (0–100)."
    )


class SpendingTrendItem(APIModel):
    """Day/Week point in a spending trend chart."""

    date: date
    total_spent: Decimal
    transaction_count: int


class BudgetPerformanceCategory(APIModel):
    """Allocated category spending analysis in a budget."""

    category_id: uuid.UUID
    name: str
    slug: str
    icon: str
    color: str
    planned_amount: Decimal
    actual_spent: Decimal
    remaining: Decimal
    pct_used: Decimal = Field(
        description="Percentage of planned budget used (0–100+). 0 if planned is 0."
    )
    is_over_budget: bool


class MonthlyComparisonItem(APIModel):
    """Comparison item for monthly analytics."""

    month: str = Field(description="YYYY-MM format.")
    income: Decimal
    total_planned: Decimal
    total_spent: Decimal
    savings: Decimal
    savings_rate: Decimal = Field(
        description="Savings rate as percentage of income (0-100)."
    )


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class SummaryResponse(APIModel):
    """Response returned by GET /analytics/summary."""

    total_spending_current_month: Decimal
    total_spending_custom_range: Decimal
    budget_utilization: Decimal = Field(
        description="Percentage of income spent (0-100+)."
    )
    remaining_budget: Decimal
    top_categories: list[CategorySpend]
    recent_transactions: list[ExpensePublic]


class CategoryBreakdownResponse(APIModel):
    """Response returned by GET /analytics/category-breakdown."""

    items: list[CategorySpend]


class SpendingTrendResponse(APIModel):
    """Response returned by GET /analytics/spending-trend."""

    items: list[SpendingTrendItem]
    highest_spending_day: Optional[date] = None
    average_daily_spending: Decimal


class BudgetPerformanceResponse(APIModel):
    """Response returned by GET /analytics/budget-performance."""

    budget_id: Optional[uuid.UUID] = None
    month: str = Field(description="YYYY-MM format.")
    income: Decimal
    total_planned: Decimal
    total_spent: Decimal
    remaining: Decimal
    pct_used: Decimal = Field(
        description="Percentage of planned budget used (0-100+)."
    )
    is_over_budget: bool
    categories: list[BudgetPerformanceCategory]


class MonthlyComparisonResponse(APIModel):
    """Response returned by GET /analytics/monthly-comparison."""

    items: list[MonthlyComparisonItem]
