"""Reports API route handlers.

All endpoints require a valid JWT access token.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import BudgetPerformanceResponse
from app.schemas.report import (
    CategoryReportResponse,
    GoalReportResponse,
    MonthlyReportResponse,
    ReportFilters,
)
from app.services.report import ReportService


router = APIRouter(prefix="/reports", tags=["reports"])


# ---------------------------------------------------------------------------
# Query Filter Dependency Parser
# ---------------------------------------------------------------------------

def _parse_report_filters(
    month: Annotated[
        Optional[str],
        Query(pattern=r"^\d{4}-\d{2}$", description="Month shortcut (YYYY-MM)."),
    ] = None,
    date_from: Annotated[Optional[date], Query(alias="dateFrom")] = None,
    date_to: Annotated[Optional[date], Query(alias="dateTo")] = None,
    category_id: Annotated[Optional[uuid.UUID], Query(alias="categoryId")] = None,
) -> ReportFilters:
    try:
        return ReportFilters(
            month=month,
            date_from=date_from,
            date_to=date_to,
            category_id=category_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# Route Handlers
# ---------------------------------------------------------------------------

@router.get("/monthly", response_model=MonthlyReportResponse)
def get_monthly_report(
    filters: Annotated[ReportFilters, Depends(_parse_report_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> MonthlyReportResponse:
    """Return overall monthly spending, budget comparison, and savings metrics."""
    service = ReportService(db)
    return service.get_monthly_report(user_id=user.id, filters=filters)


@router.get("/categories", response_model=CategoryReportResponse)
def get_category_report(
    filters: Annotated[ReportFilters, Depends(_parse_report_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> CategoryReportResponse:
    """Return detailed category spending report with averages and transaction counts."""
    service = ReportService(db)
    return service.get_category_report(user_id=user.id, filters=filters)


@router.get("/budgets", response_model=BudgetPerformanceResponse)
def get_budget_report(
    filters: Annotated[ReportFilters, Depends(_parse_report_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> BudgetPerformanceResponse:
    """Return comprehensive category-level budget planned vs actual breakdown."""
    service = ReportService(db)
    return service.get_budget_report(user_id=user.id, filters=filters)


@router.get("/goals", response_model=GoalReportResponse)
def get_goal_report(
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> GoalReportResponse:
    """Return a detailed list of savings goals and live milestone tracking."""
    service = ReportService(db)
    return service.get_goal_report(user_id=user.id)
