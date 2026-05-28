"""Expense routes.

All endpoints require a valid JWT access token (Bearer).

GET    /expenses                — list with filters + cursor pagination
POST   /expenses                — create an expense
GET    /expenses/{expense_id}   — get a single expense
PATCH  /expenses/{expense_id}   — partial update
DELETE /expenses/{expense_id}   — hard delete
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import CurrencyCode, PaymentMethod
from app.models.user import User
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseFilters,
    ExpenseListResponse,
    ExpensePublic,
    ExpenseUpdate,
)
from app.services.expense import (
    ExpenseCategoryError,
    ExpenseNotFoundError,
    ExpenseService,
    ExpenseServiceError,
)

router = APIRouter(prefix="/expenses", tags=["expenses"])


# ---------------------------------------------------------------------------
# Dependency: parse all query params into ExpenseFilters
# ---------------------------------------------------------------------------

def _parse_filters(
    month: Annotated[
        Optional[str],
        Query(pattern=r"^\d{4}-\d{2}$", description="Month shortcut (YYYY-MM)."),
    ] = None,
    date_from: Annotated[Optional[date], Query(alias="dateFrom")] = None,
    date_to: Annotated[Optional[date], Query(alias="dateTo")] = None,
    category_id: Annotated[Optional[uuid.UUID], Query(alias="categoryId")] = None,
    payment_method: Annotated[Optional[PaymentMethod], Query(alias="paymentMethod")] = None,
    amount_min: Annotated[Optional[Decimal], Query(alias="amountMin", gt=0)] = None,
    amount_max: Annotated[Optional[Decimal], Query(alias="amountMax", gt=0)] = None,
    is_recurring: Annotated[Optional[bool], Query(alias="isRecurring")] = None,
    tags: Annotated[
        Optional[str],
        Query(description="Comma-separated tag list — all must match (AND)."),
    ] = None,
    q: Annotated[Optional[str], Query(max_length=200)] = None,
    sort_by: Annotated[str, Query(alias="sortBy", pattern=r"^(date|amount)$")] = "date",
    sort_order: Annotated[
        str, Query(alias="sortOrder", pattern=r"^(asc|desc)$")
    ] = "desc",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[Optional[str], Query()] = None,
) -> ExpenseFilters:
    try:
        return ExpenseFilters(
            month=month,
            date_from=date_from,
            date_to=date_to,
            category_id=category_id,
            payment_method=payment_method,
            amount_min=amount_min,
            amount_max=amount_max,
            is_recurring=is_recurring,
            tags=tags,
            q=q,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            cursor=cursor,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# GET /expenses
# ---------------------------------------------------------------------------

@router.get("", response_model=ExpenseListResponse)
def list_expenses(
    filters: Annotated[ExpenseFilters, Depends(_parse_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> ExpenseListResponse:
    """Return a paginated list of expenses with optional filters.

    Use ``cursor`` from the previous response's ``nextCursor`` field to
    retrieve the next page.
    """
    service = ExpenseService(db)
    try:
        items, next_cursor = service.list_expenses(user_id=user.id, filters=filters)
    except ExpenseServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ExpenseListResponse(
        items=[ExpensePublic.model_validate(e) for e in items],
        next_cursor=next_cursor,
        total_returned=len(items),
    )


# ---------------------------------------------------------------------------
# POST /expenses
# ---------------------------------------------------------------------------

@router.post("", response_model=ExpensePublic, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> ExpensePublic:
    """Create a new expense."""
    service = ExpenseService(db)
    try:
        expense = service.create_expense(user_id=user.id, payload=payload)
    except ExpenseCategoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return ExpensePublic.model_validate(expense)


# ---------------------------------------------------------------------------
# GET /expenses/{expense_id}
# ---------------------------------------------------------------------------

@router.get("/{expense_id}", response_model=ExpensePublic)
def get_expense(
    expense_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> ExpensePublic:
    """Return a single expense by ID."""
    service = ExpenseService(db)
    try:
        expense = service.get_expense(user_id=user.id, expense_id=expense_id)
    except ExpenseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ExpensePublic.model_validate(expense)


# ---------------------------------------------------------------------------
# PATCH /expenses/{expense_id}
# ---------------------------------------------------------------------------

@router.patch("/{expense_id}", response_model=ExpensePublic)
def update_expense(
    expense_id: uuid.UUID,
    payload: ExpenseUpdate,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> ExpensePublic:
    """Partially update an expense.  Only provided fields are changed."""
    service = ExpenseService(db)
    try:
        expense = service.update_expense(
            user_id=user.id,
            expense_id=expense_id,
            payload=payload,
        )
    except ExpenseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ExpenseCategoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return ExpensePublic.model_validate(expense)


# ---------------------------------------------------------------------------
# DELETE /expenses/{expense_id}
# ---------------------------------------------------------------------------

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> None:
    """Hard-delete an expense and its split rows (via CASCADE)."""
    service = ExpenseService(db)
    try:
        service.delete_expense(user_id=user.id, expense_id=expense_id)
    except ExpenseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
