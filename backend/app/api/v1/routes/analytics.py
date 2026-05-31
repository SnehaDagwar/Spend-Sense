"""Analytics API route handlers.

All endpoints require a valid JWT access token.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsFilters,
    BudgetPerformanceFilters,
    BudgetPerformanceResponse,
    CategoryBreakdownResponse,
    MonthlyComparisonFilters,
    MonthlyComparisonResponse,
    SpendingTrendFilters,
    SpendingTrendResponse,
    SummaryResponse,
)
from app.services.analytics import AnalyticsService


router = APIRouter(prefix="/analytics", tags=["analytics"])


# ---------------------------------------------------------------------------
# Filter Query Parsers
# ---------------------------------------------------------------------------

def _parse_analytics_filters(
    month: Annotated[
        Optional[str],
        Query(pattern=r"^\d{4}-\d{2}$", description="Month shortcut (YYYY-MM)."),
    ] = None,
    date_from: Annotated[Optional[date], Query(alias="dateFrom")] = None,
    date_to: Annotated[Optional[date], Query(alias="dateTo")] = None,
) -> AnalyticsFilters:
    try:
        return AnalyticsFilters(
            month=month,
            date_from=date_from,
            date_to=date_to,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _parse_trend_filters(
    month: Annotated[
        Optional[str],
        Query(pattern=r"^\d{4}-\d{2}$", description="Month shortcut (YYYY-MM)."),
    ] = None,
    date_from: Annotated[Optional[date], Query(alias="dateFrom")] = None,
    date_to: Annotated[Optional[date], Query(alias="dateTo")] = None,
    interval: Annotated[
        str,
        Query(pattern=r"^(daily|weekly)$", description="Trend interval (daily or weekly)."),
    ] = "daily",
) -> SpendingTrendFilters:
    try:
        return SpendingTrendFilters(
            month=month,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _parse_budget_filters(
    month: Annotated[
        Optional[str],
        Query(pattern=r"^\d{4}-\d{2}$", description="Specific budget month (YYYY-MM)."),
    ] = None,
) -> BudgetPerformanceFilters:
    try:
        return BudgetPerformanceFilters(month=month)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _parse_comparison_filters(
    months: Annotated[
        int,
        Query(ge=1, le=12, description="Number of past months to retrieve comparison for."),
    ] = 6,
) -> MonthlyComparisonFilters:
    try:
        return MonthlyComparisonFilters(months=months)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# Route Handlers
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    filters: Annotated[AnalyticsFilters, Depends(_parse_analytics_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> SummaryResponse:
    """Return dashboard summary metrics for the target month or date range."""
    service = AnalyticsService(db)
    return service.get_summary(user_id=user.id, filters=filters)


@router.get("/category-breakdown", response_model=CategoryBreakdownResponse)
def get_category_breakdown(
    filters: Annotated[AnalyticsFilters, Depends(_parse_analytics_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> CategoryBreakdownResponse:
    """Return percentage breakdown of spending by category."""
    service = AnalyticsService(db)
    return service.get_category_breakdown(user_id=user.id, filters=filters)


@router.get("/spending-trend", response_model=SpendingTrendResponse)
def get_spending_trend(
    filters: Annotated[SpendingTrendFilters, Depends(_parse_trend_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> SpendingTrendResponse:
    """Return spending aggregates grouped daily or weekly."""
    service = AnalyticsService(db)
    return service.get_spending_trend(user_id=user.id, filters=filters)


@router.get("/budget-performance", response_model=BudgetPerformanceResponse)
def get_budget_performance(
    filters: Annotated[BudgetPerformanceFilters, Depends(_parse_budget_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> BudgetPerformanceResponse:
    """Return allocation-level actual vs planned budget metrics for a month."""
    service = AnalyticsService(db)
    return service.get_budget_performance(user_id=user.id, filters=filters)


@router.get("/monthly-comparison", response_model=MonthlyComparisonResponse)
def get_monthly_comparison(
    filters: Annotated[MonthlyComparisonFilters, Depends(_parse_comparison_filters)],
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> MonthlyComparisonResponse:
    """Return comparative metrics across past N months."""
    service = AnalyticsService(db)
    return service.get_monthly_comparison(user_id=user.id, filters=filters)
