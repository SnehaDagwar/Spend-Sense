"""perf_indexes: add performance indexes for Phase 12

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-13

Changes:
- expenses: functional index on lower(note) for text search (q filter)
- expenses: functional index on lower(merchant) for text search (q filter)
- expenses: composite index on (user_id, amount DESC, id DESC) for amount-sort
- expenses: partial index on (user_id, is_recurring) for isRecurring filter
- gamification_events: index on (user_id, event_date DESC) for date-range streak scans
- refresh_tokens: partial index on (expires_at) where revoked_at IS NULL for cleanup jobs
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# ---------------------------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------------------------

revision = "0008_perf_indexes"
down_revision = "0007_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── expenses: functional indexes for q text search ───────────────────
    # These allow PostgreSQL to use an index scan instead of a seq scan
    # when the query uses func.lower(col).contains(term).
    op.create_index(
        "expenses_user_lower_note_idx",
        "expenses",
        ["user_id", sa.text("lower(note)")],
        postgresql_where=sa.text("note <> ''"),
    )
    op.create_index(
        "expenses_user_lower_merchant_idx",
        "expenses",
        ["user_id", sa.text("lower(merchant)")],
        postgresql_where=sa.text("merchant IS NOT NULL"),
    )

    # ── expenses: composite index for amount-sort cursor pagination ───────
    # Enables keyset pagination on (amount DESC, id DESC) without falling
    # back to a sequential scan.
    op.create_index(
        "expenses_user_amount_idx",
        "expenses",
        ["user_id", sa.text("amount DESC"), sa.text("id DESC")],
    )

    # ── expenses: partial index for is_recurring filter ───────────────────
    # Most expenses are not recurring; partial index keeps it small.
    op.create_index(
        "expenses_is_recurring_idx",
        "expenses",
        ["user_id", "is_recurring"],
        postgresql_where=sa.text("is_recurring = true"),
    )

    # ── gamification_events: index for date-range streak scans ───────────
    # Streak engine sometimes scans events by (user_id, event_date) range
    # rather than by event_type. This index accelerates those queries.
    op.create_index(
        "gamification_events_user_date_idx",
        "gamification_events",
        ["user_id", sa.text("event_date DESC")],
    )

    # ── refresh_tokens: partial index for active-token expiry cleanup ─────
    # A cleanup job deleting expired, non-revoked tokens benefits from this.
    op.create_index(
        "refresh_tokens_active_expires_idx",
        "refresh_tokens",
        [sa.text("expires_at DESC")],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("refresh_tokens_active_expires_idx", table_name="refresh_tokens")
    op.drop_index("gamification_events_user_date_idx", table_name="gamification_events")
    op.drop_index("expenses_is_recurring_idx", table_name="expenses")
    op.drop_index("expenses_user_amount_idx", table_name="expenses")
    op.drop_index("expenses_user_lower_merchant_idx", table_name="expenses")
    op.drop_index("expenses_user_lower_note_idx", table_name="expenses")
