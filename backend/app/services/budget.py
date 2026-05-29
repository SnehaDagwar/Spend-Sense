"""Budget service.

Owns all business rules for monthly budgets and category allocations:
- One budget per user per month (duplicate prevention)
- Category must be visible and non-archived
- Rollover: copy prior month's allocations as defaults
- Spending progress analytics computed on read (2 queries total)
- Warning threshold and overspending detection
- Projected month-end spending extrapolation
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.budget import BudgetCategoryAllocation, MonthlyBudget
from app.repositories.budget import BudgetRepository, _month_last_day
from app.repositories.category import CategoryRepository
from app.schemas.budget import (
    AllocationAnalytics,
    AllocationPublic,
    AllocationUpsert,
    BudgetAnalytics,
    BudgetCreate,
    BudgetFilters,
    BudgetListItem,
    BudgetPublic,
    BudgetUpdate,
)
from app.schemas.category import CategoryPublic


# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------

class BudgetServiceError(Exception):
    """Base for budget service errors."""


class BudgetNotFoundError(BudgetServiceError):
    """Raised when the budget does not exist or is not owned by the user."""


class BudgetConflictError(BudgetServiceError):
    """Raised when a budget already exists for the given user+month."""


class BudgetCategoryError(BudgetServiceError):
    """Raised when a referenced category is not accessible or is archived."""


class BudgetValidationError(BudgetServiceError):
    """Raised for invalid month strings or other payload issues."""


# ---------------------------------------------------------------------------
# Analytics helpers (pure Python, no DB)
# ---------------------------------------------------------------------------

def _compute_allocation_analytics(
    alloc: BudgetCategoryAllocation,
    spending_map: dict[uuid.UUID, Decimal],
    warning_threshold: Decimal,
) -> AllocationAnalytics:
    """Compute per-allocation analytics from the spending map."""
    planned = alloc.planned_amount
    spent = spending_map.get(alloc.category_id, Decimal("0"))
    remaining = max(planned - spent, Decimal("0"))

    if planned > Decimal("0"):
        pct_used = (spent / planned * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        pct_used = Decimal("100.00") if spent > Decimal("0") else Decimal("0.00")

    is_over = spent > planned
    is_near = not is_over and pct_used >= warning_threshold * Decimal("100")

    return AllocationAnalytics(
        spent=spent,
        remaining=remaining,
        pct_used=pct_used,
        is_over_budget=is_over,
        is_near_limit=is_near,
    )


def _compute_budget_analytics(
    budget: MonthlyBudget,
    spending_map: dict[uuid.UUID, Decimal],
) -> BudgetAnalytics:
    """Compute month-level analytics from the budget and spending map."""
    total_planned = sum(
        (a.planned_amount for a in budget.category_allocations), Decimal("0")
    )
    total_spent = sum(spending_map.values(), Decimal("0"))
    total_remaining = max(total_planned - total_spent, Decimal("0"))

    if total_planned > Decimal("0"):
        pct_used = (total_spent / total_planned * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        pct_used = Decimal("100.00") if total_spent > Decimal("0") else Decimal("0.00")

    is_over = total_spent > total_planned

    # Projected month-end spending
    today = date.today()
    month_start = budget.month  # already a date (first day)
    month_end = _month_last_day(month_start)
    days_in_month = (month_end - month_start).days + 1

    if today < month_start:
        # Future month — no spending yet, projection is 0
        projected = Decimal("0")
    else:
        days_elapsed = min((today - month_start).days + 1, days_in_month)
        if days_elapsed > 0 and total_spent > Decimal("0"):
            projected = (total_spent / Decimal(days_elapsed)) * Decimal(days_in_month)
            projected = projected.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            projected = Decimal("0")

    return BudgetAnalytics(
        total_planned=total_planned,
        total_spent=total_spent,
        total_remaining=total_remaining,
        pct_used=pct_used,
        projected_spend=projected,
        is_over_budget=is_over,
    )


def _month_date_to_str(month_date: date) -> str:
    """Convert a first-of-month date to YYYY-MM string."""
    return month_date.strftime("%Y-%m")


def _prev_month(month_date: date) -> date:
    """Return the first day of the previous calendar month."""
    if month_date.month == 1:
        return date(month_date.year - 1, 12, 1)
    return date(month_date.year, month_date.month - 1, 1)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class BudgetService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = BudgetRepository(db)
        self.categories = CategoryRepository(db)

    # ------------------------------------------------------------------
    # Internal: analytics assembly
    # ------------------------------------------------------------------

    def _spending_map(self, user_id: uuid.UUID, budget: MonthlyBudget) -> dict[uuid.UUID, Decimal]:
        """Fetch the spending aggregate for a budget month. One query."""
        month_end = _month_last_day(budget.month)
        return self.repo.get_spending_by_category(
            user_id=user_id,
            month_start=budget.month,
            month_end=month_end,
        )

    def _build_allocation_public(
        self,
        alloc: BudgetCategoryAllocation,
        spending_map: dict[uuid.UUID, Decimal],
        warning_threshold: Decimal,
    ) -> AllocationPublic:
        analytics = _compute_allocation_analytics(alloc, spending_map, warning_threshold)
        return AllocationPublic(
            id=alloc.id,
            category_id=alloc.category_id,
            category=CategoryPublic.model_validate(alloc.category),
            planned_amount=alloc.planned_amount,
            display_order=alloc.display_order,
            analytics=analytics,
            created_at=alloc.created_at,
            updated_at=alloc.updated_at,
        )

    def _build_budget_public(
        self,
        budget: MonthlyBudget,
        spending_map: dict[uuid.UUID, Decimal],
    ) -> BudgetPublic:
        allocations = [
            self._build_allocation_public(a, spending_map, budget.warning_threshold)
            for a in budget.category_allocations
        ]
        analytics = _compute_budget_analytics(budget, spending_map)
        return BudgetPublic(
            id=budget.id,
            month=_month_date_to_str(budget.month),
            income=budget.income,
            warning_threshold=budget.warning_threshold,
            categories=allocations,
            analytics=analytics,
            created_at=budget.created_at,
            updated_at=budget.updated_at,
        )

    def _build_list_item(
        self,
        budget: MonthlyBudget,
        spending_map: dict[uuid.UUID, Decimal],
    ) -> BudgetListItem:
        total_planned = sum(
            (a.planned_amount for a in budget.category_allocations), Decimal("0")
        )
        total_spent = sum(spending_map.values(), Decimal("0"))
        is_over = total_spent > total_planned if total_planned > Decimal("0") else False
        return BudgetListItem(
            id=budget.id,
            month=_month_date_to_str(budget.month),
            income=budget.income,
            warning_threshold=budget.warning_threshold,
            allocation_count=len(budget.category_allocations),
            total_planned=total_planned,
            total_spent=total_spent,
            is_over_budget=is_over,
            created_at=budget.created_at,
            updated_at=budget.updated_at,
        )

    # ------------------------------------------------------------------
    # Internal: category validation
    # ------------------------------------------------------------------

    def _validate_categories(
        self, user_id: uuid.UUID, items: list[AllocationUpsert]
    ) -> None:
        """Validate that each category is visible and non-archived.

        Raises BudgetCategoryError on the first violation.
        """
        for item in items:
            cat = self.categories.get_by_id_for_user(item.category_id, user_id)
            if cat is None:
                raise BudgetCategoryError(
                    f"Category {item.category_id} not found or not accessible."
                )
            if cat.is_archived:
                raise BudgetCategoryError(
                    f"Category '{cat.name}' is archived and cannot receive an allocation."
                )

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def list_budgets(
        self,
        *,
        user_id: uuid.UUID,
        filters: BudgetFilters,
    ) -> list[BudgetListItem]:
        """Return lightweight budget list items for the given filters.

        Each item includes month-level totals computed from a spending aggregate
        query per budget. For large month ranges this could be many queries, but
        in practice users have at most 12–24 budget months.
        """
        today = date.today()
        from_date = filters.from_date()
        to_date = filters.to_date()

        if filters.active_only:
            from_date = date(today.year, today.month, 1)
            to_date = from_date

        budgets = self.repo.list_for_user(
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            category_id=filters.category_id,
        )

        items = []
        for budget in budgets:
            spending_map = self._spending_map(user_id, budget)
            items.append(self._build_list_item(budget, spending_map))
        return items

    # ------------------------------------------------------------------
    # Single-record get
    # ------------------------------------------------------------------

    def get_budget(
        self,
        *,
        user_id: uuid.UUID,
        budget_id: uuid.UUID,
    ) -> BudgetPublic:
        budget = self.repo.get_by_id_and_user(budget_id, user_id)
        if budget is None:
            raise BudgetNotFoundError(f"Budget {budget_id} not found.")

        spending_map = self._spending_map(user_id, budget)
        return self._build_budget_public(budget, spending_map)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_budget(
        self,
        *,
        user_id: uuid.UUID,
        payload: BudgetCreate,
    ) -> BudgetPublic:
        """Create a new monthly budget.

        Raises:
            BudgetValidationError: Invalid month string.
            BudgetConflictError: A budget for that month already exists.
            BudgetCategoryError: Any referenced category is invalid/archived.
        """
        from app.schemas.budget import _parse_year_month

        try:
            month_date = _parse_year_month(payload.month)
        except ValueError as exc:
            raise BudgetValidationError(str(exc)) from exc

        # Pre-check for duplicate (friendly 409 before DB constraint fires)
        existing = self.repo.get_by_month_and_user(month_date, user_id)
        if existing is not None:
            raise BudgetConflictError(
                f"A budget for {payload.month} already exists (id={existing.id})."
            )

        # Validate categories before any DB write
        self._validate_categories(user_id, payload.categories)

        # Resolve rollover allocations from the previous month
        rollover_allocs: list[AllocationUpsert] = []
        if payload.rollover:
            prev_month_date = _prev_month(month_date)
            prior_budget = self.repo.get_by_month_and_user(prev_month_date, user_id)
            if prior_budget is not None:
                existing_cat_ids = {a.category_id for a in payload.categories}
                for prior_alloc in prior_budget.category_allocations:
                    if prior_alloc.category_id not in existing_cat_ids:
                        # Only roll over if not explicitly overridden
                        rollover_allocs.append(
                            AllocationUpsert(
                                category_id=prior_alloc.category_id,
                                planned_amount=prior_alloc.planned_amount,
                                display_order=prior_alloc.display_order,
                            )
                        )

        try:
            budget = self.repo.create(
                user_id=user_id,
                month_date=month_date,
                income=payload.income,
                warning_threshold=payload.warning_threshold,
            )
            self.db.flush()  # get budget.id

            all_allocs = list(payload.categories) + rollover_allocs
            for item in all_allocs:
                self.repo.upsert_allocation(
                    budget_id=budget.id,
                    category_id=item.category_id,
                    planned_amount=item.planned_amount,
                    display_order=item.display_order,
                )

            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise BudgetConflictError(
                f"A budget for {payload.month} already exists."
            ) from exc

        # Reload with eager joins
        budget = self.repo.get_by_id_and_user(budget.id, user_id)
        spending_map = self._spending_map(user_id, budget)
        return self._build_budget_public(budget, spending_map)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_budget(
        self,
        *,
        user_id: uuid.UUID,
        budget_id: uuid.UUID,
        payload: BudgetUpdate,
    ) -> BudgetPublic:
        budget = self.repo.get_by_id_and_user(budget_id, user_id)
        if budget is None:
            raise BudgetNotFoundError(f"Budget {budget_id} not found.")

        self.repo.update(
            budget,
            income=payload.income,
            warning_threshold=payload.warning_threshold,
        )
        self.db.commit()

        # Reload fresh
        budget = self.repo.get_by_id_and_user(budget_id, user_id)
        spending_map = self._spending_map(user_id, budget)
        return self._build_budget_public(budget, spending_map)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_budget(
        self,
        *,
        user_id: uuid.UUID,
        budget_id: uuid.UUID,
    ) -> None:
        budget = self.repo.get_by_id_and_user(budget_id, user_id)
        if budget is None:
            raise BudgetNotFoundError(f"Budget {budget_id} not found.")

        self.repo.delete(budget)
        self.db.commit()
