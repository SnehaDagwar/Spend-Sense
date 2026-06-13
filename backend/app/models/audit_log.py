"""Audit log model.

Stores a structured, PII-free record of security-relevant user actions.
Used for detecting anomalies, supporting incident response, and providing
users with their own login history.

Index strategy:
  - user_created_idx   — fetch all events for a user ordered by time
  - action_created_idx — aggregate/alert on specific action types
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    """Immutable audit log row — never updated, only inserted."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    # Nullable: pre-auth events (e.g. failed login before user is resolved)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Dotted action string, e.g. 'auth.login.success'",
    )
    resource_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    outcome: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="'success' or 'failure'",
    )
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Non-PII context: error codes, resource slugs, etc.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationship (optional — avoids join overhead in most reads)
    user: Mapped["User | None"] = relationship()  # noqa: F821

    __table_args__ = (
        Index("audit_logs_user_created_idx", "user_id", created_at.desc()),
        Index("audit_logs_action_created_idx", "action", created_at.desc()),
    )
