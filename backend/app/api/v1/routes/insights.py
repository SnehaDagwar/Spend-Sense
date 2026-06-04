"""FastAPI route handlers for AI Insights & Financial Intelligence endpoints.

All endpoints require a valid JWT access token (Bearer token).
"""

from __future__ import annotations

import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.insights import (
    FinancialSummaryInsight,
    SpendingPatternInsight,
    RecommendationsInsight,
    AnomaliesInsight,
    MonthlyReviewInsight,
)
from app.services.ai import AIService
from app.services.ai.providers import (
    AIConfigurationError,
    AIProviderError,
    AIRateLimitError,
    AIError,
)

router = APIRouter(prefix="/insights", tags=["insights"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_month(month: Optional[str]) -> str:
    """Validate and resolve the target month query parameter, defaulting to current calendar month."""
    if month is None:
        return datetime.date.today().strftime("%Y-%m")
    return month


def _handle_ai_error(exc: Exception) -> None:
    """Map service-layer AI exceptions to standardized Fast API HTTPExceptions."""
    if isinstance(exc, AIRateLimitError):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "code": "rate_limit_error",
                    "message": str(exc)
                }
            }
        ) from exc
        
    elif isinstance(exc, AIConfigurationError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "internal_error",
                    "message": f"AI service configuration mismatch: {exc}"
                }
            }
        ) from exc
        
    elif isinstance(exc, AIProviderError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": {
                    "code": "bad_gateway",
                    "message": f"LLM provider error occurred: {exc}"
                }
            }
        ) from exc
        
    elif isinstance(exc, AIError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "internal_error",
                    "message": f"AI intelligence processing failed: {exc}"
                }
            }
        ) from exc
        
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(exc)
    ) from exc


# ---------------------------------------------------------------------------
# Route Handlers
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=FinancialSummaryInsight)
async def get_summary_insight(
    month: Annotated[
        Optional[str],
        Query(pattern=r"^\d{4}-\d{2}$", description="Month target (YYYY-MM). Defaults to current month.")
    ] = None,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> FinancialSummaryInsight:
    """Return an overall financial health diagnostics summary and alerts."""
    resolved_month = _resolve_month(month)
    service = AIService(db)
    try:
        return await service.get_summary_insight(user=user, month=resolved_month)
    except Exception as exc:
        _handle_ai_error(exc)


@router.get("/spending-patterns", response_model=SpendingPatternInsight)
async def get_spending_patterns_insight(
    month: Annotated[
        Optional[str],
        Query(pattern=r"^\d{4}-\d{2}$", description="Month target (YYYY-MM). Defaults to current month.")
    ] = None,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> SpendingPatternInsight:
    """Return deep-dive spending patterns, payment methods frequency, and subscription checks."""
    resolved_month = _resolve_month(month)
    service = AIService(db)
    try:
        return await service.get_spending_patterns_insight(user=user, month=resolved_month)
    except Exception as exc:
        _handle_ai_error(exc)


@router.get("/recommendations", response_model=RecommendationsInsight)
async def get_recommendations_insight(
    month: Annotated[
        Optional[str],
        Query(pattern=r"^\d{4}-\d{2}$", description="Month target (YYYY-MM). Defaults to current month.")
    ] = None,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> RecommendationsInsight:
    """Return recommendations on category budget modifications and savings targets milestones."""
    resolved_month = _resolve_month(month)
    service = AIService(db)
    try:
        return await service.get_recommendations_insight(user=user, month=resolved_month)
    except Exception as exc:
        _handle_ai_error(exc)


@router.get("/anomalies", response_model=AnomaliesInsight)
async def get_anomalies_insight(
    month: Annotated[
        Optional[str],
        Query(pattern=r"^\d{4}-\d{2}$", description="Month target (YYYY-MM). Defaults to current month.")
    ] = None,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> AnomaliesInsight:
    """Inspect transaction parameters to audit potential duplicate spends or spikes."""
    resolved_month = _resolve_month(month)
    service = AIService(db)
    try:
        return await service.get_anomalies_insight(user=user, month=resolved_month)
    except Exception as exc:
        _handle_ai_error(exc)


@router.get("/monthly-review", response_model=MonthlyReviewInsight)
async def get_monthly_review_insight(
    month: Annotated[
        Optional[str],
        Query(pattern=r"^\d{4}-\d{2}$", description="Month target (YYYY-MM). Defaults to current month.")
    ] = None,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> MonthlyReviewInsight:
    """Return month-end summary statistics compared chronologically with prior cycles."""
    resolved_month = _resolve_month(month)
    service = AIService(db)
    try:
        return await service.get_monthly_review_insight(user=user, month=resolved_month)
    except Exception as exc:
        _handle_ai_error(exc)
