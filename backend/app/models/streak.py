"""User streak model.

Tracks incremental streak counters for gamification.  Each user has at most
one row per streak type, updated in place as events arrive.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserStreak(Base):
    """Incremental streak counter — one row per (user, streak_type)."""

    __tablename__ = "user_streaks"

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
    streak_type: Mapped[str] = mapped_column(Text, nullable=False)
    current_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
    )
    longest_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
    )
    last_active_date: Mapped[date | None] = mapped_column(
        Date, nullable=True,
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
    user: Mapped["User"] = relationship(back_populates="streaks")  # noqa: F821

    __table_args__ = (
        CheckConstraint("current_count >= 0", name="user_streaks_current_count_chk"),
        CheckConstraint("longest_count >= 0", name="user_streaks_longest_count_chk"),
        Index(
            "user_streaks_user_type_uidx",
            "user_id",
            "streak_type",
            unique=True,
        ),
    )
