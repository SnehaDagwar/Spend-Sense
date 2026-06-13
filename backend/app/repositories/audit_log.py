"""Repository for the audit_logs table.

Write path: insert only (never update).
Read path: paginated cursor-based listing for a single user.
"""

from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        action: str,
        outcome: str,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        latency_ms: Optional[int] = None,
        detail: Optional[dict] = None,
    ) -> AuditLog:
        log = AuditLog(
            action=action,
            outcome=outcome,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            latency_ms=latency_ms,
            detail=detail,
        )
        self.db.add(log)
        return log

    def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 50,
        cursor_id: Optional[uuid.UUID] = None,
    ) -> Sequence[AuditLog]:
        """Return audit events for a user, newest first, with cursor pagination."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .limit(limit + 1)
        )
        if cursor_id is not None:
            stmt = stmt.where(AuditLog.id < cursor_id)

        return self.db.scalars(stmt).all()
