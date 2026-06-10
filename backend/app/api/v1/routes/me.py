from datetime import datetime, date
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.preferences import UserPreferences, NotificationPreferences
from app.models.progress import UserProgress
from app.models.category import SpendingCategory
from app.repositories.budget import BudgetRepository
from app.schemas.user import (
    MeResponse,
    OnboardingRequest,
    ProfileUpdateRequest,
    PreferencesUpdateRequest,
    NotificationsUpdateRequest,
)

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeResponse)
def get_me(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """Get profile preferences, notifications, and progress for the current user."""
    _ensure_user_related_rows(user, db)
    return MeResponse(
        user=user,
        preferences=user.preferences,
        notifications=user.notification_preferences,
        progress=user.progress,
    )


@router.post("/onboarding", response_model=MeResponse)
def complete_onboarding(
    payload: OnboardingRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """Save onboarding profile options, preferences and create initial month budget."""
    user.display_name = payload.display_name
    user.user_type = payload.user_type
    user.onboarding_completed = True

    # Parse month YYYY-MM
    try:
        yr, mn = map(int, payload.active_month.split("-"))
        active_date = date(yr, mn, 1)
        active_datetime = datetime(yr, mn, 1)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activeMonth format. Expected YYYY-MM.",
        ) from exc

    _ensure_user_related_rows(user, db)

    user.preferences.currency = payload.currency
    user.preferences.default_monthly_income = payload.default_monthly_income
    user.preferences.monthly_saving_target_percent = payload.monthly_saving_target_percent
    user.preferences.active_month = active_datetime

    # Setup the initial budget for the active month
    budget_repo = BudgetRepository(db)
    existing_budget = budget_repo.get_by_month_and_user(active_date, user.id)
    if not existing_budget:
        budget = budget_repo.create(
            user_id=user.id,
            month_date=active_date,
            income=payload.default_monthly_income,
        )
        db.flush()
        # Seed allocations with all system categories
        system_categories = db.scalars(
            select(SpendingCategory).where(SpendingCategory.is_system == True)
        ).all()
        for idx, cat in enumerate(system_categories):
            budget_repo.upsert_allocation(
                budget_id=budget.id,
                category_id=cat.id,
                planned_amount=Decimal("0.00"),
                display_order=idx,
            )

    db.commit()
    db.refresh(user)

    return MeResponse(
        user=user,
        preferences=user.preferences,
        notifications=user.notification_preferences,
        progress=user.progress,
    )


@router.patch("/profile", response_model=MeResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """Update user identity profile fields."""
    _ensure_user_related_rows(user, db)

    if payload.display_name is not None:
        user.display_name = payload.display_name.strip()
    if payload.user_type is not None:
        user.user_type = payload.user_type
    if payload.onboarding_completed is not None:
        user.onboarding_completed = payload.onboarding_completed

    db.commit()
    db.refresh(user)

    return MeResponse(
        user=user,
        preferences=user.preferences,
        notifications=user.notification_preferences,
        progress=user.progress,
    )


@router.patch("/preferences", response_model=MeResponse)
def update_preferences(
    payload: PreferencesUpdateRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """Update profile preferences settings."""
    _ensure_user_related_rows(user, db)

    prefs = user.preferences
    if payload.currency is not None:
        prefs.currency = payload.currency
    if payload.default_monthly_income is not None:
        prefs.default_monthly_income = payload.default_monthly_income
    if payload.financial_goals_preference is not None:
        prefs.financial_goals_preference = payload.financial_goals_preference
    if payload.preferred_start_day is not None:
        prefs.preferred_start_day = payload.preferred_start_day
    if payload.monthly_saving_target_percent is not None:
        prefs.monthly_saving_target_percent = payload.monthly_saving_target_percent
    if payload.hourly_wage is not None:
        prefs.hourly_wage = payload.hourly_wage
    if payload.avatar_url is not None:
        prefs.avatar_url = payload.avatar_url

    if payload.active_month is not None:
        try:
            yr, mn = map(int, payload.active_month.split("-"))
            prefs.active_month = datetime(yr, mn, 1)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid activeMonth format. Expected YYYY-MM.",
            ) from exc

    db.commit()
    db.refresh(user)

    return MeResponse(
        user=user,
        preferences=user.preferences,
        notifications=user.notification_preferences,
        progress=user.progress,
    )


@router.patch("/notifications", response_model=MeResponse)
def update_notifications(
    payload: NotificationsUpdateRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """Update notification rules."""
    _ensure_user_related_rows(user, db)

    notifs = user.notification_preferences
    if payload.budget_limit is not None:
        notifs.budget_limit = payload.budget_limit
    if payload.overspending is not None:
        notifs.overspending = payload.overspending
    if payload.goal_reminders is not None:
        notifs.goal_reminders = payload.goal_reminders
    if payload.daily_spending is not None:
        notifs.daily_spending = payload.daily_spending
    if payload.weekly_summary is not None:
        notifs.weekly_summary = payload.weekly_summary
    if payload.achievements is not None:
        notifs.achievements = payload.achievements
    if payload.subscription_renewal is not None:
        notifs.subscription_renewal = payload.subscription_renewal
    if payload.timing is not None:
        notifs.timing = payload.timing
    if payload.custom_time is not None:
        notifs.custom_time = payload.custom_time

    # Ensure constraint: custom time must be set if timing is Custom
    if notifs.timing == "Custom" and notifs.custom_time is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customTime is required when timing is set to Custom.",
        )
    elif notifs.timing != "Custom":
        notifs.custom_time = None

    db.commit()
    db.refresh(user)

    return MeResponse(
        user=user,
        preferences=user.preferences,
        notifications=user.notification_preferences,
        progress=user.progress,
    )


def _ensure_user_related_rows(user: User, db: Session) -> None:
    """Ensure preferences, notification_preferences, and progress rows exist in the DB."""
    updated = False
    if not user.preferences:
        user.preferences = UserPreferences(user_id=user.id)
        db.add(user.preferences)
        updated = True
    if not user.notification_preferences:
        user.notification_preferences = NotificationPreferences(user_id=user.id)
        db.add(user.notification_preferences)
        updated = True
    if not user.progress:
        user.progress = UserProgress(user_id=user.id)
        db.add(user.progress)
        updated = True

    if updated:
        db.flush()
