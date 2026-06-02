"""Repository for Reports database access.

Encapsulates SQL queries for category aggregation and chunked expense streaming.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Generator, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.category import SpendingCategory
from app.models.expense import Expense


class ReportRepository:
    """Manages db access for financial reports and data exports."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_category_spending_report(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
        category_id: Optional[uuid.UUID] = None,
    ) -> list[tuple[uuid.UUID, str, str, str, str, Decimal, int, Decimal]]:
        """Fetch category spending stats aggregated for a date range.

        Returns tuples of:
        (category_id, name, slug, icon, color, total_spent, transaction_count, average_spent)
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
                func.count(Expense.id).label("transaction_count"),
                func.avg(Expense.amount).label("average_spent"),
            )
            .join(Expense, Expense.category_id == SpendingCategory.id)
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
        )

        if category_id is not None:
            stmt = stmt.where(SpendingCategory.id == category_id)

        stmt = stmt.group_by(
            SpendingCategory.id,
            SpendingCategory.name,
            SpendingCategory.slug,
            SpendingCategory.icon,
            SpendingCategory.color,
        ).order_by(func.sum(Expense.amount).desc())

        results = self.db.execute(stmt).all()
        return [
            (
                r.category_id,
                r.name,
                r.slug,
                r.icon,
                r.color,
                r.total_spent or Decimal("0.00"),
                r.transaction_count or 0,
                r.average_spent or Decimal("0.00"),
            )
            for r in results
        ]

    def stream_expenses_for_export(
        self,
        *,
        user_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[uuid.UUID] = None,
        chunk_size: int = 1000,
    ) -> Generator[Expense, None, None]:
        """Stream expense rows from the database in chunks of `chunk_size`.

        Ensures low memory utilization even on extremely large datasets.
        """
        stmt = (
            select(Expense)
            .options(joinedload(Expense.category))
            .where(Expense.user_id == user_id)
        )

        if start_date is not None:
            stmt = stmt.where(Expense.expense_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(Expense.expense_date <= end_date)
        if category_id is not None:
            stmt = stmt.where(Expense.category_id == category_id)

        # Sort chronologically or by newest
        stmt = stmt.order_by(Expense.expense_date.desc(), Expense.id.desc())

        offset = 0
        while True:
            chunk_stmt = stmt.limit(chunk_size).offset(offset)
            results = self.db.scalars(chunk_stmt).all()
            if not results:
                break
            for expense in results:
                yield expense
            offset += chunk_size
