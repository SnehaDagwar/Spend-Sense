"""Audit logging helpers.

Provides AuditAction string constants and a record_audit() helper
that writes to the audit_logs table without raising on failure.

Design decisions:
- No PII is stored in the detail JSONB — only error codes, resource IDs.
- record_audit() swallows exceptions silently so a logging failure
  never blocks a user-facing response.
- The caller is responsible for committing the DB session; audit rows
  are flushed (not committed) by record_audit.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AuditAction:
    """String constants for audit action names."""

    # Auth
    AUTH_REGISTER_SUCCESS = "auth.register.success"
    AUTH_REGISTER_FAILURE = "auth.register.failure"
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_REFRESH_SUCCESS = "auth.refresh.success"
    AUTH_REFRESH_FAILURE = "auth.refresh.failure"

    # Expenses
    EXPENSE_CREATE = "expense.create"
    EXPENSE_UPDATE = "expense.update"
    EXPENSE_DELETE = "expense.delete"

    # Goals
    GOAL_CREATE = "goal.create"
    GOAL_CONTRIBUTION = "goal.contribution"

    # Family
    FAMILY_INVITE = "family.invite"
    FAMILY_MEMBER_REMOVE = "family.member.remove"


def record_audit(
    db: Session,
    *,
    action: str,
    outcome: str,                        # "success" | "failure"
    user_id: Any | None = None,
    resource_type: str | None = None,
    resource_id: Any | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    latency_ms: int | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    """Insert one audit log row and flush (without committing).

    Silently swallows all exceptions so audit failures never surface to users.
    """
    try:
        from app.models.audit_log import AuditLog  # local import avoids circular deps

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
        db.add(log)
        db.flush()
    except Exception:  # noqa: BLE001
        logger.warning("audit log write failed for action=%s", action, exc_info=True)
