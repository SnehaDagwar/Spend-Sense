"""Budget models.

Stores monthly budgets and their per-category planned allocations.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MonthlyBudget(Base):
    """One budget per user per month.

    The ``month`` column stores the first day of the month (e.g. 2026-05-01).
    The API layer maps ``YYYY-MM`` strings to/from this date.
    """

    __tablename__ = "monthly_budgets"

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
    month: Mapped[date] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
    )
    income: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
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
    user: Mapped["User"] = relationship(back_populates="budgets")  # noqa: F821
    category_allocations: Mapped[list["BudgetCategoryAllocation"]] = relationship(
        back_populates="budget",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "extract(day from month) = 1",
            name="monthly_budgets_month_chk",
        ),
        CheckConstraint("income >= 0", name="monthly_budgets_income_chk"),
        UniqueConstraint("user_id", "month", name="monthly_budgets_user_month_uidx"),
        Index("monthly_budgets_user_month_idx", "user_id", month.desc()),
    )


class BudgetCategoryAllocation(Base):
    """Planned amount for one category within a monthly budget."""

    __tablename__ = "budget_category_allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    budget_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monthly_budgets.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("spending_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    planned_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    display_order: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default="0",
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
    budget: Mapped["MonthlyBudget"] = relationship(
        back_populates="category_allocations",
    )
    category: Mapped["SpendingCategory"] = relationship(  # noqa: F821
        back_populates="budget_allocations",
    )

    __table_args__ = (
        CheckConstraint(
            "planned_amount >= 0",
            name="budget_category_allocations_amount_chk",
        ),
        UniqueConstraint(
            "budget_id",
            "category_id",
            name="budget_category_allocations_budget_category_uidx",
        ),
        Index(
            "budget_category_allocations_budget_idx",
            "budget_id",
        ),
    )
