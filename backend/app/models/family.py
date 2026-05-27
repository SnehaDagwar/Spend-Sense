"""Family wallet models.

Stores family containers, their members, and explicit settlement transactions.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
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
from app.models.enums import (
    CurrencyCode,
    FamilyRole,
    SettlementStatus,
    enum_values,
)


class Family(Base):
    """Family wallet container — one per user."""

    __tablename__ = "families"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Family Wallet",
        server_default="Family Wallet",
    )
    currency: Mapped[CurrencyCode] = mapped_column(
        Enum(CurrencyCode, name="currency_code", values_callable=enum_values, create_type=False),
        nullable=False,
        default=CurrencyCode.INR,
        server_default="INR",
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
    owner: Mapped["User"] = relationship(back_populates="family")  # noqa: F821
    members: Mapped[list["FamilyMember"]] = relationship(
        back_populates="family",
        cascade="all, delete-orphan",
    )
    settlements: Mapped[list["Settlement"]] = relationship(
        back_populates="family",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(name)) > 0",
            name="families_name_chk",
        ),
        Index("families_owner_user_uidx", "owner_user_id", unique=True),
    )


class FamilyMember(Base):
    """Family participant.

    May optionally link to a real user account via ``user_id``.
    """

    __tablename__ = "family_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[FamilyRole] = mapped_column(
        Enum(FamilyRole, name="family_role", values_callable=enum_values),
        nullable=False,
        default=FamilyRole.MEMBER,
        server_default="Member",
    )
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    spending_limit: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
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
    family: Mapped["Family"] = relationship(back_populates="members")
    linked_user: Mapped["User | None"] = relationship(  # noqa: F821
        back_populates="family_memberships",
        foreign_keys=[user_id],
    )
    paid_expenses: Mapped[list["Expense"]] = relationship(  # noqa: F821
        back_populates="paid_by_member",
        foreign_keys="[Expense.paid_by_member_id]",
    )
    expense_splits: Mapped[list["ExpenseSplit"]] = relationship(  # noqa: F821
        back_populates="member",
    )
    settlements_from: Mapped[list["Settlement"]] = relationship(
        back_populates="from_member",
        foreign_keys="[Settlement.from_member_id]",
    )
    settlements_to: Mapped[list["Settlement"]] = relationship(
        back_populates="to_member",
        foreign_keys="[Settlement.to_member_id]",
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(name)) > 0",
            name="family_members_name_chk",
        ),
        CheckConstraint(
            "spending_limit IS NULL OR spending_limit >= 0",
            name="family_members_spending_limit_chk",
        ),
        Index("family_members_family_idx", "family_id", "is_active"),
        Index(
            "family_members_family_email_uidx",
            "family_id",
            func.lower(email),
            unique=True,
            postgresql_where=text("email IS NOT NULL"),
        ),
    )


class Settlement(Base):
    """Explicit settlement transaction between family members."""

    __tablename__ = "settlements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("family_members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    to_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("family_members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[CurrencyCode] = mapped_column(
        Enum(CurrencyCode, name="currency_code", values_callable=enum_values, create_type=False),
        nullable=False,
        default=CurrencyCode.INR,
        server_default="INR",
    )
    status: Mapped[SettlementStatus] = mapped_column(
        Enum(
            SettlementStatus,
            name="settlement_status",
            values_callable=enum_values,
        ),
        nullable=False,
        default=SettlementStatus.PENDING,
        server_default="pending",
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    family: Mapped["Family"] = relationship(back_populates="settlements")
    from_member: Mapped["FamilyMember"] = relationship(
        back_populates="settlements_from",
        foreign_keys=[from_member_id],
    )
    to_member: Mapped["FamilyMember"] = relationship(
        back_populates="settlements_to",
        foreign_keys=[to_member_id],
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="settlements_amount_chk"),
        CheckConstraint(
            "from_member_id <> to_member_id",
            name="settlements_members_distinct_chk",
        ),
        CheckConstraint(
            "(status <> 'settled' AND settled_at IS NULL) "
            "OR (status = 'settled' AND settled_at IS NOT NULL)",
            name="settlements_settled_at_chk",
        ),
        Index(
            "settlements_family_status_idx",
            "family_id",
            "status",
            created_at.desc(),
        ),
    )
