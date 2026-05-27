"""Spending category model.

Stores both system-default categories (user_id IS NULL, is_system = true) and
user-created custom categories.  Partial unique indexes enforce slug uniqueness
within each scope.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SpendingCategory(Base):
    """System or user-owned spending category."""

    __tablename__ = "spending_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(Text, nullable=False)
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
    )
    display_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0",
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
    user: Mapped["User | None"] = relationship(  # noqa: F821
        back_populates="categories",
    )
    budget_allocations: Mapped[list["BudgetCategoryAllocation"]] = relationship(  # noqa: F821
        back_populates="category",
    )
    expenses: Mapped[list["Expense"]] = relationship(  # noqa: F821
        back_populates="category",
    )
    challenges: Mapped[list["Challenge"]] = relationship(  # noqa: F821
        back_populates="category",
    )

    __table_args__ = (
        CheckConstraint(
            "(is_system = true AND user_id IS NULL) "
            "OR (is_system = false AND user_id IS NOT NULL)",
            name="spending_categories_owner_chk",
        ),
        CheckConstraint(
            "length(trim(slug)) > 0",
            name="spending_categories_slug_chk",
        ),
        CheckConstraint(
            "length(trim(name)) > 0",
            name="spending_categories_name_chk",
        ),
        # Partial unique index: system categories by slug
        Index(
            "spending_categories_system_slug_uidx",
            func.lower(slug),
            unique=True,
            postgresql_where=text("user_id IS NULL"),
        ),
        # Partial unique index: user categories by (user_id, slug)
        Index(
            "spending_categories_user_slug_uidx",
            "user_id",
            func.lower(slug),
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
    )
