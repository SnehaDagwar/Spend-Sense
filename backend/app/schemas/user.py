import uuid
from datetime import datetime, time
from decimal import Decimal
from typing import Any

from pydantic import EmailStr, Field

from app.models.enums import CurrencyCode, NotificationTiming, UserType
from app.schemas.base import APIModel


class UserPublic(APIModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str
    user_type: UserType
    onboarding_completed: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserPreferencesPublic(APIModel):
    currency: CurrencyCode
    default_monthly_income: Decimal
    financial_goals_preference: str
    preferred_start_day: int
    monthly_saving_target_percent: Decimal | None
    hourly_wage: Decimal
    active_month: str | None = None  # YYYY-MM
    avatar_url: str | None = None

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> "UserPreferencesPublic":
        # Handle conversion of active_month datetime to YYYY-MM string
        validated = super().model_validate(obj, **kwargs)
        if hasattr(obj, "active_month") and obj.active_month:
            validated.active_month = obj.active_month.strftime("%Y-%m")
        return validated


class NotificationPreferencesPublic(APIModel):
    budget_limit: bool
    overspending: bool
    goal_reminders: bool
    daily_spending: bool
    weekly_summary: bool
    achievements: bool
    subscription_renewal: bool
    timing: NotificationTiming
    custom_time: time | None = None


class UserProgressPublic(APIModel):
    savings_streak: int
    xp: int
    level: int


class MeResponse(APIModel):
    user: UserPublic
    preferences: UserPreferencesPublic | None = None
    notifications: NotificationPreferencesPublic | None = None
    progress: UserProgressPublic | None = None


class OnboardingRequest(APIModel):
    display_name: str = Field(min_length=1, max_length=100)
    user_type: UserType
    currency: CurrencyCode
    default_monthly_income: Decimal = Field(ge=0)
    monthly_saving_target_percent: Decimal = Field(ge=0, le=100)
    active_month: str = Field(pattern=r"^\d{4}-\d{2}$")


class ProfileUpdateRequest(APIModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    user_type: UserType | None = None
    onboarding_completed: bool | None = None


class PreferencesUpdateRequest(APIModel):
    currency: CurrencyCode | None = None
    default_monthly_income: Decimal | None = Field(default=None, ge=0)
    financial_goals_preference: str | None = None
    preferred_start_day: int | None = Field(default=None, ge=1, le=28)
    monthly_saving_target_percent: Decimal | None = Field(default=None, ge=0, le=100)
    hourly_wage: Decimal | None = Field(default=None, ge=0)
    active_month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    avatar_url: str | None = None


class NotificationsUpdateRequest(APIModel):
    budget_limit: bool | None = None
    overspending: bool | None = None
    goal_reminders: bool | None = None
    daily_spending: bool | None = None
    weekly_summary: bool | None = None
    achievements: bool | None = None
    subscription_renewal: bool | None = None
    timing: NotificationTiming | None = None
    custom_time: time | None = None

