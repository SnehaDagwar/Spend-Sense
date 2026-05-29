"""Budget routes.

All endpoints require a valid JWT access token (Bearer).

GET    /budgets                — list budgets with month-range/category filters
POST   /budgets                — create a budget for a month
GET    /budgets/{budget_id}    — get a single budget with per-category analytics
PATCH  /budgets/{budget_id}    — partial update (income, warning_threshold)
DELETE /budgets/{budget_id}    — hard-delete (allocations cascade)
"""

from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.budget import (
    BudgetCreate,
    BudgetFilters,
    BudgetListResponse,
    BudgetPublic,
    BudgetUpdate,
)
from app.services.budget import (
    BudgetCategoryError,
    BudgetConflictError,
    BudgetNotFoundError,
    BudgetService,
    BudgetServiceError,
    BudgetValidationError,
)

router = APIRouter(prefix="/budgets", tags=["budgets"])


# ---------------------------------------------------------------------------
# Dependency: parse query params into BudgetFilters
# ---------------------------------------------------------------------------

def _parse_filters(
    from_month: Annotated[
        Optional[str],
        Query(
            alias="from",
            pattern=r"^\d{4}-\d{2}$",
            description="Start month (YYYY-MM), inclusive.",
        ),
    ] = None,
    to_month: Annotated[
        Optional[str],
        Query(
            alias="to",
            pattern=r"^\d{4}-\d{2}$",
            description="End month (YYYY-MM), inclusive.",
        ),
    ] = None,
    category_id: Annotated[
        Optional[uuid.UUID],
        Query(alias="categoryId", description="Filter to budgets containing this category."),
    ] = None,
    active_only: Annotated[
        bool,
        Query(alias="activeOnly", description="Restrict to the current calendar month."),
    ] = False,
) -> BudgetFilters:
    try:
        return BudgetFilters(
            from_month=from_month,
            to_month=to_month,
            category_id=category_id,
            active_only=active_only,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# GET /budgets
# ---------------------------------------------------------------------------

@router.get("", response_model=BudgetListResponse)
def list_budgets(
    filters: Annotated[BudgetFilters, Depends(_parse_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> BudgetListResponse:
    """Return a list of monthly budgets with summary analytics.

    Supports optional ``from``/``to`` month-range filters (YYYY-MM),
    ``categoryId`` to find budgets containing a specific allocation,
    and ``activeOnly`` to restrict to the current calendar month.
    """
    service = BudgetService(db)
    try:
        items = service.list_budgets(user_id=user.id, filters=filters)
    except BudgetServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return BudgetListResponse(items=items, total_returned=len(items))


# ---------------------------------------------------------------------------
# POST /budgets
# ---------------------------------------------------------------------------

@router.post("", response_model=BudgetPublic, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> BudgetPublic:
    """Create a monthly budget.

    - ``month``: required, YYYY-MM format.
    - ``income``: optional gross income for the month (≥ 0).
    - ``warningThreshold``: fraction 0–1 at which "near limit" warnings fire (default 0.80).
    - ``categories``: list of category allocations (categoryId + plannedAmount).
    - ``rollover``: when true, copy allocations from the prior month as defaults.

    Returns 409 if a budget for that month already exists.
    Returns 422 if any category is not accessible or is archived.
    """
    service = BudgetService(db)
    try:
        return service.create_budget(user_id=user.id, payload=payload)
    except BudgetValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except BudgetConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except BudgetCategoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# GET /budgets/{budget_id}
# ---------------------------------------------------------------------------

@router.get("/{budget_id}", response_model=BudgetPublic)
def get_budget(
    budget_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> BudgetPublic:
    """Return a single budget with full per-category and month-level analytics.

    Analytics include:
    - Per-category: spent, remaining, pct_used, is_over_budget, is_near_limit
    - Month-level: total_planned, total_spent, total_remaining, pct_used,
                   projected_spend, is_over_budget
    """
    service = BudgetService(db)
    try:
        return service.get_budget(user_id=user.id, budget_id=budget_id)
    except BudgetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# PATCH /budgets/{budget_id}
# ---------------------------------------------------------------------------

@router.patch("/{budget_id}", response_model=BudgetPublic)
def update_budget(
    budget_id: uuid.UUID,
    payload: BudgetUpdate,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> BudgetPublic:
    """Partially update a budget.

    Updatable fields: ``income``, ``warningThreshold``.
    At least one field must be provided.
    Returns the updated budget with fresh analytics.
    """
    service = BudgetService(db)
    try:
        return service.update_budget(
            user_id=user.id,
            budget_id=budget_id,
            payload=payload,
        )
    except BudgetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# DELETE /budgets/{budget_id}
# ---------------------------------------------------------------------------

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> None:
    """Hard-delete a budget and all its category allocations (via CASCADE).

    This does NOT delete any expense records; they remain unchanged.
    """
    service = BudgetService(db)
    try:
        service.delete_budget(user_id=user.id, budget_id=budget_id)
    except BudgetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
