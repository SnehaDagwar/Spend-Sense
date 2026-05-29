"""Repository for monthly_budgets and budget_category_allocations tables.

All SQL for budget CRUD and spending aggregation lives here.
No business logic — only database access.

Query strategy:
- Budget + allocations + categories are fetched in a single joinedload to
  prevent N+1.
- Spending aggregation uses one GROUP BY query over the expenses table,
  leveraging the ``expenses_user_category_date_idx`` index.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload, contains_eager

from app.models.budget import BudgetCategoryAllocation, MonthlyBudget
from app.models.expense import Expense


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _month_last_day(month_start: date) -> date:
    """Return the last day of the month given its first day."""
    year, mon = month_start.year, month_start.month
    if mon == 12:
        return date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, mon + 1, 1) - timedelta(days=1)


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class BudgetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Single-record reads
    # ------------------------------------------------------------------

    def get_by_id_and_user(
        self,
        budget_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[MonthlyBudget]:
        """Fetch one budget with allocations+categories eagerly loaded."""
        return self.db.scalar(
            select(MonthlyBudget)
            .options(
                joinedload(MonthlyBudget.category_allocations).joinedload(
                    BudgetCategoryAllocation.category
                )
            )
            .where(
                MonthlyBudget.id == budget_id,
                MonthlyBudget.user_id == user_id,
            )
        )

    def get_by_month_and_user(
        self,
        month_date: date,
        user_id: uuid.UUID,
    ) -> Optional[MonthlyBudget]:
        """Fetch a budget by (user_id, month) with allocations+categories."""
        return self.db.scalar(
            select(MonthlyBudget)
            .options(
                joinedload(MonthlyBudget.category_allocations).joinedload(
                    BudgetCategoryAllocation.category
                )
            )
            .where(
                MonthlyBudget.month == month_date,
                MonthlyBudget.user_id == user_id,
            )
        )

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        category_id: Optional[uuid.UUID] = None,
    ) -> Sequence[MonthlyBudget]:
        """Return budgets for a user with optional month-range and category filters.

        When ``category_id`` is provided, only budgets that have an allocation
        for that category are returned.

        Results are ordered by ``month DESC`` (most recent first).
        Allocations + categories are eagerly loaded in a single subquery load
        to avoid N+1.
        """
        stmt = (
            select(MonthlyBudget)
            .options(
                joinedload(MonthlyBudget.category_allocations).joinedload(
                    BudgetCategoryAllocation.category
                )
            )
            .where(MonthlyBudget.user_id == user_id)
            .order_by(MonthlyBudget.month.desc())
        )

        if from_date is not None:
            stmt = stmt.where(MonthlyBudget.month >= from_date)
        if to_date is not None:
            stmt = stmt.where(MonthlyBudget.month <= to_date)

        if category_id is not None:
            # Only budgets that contain an allocation for this category
            allocation_sub = select(BudgetCategoryAllocation.budget_id).where(
                BudgetCategoryAllocation.category_id == category_id
            )
            stmt = stmt.where(MonthlyBudget.id.in_(allocation_sub))

        # Use unique() because joinedload can produce duplicates with collections
        return self.db.scalars(stmt).unique().all()

    # ------------------------------------------------------------------
    # Spending aggregation
    # ------------------------------------------------------------------

    def get_spending_by_category(
        self,
        *,
        user_id: uuid.UUID,
        month_start: date,
        month_end: date,
    ) -> dict[uuid.UUID, Decimal]:
        """Return {category_id: total_spent} for the given month range.

        Uses a single SUM + GROUP BY query over the expenses table.
        Leverages the ``expenses_user_category_date_idx`` index.
        """
        rows = self.db.execute(
            select(Expense.category_id, func.sum(Expense.amount).label("total"))
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= month_start,
                Expense.expense_date <= month_end,
            )
            .group_by(Expense.category_id)
        ).all()

        return {row.category_id: row.total for row in rows}

    # ------------------------------------------------------------------
    # Writes — MonthlyBudget
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        user_id: uuid.UUID,
        month_date: date,
        income: Decimal = Decimal("0"),
        warning_threshold: Decimal = Decimal("0.8000"),
    ) -> MonthlyBudget:
        budget = MonthlyBudget(
            user_id=user_id,
            month=month_date,
            income=income,
            warning_threshold=warning_threshold,
        )
        self.db.add(budget)
        return budget

    def update(
        self,
        budget: MonthlyBudget,
        *,
        income: Optional[Decimal] = None,
        warning_threshold: Optional[Decimal] = None,
    ) -> MonthlyBudget:
        if income is not None:
            budget.income = income
        if warning_threshold is not None:
            budget.warning_threshold = warning_threshold
        return budget

    def delete(self, budget: MonthlyBudget) -> None:
        """Hard-delete a budget. Allocations are cascade-deleted by the DB."""
        self.db.delete(budget)

    # ------------------------------------------------------------------
    # Writes — BudgetCategoryAllocation
    # ------------------------------------------------------------------

    def get_allocation(
        self,
        budget_id: uuid.UUID,
        category_id: uuid.UUID,
    ) -> Optional[BudgetCategoryAllocation]:
        return self.db.scalar(
            select(BudgetCategoryAllocation).where(
                BudgetCategoryAllocation.budget_id == budget_id,
                BudgetCategoryAllocation.category_id == category_id,
            )
        )

    def upsert_allocation(
        self,
        *,
        budget_id: uuid.UUID,
        category_id: uuid.UUID,
        planned_amount: Decimal,
        display_order: int = 0,
    ) -> BudgetCategoryAllocation:
        """Create or update a single category allocation."""
        existing = self.get_allocation(budget_id, category_id)
        if existing is not None:
            existing.planned_amount = planned_amount
            existing.display_order = display_order
            return existing

        allocation = BudgetCategoryAllocation(
            budget_id=budget_id,
            category_id=category_id,
            planned_amount=planned_amount,
            display_order=display_order,
        )
        self.db.add(allocation)
        return allocation

    def delete_allocation(
        self,
        budget_id: uuid.UUID,
        category_id: uuid.UUID,
    ) -> bool:
        """Remove one allocation. Returns True if it existed."""
        existing = self.get_allocation(budget_id, category_id)
        if existing is None:
            return False
        self.db.delete(existing)
        return True

    def replace_all_allocations(
        self,
        budget: MonthlyBudget,
        allocations: list[dict],
    ) -> None:
        """Replace all allocations for a budget with the supplied list.

        ``allocations`` is a list of dicts with keys:
            category_id, planned_amount, display_order
        """
        # Remove existing allocations not in the new set
        new_cat_ids = {a["category_id"] for a in allocations}
        for alloc in list(budget.category_allocations):
            if alloc.category_id not in new_cat_ids:
                self.db.delete(alloc)

        # Upsert all supplied allocations
        for entry in allocations:
            self.upsert_allocation(
                budget_id=budget.id,
                category_id=entry["category_id"],
                planned_amount=entry["planned_amount"],
                display_order=entry.get("display_order", 0),
            )
