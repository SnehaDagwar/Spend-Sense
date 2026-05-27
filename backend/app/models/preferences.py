"""User preferences models.

Stores profile preferences and notification preferences as 1:1 extensions
of the users table.
"""

from __future__ import annotations

import uuid
from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    SmallInteger,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CurrencyCode, NotificationTiming, enum_values


class UserPreferences(Base):
    """Profile preferences — one row per user."""

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    currency: Mapped[CurrencyCode] = mapped_column(
        Enum(CurrencyCode, name="currency_code", values_callable=enum_values),
        nullable=False,
        default=CurrencyCode.INR,
        server_default="INR",
    )
    default_monthly_income: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    financial_goals_preference: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Balanced",
        server_default="Balanced",
    )
    preferred_start_day: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default="1",
    )
    monthly_saving_target_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    hourly_wage: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    active_month: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        comment="First day of the active month (YYYY-MM-01)",
    )
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="preferences")  # noqa: F821

    __table_args__ = (
        CheckConstraint(
            "default_monthly_income >= 0",
            name="user_preferences_income_chk",
        ),
        CheckConstraint(
            "monthly_saving_target_percent IS NULL "
            "OR monthly_saving_target_percent BETWEEN 0 AND 100",
            name="user_preferences_saving_target_chk",
        ),
        CheckConstraint(
            "preferred_start_day BETWEEN 1 AND 28",
            name="user_preferences_start_day_chk",
        ),
        CheckConstraint(
            "hourly_wage >= 0",
            name="user_preferences_hourly_wage_chk",
        ),
        CheckConstraint(
            "active_month IS NULL OR extract(day from active_month) = 1",
            name="user_preferences_active_month_chk",
        ),
    )


class NotificationPreferences(Base):
    """Alert preferences — one row per user."""

    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    budget_limit: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
    )
    overspending: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
    )
    goal_reminders: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
    )
    daily_spending: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
    )
    weekly_summary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
    )
    achievements: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
    )
    subscription_renewal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
    )
    timing: Mapped[NotificationTiming] = mapped_column(
        Enum(
            NotificationTiming,
            name="notification_timing",
            values_callable=enum_values,
        ),
        nullable=False,
        default=NotificationTiming.EVENING,
        server_default="Evening",
    )
    custom_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="notification_preferences",
    )

    __table_args__ = (
        CheckConstraint(
            "(timing = 'Custom' AND custom_time IS NOT NULL) "
            "OR (timing <> 'Custom' AND custom_time IS NULL)",
            name="notification_preferences_custom_time_chk",
        ),
    )
