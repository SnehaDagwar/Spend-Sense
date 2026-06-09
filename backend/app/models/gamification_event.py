"""Gamification event log model.

Stores every significant user action that the gamification engine evaluates
for badge awarding, streak tracking, and XP grants.  Events are idempotent —
a composite unique index on (user_id, event_type, event_key) prevents
double-recording.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Index,
    ForeignKey,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GamificationEvent(Base):
    """Immutable event log entry for gamification evaluation."""

    __tablename__ = "gamification_events"

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
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    event_key: Mapped[str] = mapped_column(Text, nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="gamification_events")  # noqa: F821

    __table_args__ = (
        Index(
            "gamification_events_user_type_key_uidx",
            "user_id",
            "event_type",
            "event_key",
            unique=True,
        ),
        Index(
            "gamification_events_user_type_date_idx",
            "user_id",
            "event_type",
            "event_date",
        ),
    )
