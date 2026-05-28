"""expense: add extended fields (payment_method, merchant, tags, currency, is_recurring)

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-28

Adds five new columns to the ``expenses`` table that support the Phase 2
expense features:

- payment_method  nullable enum (payment_method_enum)
- merchant        nullable varchar(200)
- tags            not-null text[] default '{}'
- currency        not-null currency_code enum default 'INR'
- is_recurring    not-null boolean default false

The ``currency_code`` PostgreSQL enum already exists (created by migration
0002). ``payment_method_enum`` is created here and dropped on downgrade.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------------------------

revision = "0003_expense_extended_fields"
down_revision = "0002_phase1_full_schema"
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# Enum helpers
# ---------------------------------------------------------------------------

payment_method_enum = postgresql.ENUM(
    "cash",
    "card",
    "upi",
    "bank_transfer",
    "wallet",
    "other",
    name="payment_method_enum",
    create_type=False,  # we manage creation manually below
)


def upgrade() -> None:
    # Create the new enum type first
    payment_method_enum_type = sa.Enum(
        "cash",
        "card",
        "upi",
        "bank_transfer",
        "wallet",
        "other",
        name="payment_method_enum",
    )
    payment_method_enum_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "expenses",
        sa.Column(
            "payment_method",
            payment_method_enum,
            nullable=True,
        ),
    )
    op.add_column(
        "expenses",
        sa.Column("merchant", sa.String(200), nullable=True),
    )
    op.add_column(
        "expenses",
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )
    # currency_code enum was created in migration 0002 — reference without create
    currency_code_enum = postgresql.ENUM(
        "INR", "USD", "EUR",
        name="currency_code",
        create_type=False,
    )
    op.add_column(
        "expenses",
        sa.Column(
            "currency",
            currency_code_enum,
            nullable=False,
            server_default="INR",
        ),
    )
    op.add_column(
        "expenses",
        sa.Column(
            "is_recurring",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # GIN index for efficient tag array containment queries
    op.create_index(
        "expenses_tags_gin_idx",
        "expenses",
        ["tags"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("expenses_tags_gin_idx", table_name="expenses")
    op.drop_column("expenses", "is_recurring")
    op.drop_column("expenses", "currency")
    op.drop_column("expenses", "tags")
    op.drop_column("expenses", "merchant")
    op.drop_column("expenses", "payment_method")

    # Drop the enum type we created
    sa.Enum(name="payment_method_enum").drop(op.get_bind(), checkfirst=True)
