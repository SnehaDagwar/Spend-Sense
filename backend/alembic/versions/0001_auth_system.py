"""create auth tables

Revision ID: 0001_auth_system
Revises:
Create Date: 2026-05-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_auth_system"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


user_type_enum = postgresql.ENUM(
    "Student",
    "Family",
    "Professional",
    "Freelancer",
    name="user_type",
    create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE user_type AS ENUM (
                'Student',
                'Family',
                'Professional',
                'Freelancer'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END
        $$;
        """
    )

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column(
            "user_type",
            user_type_enum,
            nullable=False,
            server_default="Professional",
        ),
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("position('@' in email) > 1", name="users_email_format_chk"),
        sa.CheckConstraint(
            "length(trim(display_name)) > 0",
            name="users_display_name_not_blank_chk",
        ),
    )
    op.create_index(
        "users_email_lower_uidx",
        "users",
        [sa.text("lower(email)")],
        unique=True,
    )

    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "replaced_by_token_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("created_by_ip", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["replaced_by_token_id"],
            ["refresh_tokens.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "refresh_tokens_token_hash_uidx",
        "refresh_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "refresh_tokens_user_id_idx",
        "refresh_tokens",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("refresh_tokens_user_id_idx", table_name="refresh_tokens")
    op.drop_index("refresh_tokens_token_hash_uidx", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("users_email_lower_uidx", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS user_type")
