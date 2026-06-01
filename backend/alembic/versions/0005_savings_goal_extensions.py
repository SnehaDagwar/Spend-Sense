"""savings_goal: add description, priority, category and paused status

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-01

Adds three new columns to the ``savings_goals`` table:
- description (text, nullable)
- priority (text, nullable)
- category (text, nullable)

Also registers `'paused'` as a valid enum state for `savings_goal_status`.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# ---------------------------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------------------------

revision = "0005_savings_goal_extensions"
down_revision = "0004_budget_warning_threshold"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Register 'paused' status in postgres enum type 'savings_goal_status'
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block, so we use autocommit.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE savings_goal_status ADD VALUE IF NOT EXISTS 'paused'")

    # 2. Add columns to savings_goals
    op.add_column(
        "savings_goals",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "savings_goals",
        sa.Column("priority", sa.Text(), nullable=True),
    )
    op.add_column(
        "savings_goals",
        sa.Column("category", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    # 1. Drop columns
    op.drop_column("savings_goals", "category")
    op.drop_column("savings_goals", "priority")
    op.drop_column("savings_goals", "description")

    # PostgreSQL does not natively support dropping enum values without recreating the type.
    # We leave the paused value in the enum as it does not affect any active operations when
    # the column configuration is rolled back.
