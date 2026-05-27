"""Challenge model.

Stores generated daily challenge instances for gamification.
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
    Integer,
    Numeric,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ChallengeStatus, ChallengeType, enum_values


class Challenge(Base):
    """Generated daily challenge instance."""

    __tablename__ = "challenges"

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
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reward_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[ChallengeType] = mapped_column(
        Enum(ChallengeType, name="challenge_type", values_callable=enum_values),
        nullable=False,
    )
    target_value: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("spending_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    challenge_date: Mapped[date] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
    )
    status: Mapped[ChallengeStatus] = mapped_column(
        Enum(
            ChallengeStatus,
            name="challenge_status",
            values_callable=enum_values,
        ),
        nullable=False,
        default=ChallengeStatus.ACTIVE,
        server_default="active",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
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
    user: Mapped["User"] = relationship(back_populates="challenges")  # noqa: F821
    category: Mapped["SpendingCategory | None"] = relationship(  # noqa: F821
        back_populates="challenges",
    )

    __table_args__ = (
        CheckConstraint("reward_xp >= 0", name="challenges_reward_xp_chk"),
        CheckConstraint(
            "target_value IS NULL OR target_value >= 0",
            name="challenges_target_value_chk",
        ),
        CheckConstraint(
            "status NOT IN ('completed', 'claimed') OR completed_at IS NOT NULL",
            name="challenges_completed_at_chk",
        ),
        CheckConstraint(
            "status <> 'claimed' OR claimed_at IS NOT NULL",
            name="challenges_claimed_at_chk",
        ),
        Index(
            "challenges_user_date_idx",
            "user_id",
            challenge_date.desc(),
            "status",
        ),
        Index(
            "challenges_user_date_title_uidx",
            "user_id",
            "challenge_date",
            func.lower(title),
            unique=True,
        ),
    )
