"""Repository for the expenses table.

Handles all SQL for expense CRUD and filtered paginated listing.
Cursor-based pagination uses (expense_date DESC, id DESC) which matches
the ``expenses_user_date_idx`` index defined on the model.

No business logic lives here — only database access.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import and_, cast, or_, select, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Text as SAText
from sqlalchemy.orm import Session, joinedload

from app.models.category import SpendingCategory
from app.models.expense import Expense


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _month_date_range(month: str) -> tuple[date, date]:
    """Return (first_day, last_day) for a YYYY-MM string."""
    year, mon = int(month[:4]), int(month[5:7])
    first = date(year, mon, 1)
    # Roll forward to find the last day of the month
    if mon == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, mon + 1, 1) - timedelta(days=1)
    return first, last


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class ExpenseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Single-record reads
    # ------------------------------------------------------------------

    def get_by_id_and_user(
        self,
        expense_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Expense]:
        """Fetch one expense with its category eagerly loaded, enforcing ownership."""
        return self.db.scalar(
            select(Expense)
            .options(joinedload(Expense.category))
            .where(
                Expense.id == expense_id,
                Expense.user_id == user_id,
            )
        )

    # ------------------------------------------------------------------
    # List with filtering + cursor pagination
    # ------------------------------------------------------------------

    def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        # date filters
        month: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        # dimension filters
        category_id: Optional[uuid.UUID] = None,
        payment_method: Optional[str] = None,
        is_recurring: Optional[bool] = None,
        tags: Optional[list[str]] = None,
        # amount range
        amount_min: Optional[Decimal] = None,
        amount_max: Optional[Decimal] = None,
        # search
        q: Optional[str] = None,
        # sorting
        sort_by: str = "date",
        sort_order: str = "desc",
        # pagination
        limit: int = 50,
        cursor_date: Optional[date] = None,
        cursor_id: Optional[uuid.UUID] = None,
    ) -> tuple[Sequence[Expense], Optional[str]]:
        """Return (items, next_cursor) for the given filters.

        Returns one extra row beyond ``limit`` to determine whether a next
        page exists without a separate COUNT query.
        """
        from app.schemas.expense import PaginationCursor

        stmt = (
            select(Expense)
            .options(joinedload(Expense.category))
            .where(Expense.user_id == user_id)
        )

        # -- Date range (month shortcut or explicit range) ----------------
        if month:
            d_from, d_to = _month_date_range(month)
            stmt = stmt.where(
                Expense.expense_date >= d_from,
                Expense.expense_date <= d_to,
            )
        else:
            if date_from:
                stmt = stmt.where(Expense.expense_date >= date_from)
            if date_to:
                stmt = stmt.where(Expense.expense_date <= date_to)

        # -- Dimension filters -------------------------------------------
        if category_id is not None:
            stmt = stmt.where(Expense.category_id == category_id)

        if payment_method is not None:
            stmt = stmt.where(Expense.payment_method == payment_method)

        if is_recurring is not None:
            stmt = stmt.where(Expense.is_recurring == is_recurring)

        # Tags — require ALL specified tags present (AND containment)
        if tags:
            stmt = stmt.where(
                Expense.tags.contains(cast(tags, ARRAY(SAText())))
            )

        # -- Amount range ------------------------------------------------
        if amount_min is not None:
            stmt = stmt.where(Expense.amount >= amount_min)
        if amount_max is not None:
            stmt = stmt.where(Expense.amount <= amount_max)

        # -- Full-text search on note + merchant -------------------------
        if q:
            pattern = f"%{q.lower()}%"
            stmt = stmt.where(
                or_(
                    Expense.note.ilike(pattern),
                    Expense.merchant.ilike(pattern),
                )
            )

        # -- Cursor application (keyset pagination) ----------------------
        desc = sort_order == "desc"
        if cursor_date is not None and cursor_id is not None:
            if sort_by == "date":
                if desc:
                    # Rows before the cursor position
                    stmt = stmt.where(
                        or_(
                            Expense.expense_date < cursor_date,
                            and_(
                                Expense.expense_date == cursor_date,
                                Expense.id < cursor_id,
                            ),
                        )
                    )
                else:
                    stmt = stmt.where(
                        or_(
                            Expense.expense_date > cursor_date,
                            and_(
                                Expense.expense_date == cursor_date,
                                Expense.id > cursor_id,
                            ),
                        )
                    )
            # For amount sort, fall back to id tiebreak on same amount
            elif sort_by == "amount":
                if desc:
                    stmt = stmt.where(Expense.id < cursor_id)
                else:
                    stmt = stmt.where(Expense.id > cursor_id)

        # -- Sorting ------------------------------------------------------
        if sort_by == "amount":
            order_col = Expense.amount.desc() if desc else Expense.amount.asc()
        else:  # default: date
            order_col = (
                Expense.expense_date.desc() if desc else Expense.expense_date.asc()
            )

        stmt = stmt.order_by(order_col, Expense.id.desc() if desc else Expense.id.asc())

        # Fetch limit + 1 to detect next page
        stmt = stmt.limit(limit + 1)

        rows = list(self.db.scalars(stmt).all())

        if len(rows) > limit:
            rows = rows[:limit]
            last = rows[-1]
            next_cursor = PaginationCursor.encode(last.expense_date, last.id)
        else:
            next_cursor = None

        return rows, next_cursor

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        amount: Decimal,
        expense_date: date,
        note: str = "",
        payment_method: Optional[str] = None,
        merchant: Optional[str] = None,
        tags: list[str] | None = None,
        currency: str = "INR",
        is_recurring: bool = False,
        receipt_file_id: Optional[uuid.UUID] = None,
        paid_by_member_id: Optional[uuid.UUID] = None,
    ) -> Expense:
        expense = Expense(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            expense_date=expense_date,
            note=note,
            payment_method=payment_method,
            merchant=merchant,
            tags=tags if tags is not None else [],
            currency=currency,
            is_recurring=is_recurring,
            receipt_file_id=receipt_file_id,
            paid_by_member_id=paid_by_member_id,
        )
        self.db.add(expense)
        return expense

    def update(
        self,
        expense: Expense,
        *,
        category_id: Optional[uuid.UUID] = None,
        amount: Optional[Decimal] = None,
        expense_date: Optional[date] = None,
        note: Optional[str] = None,
        payment_method: Optional[str] = None,
        merchant: Optional[str] = None,
        tags: Optional[list[str]] = None,
        currency: Optional[str] = None,
        is_recurring: Optional[bool] = None,
        receipt_file_id: Optional[uuid.UUID] = None,
        paid_by_member_id: Optional[uuid.UUID] = None,
    ) -> Expense:
        if category_id is not None:
            expense.category_id = category_id
        if amount is not None:
            expense.amount = amount
        if expense_date is not None:
            expense.expense_date = expense_date
        if note is not None:
            expense.note = note
        if payment_method is not None:
            expense.payment_method = payment_method
        if merchant is not None:
            expense.merchant = merchant
        if tags is not None:
            expense.tags = tags
        if currency is not None:
            expense.currency = currency
        if is_recurring is not None:
            expense.is_recurring = is_recurring
        if receipt_file_id is not None:
            expense.receipt_file_id = receipt_file_id
        if paid_by_member_id is not None:
            expense.paid_by_member_id = paid_by_member_id
        return expense

    def delete(self, expense: Expense) -> None:
        self.db.delete(expense)
