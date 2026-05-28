"""Expense models.

Stores individual expenses and family expense splits.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CurrencyCode, PaymentMethod, enum_values


class Expense(Base):
    """Individual expense record."""

    __tablename__ = "expenses"

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
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("spending_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
    )
    note: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default="",
    )
    payment_method: Mapped[Optional[str]] = mapped_column(
        Enum(*enum_values(PaymentMethod), name="payment_method_enum", create_type=False),
        nullable=True,
    )
    merchant: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        server_default="{}",
    )
    currency: Mapped[str] = mapped_column(
        Enum(*enum_values(CurrencyCode), name="currency_code", create_type=False),
        nullable=False,
        default=CurrencyCode.INR.value,
        server_default=CurrencyCode.INR.value,
    )
    is_recurring: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
    )
    paid_by_member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("family_members.id", ondelete="SET NULL"),
        nullable=True,
    )
    receipt_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uploaded_files.id", ondelete="SET NULL"),
        nullable=True,
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
    user: Mapped["User"] = relationship(back_populates="expenses")  # noqa: F821
    category: Mapped["SpendingCategory"] = relationship(  # noqa: F821
        back_populates="expenses",
    )
    paid_by_member: Mapped["FamilyMember | None"] = relationship(  # noqa: F821
        back_populates="paid_expenses",
        foreign_keys=[paid_by_member_id],
    )
    receipt_file: Mapped["UploadedFile | None"] = relationship(  # noqa: F821
        back_populates="expenses",
        foreign_keys=[receipt_file_id],
    )
    splits: Mapped[list["ExpenseSplit"]] = relationship(
        back_populates="expense",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="expenses_amount_chk"),
        Index(
            "expenses_user_date_idx",
            "user_id",
            expense_date.desc(),
            "id",
        ),
        Index(
            "expenses_user_category_date_idx",
            "user_id",
            "category_id",
            expense_date.desc(),
        ),
        Index(
            "expenses_paid_by_member_idx",
            "paid_by_member_id",
            postgresql_where=text("paid_by_member_id IS NOT NULL"),
        ),
    )


class ExpenseSplit(Base):
    """Split participant for a family expense.

    Composite primary key on (expense_id, member_id).
    """

    __tablename__ = "expense_splits"

    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("expenses.id", ondelete="CASCADE"),
        primary_key=True,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("family_members.id", ondelete="CASCADE"),
        primary_key=True,
    )
    share_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_settled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
    )
    settled_at: Mapped[datetime | None] = mapped_column(
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
    expense: Mapped["Expense"] = relationship(back_populates="splits")
    member: Mapped["FamilyMember"] = relationship(  # noqa: F821
        back_populates="expense_splits",
    )

    __table_args__ = (
        CheckConstraint(
            "share_amount >= 0",
            name="expense_splits_share_amount_chk",
        ),
        CheckConstraint(
            "(is_settled = false AND settled_at IS NULL) "
            "OR (is_settled = true AND settled_at IS NOT NULL)",
            name="expense_splits_settled_at_chk",
        ),
        Index(
            "expense_splits_member_idx",
            "member_id",
            "is_settled",
        ),
    )
