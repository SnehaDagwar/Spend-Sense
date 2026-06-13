"""audit_logs: create audit log table

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-13

Changes:
- Creates ``audit_logs`` table for structured, PII-free security event logging.
- Index on (user_id, created_at DESC) for per-user history queries.
- Index on (action, created_at DESC) for alert/aggregation queries.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# ---------------------------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------------------------

revision = "0007_audit_logs"
down_revision = "0006_family_shared_finance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "action",
            sa.Text(),
            nullable=False,
            comment="Dotted action string, e.g. 'auth.login.success'",
        ),
        sa.Column("resource_type", sa.Text(), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "outcome",
            sa.String(16),
            nullable=False,
            comment="success or failure",
        ),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "detail",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Non-PII context: error codes, resource slugs, etc.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Per-user audit history (newest first)
    op.create_index(
        "audit_logs_user_created_idx",
        "audit_logs",
        ["user_id", sa.text("created_at DESC")],
    )

    # Per-action aggregation / alerting
    op.create_index(
        "audit_logs_action_created_idx",
        "audit_logs",
        ["action", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("audit_logs_action_created_idx", table_name="audit_logs")
    op.drop_index("audit_logs_user_created_idx", table_name="audit_logs")
    op.drop_table("audit_logs")
