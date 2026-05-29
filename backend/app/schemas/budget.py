"""Pydantic schemas for budget management.

Covers:
- Request bodies: BudgetCreate, BudgetUpdate, AllocationUpsert
- Query parameters: BudgetFilters
- Response models: AllocationAnalytics, BudgetAnalytics,
                   AllocationPublic, BudgetPublic,
                   BudgetListItem, BudgetListResponse
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import Field, field_validator, model_validator

from app.schemas.base import APIModel
from app.schemas.category import CategoryPublic


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_year_month(value: str) -> date:
    """Parse a 'YYYY-MM' string and return the first day of that month as a date.

    Raises ValueError for invalid months (e.g. '2026-13').
    """
    try:
        year, month = int(value[:4]), int(value[5:7])
        return date(year, month, 1)
    except (ValueError, IndexError) as exc:
        raise ValueError(f"Invalid month format: {value!r}. Expected YYYY-MM.") from exc


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class AllocationUpsert(APIModel):
    """One category allocation entry inside a BudgetCreate or standalone upsert."""

    category_id: uuid.UUID
    planned_amount: Annotated[
        Decimal, Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    ] = Decimal("0")
    display_order: Annotated[int, Field(ge=0, le=32767)] = 0


class BudgetCreate(APIModel):
    """Payload for POST /budgets.

    ``month`` must be YYYY-MM format.  Only one budget per month is allowed;
    attempting to create a duplicate raises 409.

    When ``rollover`` is True, allocations from the previous calendar month
    are copied in as defaults before applying the supplied ``categories`` list.
    """

    month: Annotated[str, Field(pattern=r"^\d{4}-\d{2}$")]
    income: Annotated[
        Decimal, Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    ] = Decimal("0")
    warning_threshold: Annotated[
        Decimal,
        Field(
            ge=Decimal("0"),
            le=Decimal("1"),
            max_digits=5,
            decimal_places=4,
            description="Warning level as a fraction 0–1 (default 0.80 = 80 %).",
        ),
    ] = Decimal("0.8000")
    categories: list[AllocationUpsert] = []
    rollover: bool = False

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: str) -> str:
        """Validate that the month string represents a real calendar month."""
        _parse_year_month(v)  # raises ValueError if invalid
        return v

    @model_validator(mode="after")
    def no_duplicate_categories(self) -> "BudgetCreate":
        ids = [a.category_id for a in self.categories]
        if len(ids) != len(set(ids)):
            raise ValueError(
                "Duplicate category IDs in the categories list are not allowed."
            )
        return self


class BudgetUpdate(APIModel):
    """Payload for PATCH /budgets/{budget_id}.

    All fields are optional; at least one must be provided.
    """

    income: Annotated[
        Optional[Decimal],
        Field(default=None, ge=Decimal("0"), max_digits=14, decimal_places=2),
    ] = None
    warning_threshold: Annotated[
        Optional[Decimal],
        Field(
            default=None,
            ge=Decimal("0"),
            le=Decimal("1"),
            max_digits=5,
            decimal_places=4,
        ),
    ] = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "BudgetUpdate":
        if self.income is None and self.warning_threshold is None:
            raise ValueError("At least one field must be provided for an update.")
        return self


# ---------------------------------------------------------------------------
# Query-parameter model
# ---------------------------------------------------------------------------

class BudgetFilters(APIModel):
    """Query parameters accepted by GET /budgets."""

    from_month: Optional[str] = Field(
        default=None,
        alias="from",
        pattern=r"^\d{4}-\d{2}$",
        description="Start month (YYYY-MM), inclusive.",
    )
    to_month: Optional[str] = Field(
        default=None,
        alias="to",
        pattern=r"^\d{4}-\d{2}$",
        description="End month (YYYY-MM), inclusive.",
    )
    category_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Filter: only return budgets that include this category allocation.",
    )
    active_only: bool = Field(
        default=False,
        description="When true, restrict to the current calendar month.",
    )

    @model_validator(mode="after")
    def validate_range(self) -> "BudgetFilters":
        if self.from_month and self.to_month:
            start = _parse_year_month(self.from_month)
            end = _parse_year_month(self.to_month)
            if start > end:
                raise ValueError("'from' must be on or before 'to'.")
        return self

    def from_date(self) -> Optional[date]:
        return _parse_year_month(self.from_month) if self.from_month else None

    def to_date(self) -> Optional[date]:
        return _parse_year_month(self.to_month) if self.to_month else None


# ---------------------------------------------------------------------------
# Analytics sub-schemas (embedded in responses)
# ---------------------------------------------------------------------------

class AllocationAnalytics(APIModel):
    """Per-category spending analytics for a budget allocation."""

    spent: Decimal
    remaining: Decimal
    pct_used: Decimal = Field(
        description="Spending as a percentage of planned (0–100+). 0 if planned is 0."
    )
    is_over_budget: bool
    is_near_limit: bool = Field(
        description="True when pct_used >= warning_threshold * 100 and not over budget."
    )


class BudgetAnalytics(APIModel):
    """Month-level budget analytics."""

    total_planned: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    pct_used: Decimal = Field(
        description="Total spent as percentage of total planned (0–100+)."
    )
    projected_spend: Decimal = Field(
        description=(
            "Projected month-end spend extrapolated from spend rate so far. "
            "0 for future months with no spending."
        )
    )
    is_over_budget: bool


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class AllocationPublic(APIModel):
    """One category allocation row as returned by the API."""

    id: uuid.UUID
    category_id: uuid.UUID
    category: CategoryPublic
    planned_amount: Decimal
    display_order: int
    analytics: AllocationAnalytics
    created_at: datetime
    updated_at: datetime


class BudgetPublic(APIModel):
    """Full budget response including allocations and analytics."""

    id: uuid.UUID
    month: str = Field(description="YYYY-MM format.")
    income: Decimal
    warning_threshold: Decimal
    categories: list[AllocationPublic]
    analytics: BudgetAnalytics
    created_at: datetime
    updated_at: datetime


class BudgetListItem(APIModel):
    """Lightweight budget summary for the list endpoint (no per-allocation analytics)."""

    id: uuid.UUID
    month: str = Field(description="YYYY-MM format.")
    income: Decimal
    warning_threshold: Decimal
    allocation_count: int
    total_planned: Decimal
    total_spent: Decimal
    is_over_budget: bool
    created_at: datetime
    updated_at: datetime


class BudgetListResponse(APIModel):
    """Envelope for GET /budgets."""

    items: list[BudgetListItem]
    total_returned: int
