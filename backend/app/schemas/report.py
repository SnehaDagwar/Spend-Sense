"""Pydantic schemas for Reports and Exports.

Covers filters, monthly reports, category summaries, budget breakdowns, and goals.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import Field, model_validator

from app.schemas.base import APIModel
from app.schemas.analytics import BudgetPerformanceCategory
from app.schemas.goal import GoalPublic


# ---------------------------------------------------------------------------
# Filter Query Schemas
# ---------------------------------------------------------------------------

class ReportFilters(APIModel):
    """Query filters for reports and exports endpoints."""

    month: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    date_from: Optional[date] = Field(default=None, alias="dateFrom")
    date_to: Optional[date] = Field(default=None, alias="dateTo")
    category_id: Optional[uuid.UUID] = Field(default=None, alias="categoryId")

    @model_validator(mode="after")
    def validate_filters(self) -> "ReportFilters":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("dateFrom must be on or before dateTo.")
        if self.month and (self.date_from or self.date_to):
            raise ValueError("Provide either 'month' or 'dateFrom'/'dateTo', not both.")
        return self


# ---------------------------------------------------------------------------
# Report Response Schemas
# ---------------------------------------------------------------------------

class MonthlyReportResponse(APIModel):
    """Detailed response for GET /reports/monthly."""

    month: str = Field(description="YYYY-MM format.")
    income: Decimal
    total_planned: Decimal
    total_spent: Decimal
    savings: Decimal
    savings_rate: Decimal = Field(description="Savings rate as percentage of income (0-100).")
    categories: list[BudgetPerformanceCategory] = Field(
        description="Budget categories planned vs actual performance breakdown."
    )


class CategoryReportItem(APIModel):
    """Detailed spending item for category report."""

    category_id: uuid.UUID
    name: str
    slug: str
    icon: str
    color: str
    total_spent: Decimal
    percentage: Decimal = Field(description="Percentage of total spent across all categories.")
    transaction_count: int = Field(description="Number of transactions in this category.")
    average_transaction_amount: Decimal = Field(description="Average transaction size in this category.")


class CategoryReportResponse(APIModel):
    """Response returned by GET /reports/categories."""

    total_spending: Decimal
    items: list[CategoryReportItem]


class GoalReportResponse(APIModel):
    """Response returned by GET /reports/goals."""

    items: list[GoalPublic]
