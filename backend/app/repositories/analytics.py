"""Repository for analytics database queries.

Encapsulates database access for aggregation, range filters, and budget comparisons.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.budget import BudgetCategoryAllocation, MonthlyBudget
from app.models.category import SpendingCategory
from app.models.expense import Expense


class AnalyticsRepository:
    """Repository wrapping db queries for Spend Sense analytics."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_total_spending(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """Calculate total spending of the user in a custom date range.

        Uses compound indexes for fast query.
        """
        stmt = (
            select(func.sum(Expense.amount))
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
        )
        result = self.db.execute(stmt).scalar()
        return result or Decimal("0.00")

    def get_spending_by_category(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[tuple[uuid.UUID, str, str, str, str, Decimal]]:
        """Return category details and their total spending in a date range.

        Result elements are: (category_id, name, slug, icon, color, total_spent)
        Ordered by total_spent DESC.
        """
        stmt = (
            select(
                SpendingCategory.id.label("category_id"),
                SpendingCategory.name,
                SpendingCategory.slug,
                SpendingCategory.icon,
                SpendingCategory.color,
                func.sum(Expense.amount).label("total_spent"),
            )
            .join(Expense, Expense.category_id == SpendingCategory.id)
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
            .group_by(
                SpendingCategory.id,
                SpendingCategory.name,
                SpendingCategory.slug,
                SpendingCategory.icon,
                SpendingCategory.color,
            )
            .order_by(func.sum(Expense.amount).desc())
        )
        results = self.db.execute(stmt).all()
        return [
            (
                r.category_id,
                r.name,
                r.slug,
                r.icon,
                r.color,
                r.total_spent,
            )
            for r in results
        ]

    def get_spending_trend(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[tuple[date, Decimal, int]]:
        """Return spending aggregates by day.

        Result elements are: (date, total_spent, transaction_count)
        """
        stmt = (
            select(
                Expense.expense_date,
                func.sum(Expense.amount).label("total_spent"),
                func.count(Expense.id).label("transaction_count"),
            )
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
            .group_by(Expense.expense_date)
            .order_by(Expense.expense_date.asc())
        )
        results = self.db.execute(stmt).all()
        return [
            (
                r.expense_date,
                r.total_spent,
                r.transaction_count,
            )
            for r in results
        ]

    def get_budget_by_month(
        self,
        user_id: uuid.UUID,
        month_start: date,
    ) -> Optional[MonthlyBudget]:
        """Fetch the MonthlyBudget for a specific month with its allocations and categories."""
        stmt = (
            select(MonthlyBudget)
            .options(
                joinedload(MonthlyBudget.category_allocations).joinedload(
                    BudgetCategoryAllocation.category
                )
            )
            .where(
                MonthlyBudget.user_id == user_id,
                MonthlyBudget.month == month_start,
            )
        )
        return self.db.scalar(stmt)

    def get_budgets_for_months(
        self,
        user_id: uuid.UUID,
        months_starts: Sequence[date],
    ) -> Sequence[MonthlyBudget]:
        """Fetch MonthlyBudgets for a set of month starting dates."""
        if not months_starts:
            return []
        stmt = (
            select(MonthlyBudget)
            .options(
                joinedload(MonthlyBudget.category_allocations)
            )
            .where(
                MonthlyBudget.user_id == user_id,
                MonthlyBudget.month.in_(months_starts),
            )
            .order_by(MonthlyBudget.month.asc())
        )
        return self.db.scalars(stmt).unique().all()
