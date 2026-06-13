"""Expense service.

Owns all business rules for individual expense records:
- Category must exist and be visible to the requesting user
- Ownership checks on read/update/delete
- Delegates cursor pagination assembly to the repository
"""

from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.repositories.category import CategoryRepository
from app.repositories.expense import ExpenseRepository
from app.schemas.expense import ExpenseCreate, ExpenseFilters, ExpenseUpdate, PaginationCursor


# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------

class ExpenseServiceError(Exception):
    """Base for expense service errors."""


class ExpenseNotFoundError(ExpenseServiceError):
    """Raised when the expense does not exist or is not owned by the user."""


class ExpenseCategoryError(ExpenseServiceError):
    """Raised when the referenced category is not accessible to the user."""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class ExpenseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ExpenseRepository(db)
        self.categories = CategoryRepository(db)

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def list_expenses(
        self,
        *,
        user_id: uuid.UUID,
        filters: ExpenseFilters,
    ) -> tuple[list[Expense], Optional[str]]:
        """Return (expenses, next_cursor) applying all filters."""
        cursor_date = None
        cursor_id = None
        cursor_amount = None
        if filters.cursor:
            try:
                cursor_date, cursor_id, cursor_amount = PaginationCursor.decode(filters.cursor)
            except ValueError as exc:
                raise ExpenseServiceError(f"Invalid cursor: {exc}") from exc

        items, next_cursor = self.repo.list_for_user(
            user_id=user_id,
            month=filters.month,
            date_from=filters.date_from,
            date_to=filters.date_to,
            category_id=filters.category_id,
            payment_method=filters.payment_method.value if filters.payment_method else None,
            is_recurring=filters.is_recurring,
            tags=filters.parsed_tags() or None,
            amount_min=filters.amount_min,
            amount_max=filters.amount_max,
            q=filters.q,
            sort_by=filters.sort_by,
            sort_order=filters.sort_order,
            limit=filters.limit,
            cursor_date=cursor_date,
            cursor_id=cursor_id,
            cursor_amount=cursor_amount,
        )
        return list(items), next_cursor

    # ------------------------------------------------------------------
    # Single-record reads
    # ------------------------------------------------------------------

    def get_expense(
        self,
        *,
        user_id: uuid.UUID,
        expense_id: uuid.UUID,
    ) -> Expense:
        expense = self.repo.get_by_id_and_user(expense_id, user_id)
        if expense is None:
            raise ExpenseNotFoundError(f"Expense {expense_id} not found.")
        return expense

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_expense(
        self,
        *,
        user_id: uuid.UUID,
        payload: ExpenseCreate,
    ) -> Expense:
        # Validate that the category is visible to this user
        category = self.categories.get_by_id_for_user(
            payload.category_id, user_id
        )
        if category is None:
            raise ExpenseCategoryError(
                f"Category {payload.category_id} not found or not accessible."
            )
        if category.is_archived:
            raise ExpenseCategoryError(
                "Cannot assign an archived category to a new expense."
            )

        expense = self.repo.create(
            user_id=user_id,
            category_id=payload.category_id,
            amount=payload.amount,
            expense_date=payload.expense_date,
            note=payload.note,
            payment_method=payload.payment_method.value if payload.payment_method else None,
            merchant=payload.merchant,
            tags=payload.tags,
            currency=payload.currency.value,
            is_recurring=payload.is_recurring,
            receipt_file_id=payload.receipt_file_id,
            paid_by_member_id=payload.paid_by_member_id,
        )

        self.db.flush()
        # Eagerly load the category so the response schema can serialize it
        self.db.refresh(expense)
        # Load category relationship
        _ = expense.category
        self.db.commit()
        self.db.refresh(expense)
        # Ensure category is loaded after commit
        _ = expense.category
        # Invalidate per-user analytics cache
        from app.core.cache import invalidate_user
        invalidate_user(str(user_id))
        return expense

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_expense(
        self,
        *,
        user_id: uuid.UUID,
        expense_id: uuid.UUID,
        payload: ExpenseUpdate,
    ) -> Expense:
        expense = self.repo.get_by_id_and_user(expense_id, user_id)
        if expense is None:
            raise ExpenseNotFoundError(f"Expense {expense_id} not found.")

        # Validate new category if provided
        if payload.category_id is not None:
            category = self.categories.get_by_id_for_user(
                payload.category_id, user_id
            )
            if category is None:
                raise ExpenseCategoryError(
                    f"Category {payload.category_id} not found or not accessible."
                )
            if category.is_archived:
                raise ExpenseCategoryError(
                    "Cannot assign an archived category to an expense."
                )

        self.repo.update(
            expense,
            category_id=payload.category_id,
            amount=payload.amount,
            expense_date=payload.expense_date,
            note=payload.note,
            payment_method=payload.payment_method.value if payload.payment_method else None,
            merchant=payload.merchant,
            tags=payload.tags,
            currency=payload.currency.value if payload.currency else None,
            is_recurring=payload.is_recurring,
            receipt_file_id=payload.receipt_file_id,
            paid_by_member_id=payload.paid_by_member_id,
        )

        self.db.commit()
        self.db.refresh(expense)
        # Ensure category relationship is fresh
        _ = expense.category
        # Invalidate per-user analytics cache
        from app.core.cache import invalidate_user
        invalidate_user(str(user_id))
        return expense

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_expense(
        self,
        *,
        user_id: uuid.UUID,
        expense_id: uuid.UUID,
    ) -> None:
        expense = self.repo.get_by_id_and_user(expense_id, user_id)
        if expense is None:
            raise ExpenseNotFoundError(f"Expense {expense_id} not found.")

        self.repo.delete(expense)
        self.db.commit()
        # Invalidate per-user analytics cache
        from app.core.cache import invalidate_user
        invalidate_user(str(user_id))
