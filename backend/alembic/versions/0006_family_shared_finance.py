"""family: add Owner role and family_invitations table

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-03

Changes:
- Adds 'Owner' value to the ``family_role`` PostgreSQL enum (autocommit block,
  cannot run inside a transaction).
- Creates the ``family_invitations`` table with all constraints and indexes.
"""

from __future__ import annotations

from datetime import timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# ---------------------------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------------------------

revision = "0006_family_shared_finance"
down_revision = "0005_savings_goal_extensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add 'Owner' to the existing family_role enum.
    #    ALTER TYPE … ADD VALUE cannot run inside a transaction block in
    #    PostgreSQL, so we use an autocommit context.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE family_role ADD VALUE IF NOT EXISTS 'Owner'")

    # 2. Create the family_invitations table.
    op.create_table(
        "family_invitations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "family_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("families.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "invited_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("family_members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column(
            "role",
            # Re-use the existing enum type; do NOT create a new one.
            sa.Enum(
                "Owner", "Admin", "Member", "Child",
                name="family_role",
                create_type=False,
            ),
            nullable=False,
            server_default="Member",
        ),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # Constraints
        sa.CheckConstraint(
            "position('@' in email) > 1",
            name="family_invitations_email_chk",
        ),
        sa.CheckConstraint(
            "(accepted_at IS NULL) OR (revoked_at IS NULL)",
            name="family_invitations_terminal_state_chk",
        ),
    )

    # Unique index on token_hash — enables O(1) accept-invite lookup.
    op.create_index(
        "family_invitations_token_hash_uidx",
        "family_invitations",
        ["token_hash"],
        unique=True,
    )

    # Composite index for duplicate-invite checks (family_id + lower(email)).
    op.create_index(
        "family_invitations_family_email_idx",
        "family_invitations",
        ["family_id", sa.text("lower(email)")],
    )


def downgrade() -> None:
    # Drop indexes first, then table.
    op.drop_index("family_invitations_family_email_idx", table_name="family_invitations")
    op.drop_index("family_invitations_token_hash_uidx", table_name="family_invitations")
    op.drop_table("family_invitations")

    # PostgreSQL does not support removing enum values without recreating the
    # type. We intentionally leave the 'Owner' value in place on downgrade as
    # it does not affect any other tables and avoids a costly type recreation.
