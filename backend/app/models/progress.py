"""User progress model.

Stores gamification counters (XP, level, savings streak) as a 1:1 extension
of the users table.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserProgress(Base):
    """Gamification counters — one row per user."""

    __tablename__ = "user_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    savings_streak: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
    )
    xp: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
    )
    level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1",
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
    user: Mapped["User"] = relationship(back_populates="progress")  # noqa: F821

    __table_args__ = (
        CheckConstraint("savings_streak >= 0", name="user_progress_savings_streak_chk"),
        CheckConstraint("xp >= 0", name="user_progress_xp_chk"),
        CheckConstraint("level >= 1", name="user_progress_level_chk"),
    )
