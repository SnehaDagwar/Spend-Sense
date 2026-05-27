"""Badge models.

Stores the system badge catalog and per-user unlock records.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import BadgeCategory, enum_values


class Badge(Base):
    """System badge catalog entry."""

    __tablename__ = "badges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[BadgeCategory] = mapped_column(
        Enum(BadgeCategory, name="badge_category", values_callable=enum_values),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    user_badges: Mapped[list["UserBadge"]] = relationship(
        back_populates="badge",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("length(trim(code)) > 0", name="badges_code_chk"),
        CheckConstraint("length(trim(name)) > 0", name="badges_name_chk"),
        Index("badges_code_uidx", func.lower(code), unique=True),
    )


class UserBadge(Base):
    """Junction: badge unlocked by a user.

    Composite primary key on (user_id, badge_id).
    """

    __tablename__ = "user_badges"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    badge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("badges.id", ondelete="CASCADE"),
        primary_key=True,
    )
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="user_badges")  # noqa: F821
    badge: Mapped["Badge"] = relationship(back_populates="user_badges")

    __table_args__ = (
        Index("user_badges_user_unlocked_idx", "user_id", unlocked_at.desc()),
    )
