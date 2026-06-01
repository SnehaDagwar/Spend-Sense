"""Savings goal models.

Stores user savings targets and their contribution history.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SavingsGoalStatus, enum_values


class SavingsGoal(Base):
    """User savings target."""

    __tablename__ = "savings_goals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    monthly_contribution: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    target_date: Mapped[date | None] = mapped_column(
        DateTime(timezone=False), nullable=True,
    )
    status: Mapped[SavingsGoalStatus] = mapped_column(
        Enum(
            SavingsGoalStatus,
            name="savings_goal_status",
            values_callable=enum_values,
        ),
        nullable=False,
        default=SavingsGoalStatus.ACTIVE,
        server_default="active",
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
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
    user: Mapped["User"] = relationship(back_populates="goals")  # noqa: F821
    contributions: Mapped[list["GoalContribution"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(name)) > 0",
            name="savings_goals_name_chk",
        ),
        CheckConstraint("target_amount > 0", name="savings_goals_target_amount_chk"),
        CheckConstraint(
            "current_amount >= 0",
            name="savings_goals_current_amount_chk",
        ),
        CheckConstraint(
            "monthly_contribution >= 0",
            name="savings_goals_monthly_contribution_chk",
        ),
        CheckConstraint(
            "(status <> 'archived' AND archived_at IS NULL) "
            "OR (status = 'archived' AND archived_at IS NOT NULL)",
            name="savings_goals_archived_at_chk",
        ),
        Index(
            "savings_goals_user_status_idx",
            "user_id",
            "status",
            created_at.desc(),
        ),
    )


class GoalContribution(Base):
    """Contribution to a savings goal."""

    __tablename__ = "goal_contributions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("savings_goals.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    contributed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    goal: Mapped["SavingsGoal"] = relationship(back_populates="contributions")

    __table_args__ = (
        CheckConstraint("amount > 0", name="goal_contributions_amount_chk"),
        Index(
            "goal_contributions_goal_date_idx",
            "goal_id",
            contributed_at.desc(),
        ),
    )
