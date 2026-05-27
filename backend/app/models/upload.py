"""Uploaded file model.

Stores receipt metadata.  Actual file bytes live on local disk or object
storage — only the reference is kept here.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UploadedFile(Base):
    """Receipt / attachment metadata."""

    __tablename__ = "uploaded_files"

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
    storage_provider: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="local",
        server_default="local",
    )
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="uploaded_files")  # noqa: F821
    expenses: Mapped[list["Expense"]] = relationship(  # noqa: F821
        back_populates="receipt_file",
    )

    __table_args__ = (
        CheckConstraint(
            "size_bytes IS NULL OR size_bytes >= 0",
            name="uploaded_files_size_chk",
        ),
        Index(
            "uploaded_files_storage_key_uidx",
            "storage_key",
            unique=True,
        ),
        Index(
            "uploaded_files_user_idx",
            "user_id",
            created_at.desc(),
        ),
    )
