"""budget: add warning_threshold to monthly_budgets

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-29

Adds ``warning_threshold numeric(5,4)`` to ``monthly_budgets``.

This column stores the fraction (0.0–1.0) at which a "near limit" warning
is triggered for a budget month.  Defaults to 0.80 (80 %).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# ---------------------------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------------------------

revision = "0004_budget_warning_threshold"
down_revision = "0003_expense_extended_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "monthly_budgets",
        sa.Column(
            "warning_threshold",
            sa.Numeric(5, 4),
            nullable=False,
            server_default="0.8000",
            comment="Fraction (0-1) at which spending triggers a near-limit warning.",
        ),
    )
    op.create_check_constraint(
        "monthly_budgets_warning_threshold_chk",
        "monthly_budgets",
        "warning_threshold BETWEEN 0 AND 1",
    )


def downgrade() -> None:
    op.drop_constraint(
        "monthly_budgets_warning_threshold_chk",
        "monthly_budgets",
        type_="check",
    )
    op.drop_column("monthly_budgets", "warning_threshold")
