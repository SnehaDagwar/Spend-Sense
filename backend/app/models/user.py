"""User and refresh token models.

Core authentication identity.  Relationship attributes point to all child
entities so eager/lazy loading works from the user root.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index
from sqlalchemy import String, Text, func, text
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserType, enum_values


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_type: Mapped[UserType] = mapped_column(
        Enum(UserType, name="user_type", values_callable=enum_values),
        nullable=False,
        default=UserType.PROFESSIONAL,
        server_default=UserType.PROFESSIONAL.value,
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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

    # ── Auth relationships (existing) ────────────────────────────────────
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # ── Profile 1:1 extensions (Phase 1) ─────────────────────────────────
    preferences: Mapped["UserPreferences | None"] = relationship(  # noqa: F821
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    notification_preferences: Mapped["NotificationPreferences | None"] = relationship(  # noqa: F821
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    progress: Mapped["UserProgress | None"] = relationship(  # noqa: F821
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # ── Family (1:1 owned wallet) ────────────────────────────────────────
    family: Mapped["Family | None"] = relationship(  # noqa: F821
        back_populates="owner",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="[Family.owner_user_id]",
    )
    family_memberships: Mapped[list["FamilyMember"]] = relationship(  # noqa: F821
        back_populates="linked_user",
        foreign_keys="[FamilyMember.user_id]",
    )

    # ── One-to-many children (Phase 1) ───────────────────────────────────
    categories: Mapped[list["SpendingCategory"]] = relationship(  # noqa: F821
        back_populates="user",
    )
    budgets: Mapped[list["MonthlyBudget"]] = relationship(  # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan",
    )
    expenses: Mapped[list["Expense"]] = relationship(  # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan",
    )
    uploaded_files: Mapped[list["UploadedFile"]] = relationship(  # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan",
    )
    goals: Mapped[list["SavingsGoal"]] = relationship(  # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan",
    )
    challenges: Mapped[list["Challenge"]] = relationship(  # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # ── Many-to-many (badges via user_badges) ────────────────────────────
    user_badges: Mapped[list["UserBadge"]] = relationship(  # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("position('@' in email) > 1", name="users_email_format_chk"),
        CheckConstraint(
            "length(trim(display_name)) > 0",
            name="users_display_name_not_blank_chk",
        ),
        Index("users_email_lower_uidx", func.lower(email), unique=True),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

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
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_token_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
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
    created_by_ip: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(String(512))

    user: Mapped[User] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        Index("refresh_tokens_user_id_idx", "user_id"),
        Index("refresh_tokens_token_hash_uidx", "token_hash", unique=True),
    )
