"""Phase 1 — full schema foundation

Revision ID: 0002_phase1_full_schema
Revises: 0001_auth_system
Create Date: 2026-05-27

Creates all non-auth tables, enums, indexes, and constraints defined in
docs/postgresql-schema.md.  The ``users`` and ``refresh_tokens`` tables
already exist from 0001_auth_system and are not touched here.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase1_full_schema"
down_revision: str = "0001_auth_system"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ── Enum helpers ─────────────────────────────────────────────────────────

def _create_enum_safe(name: str, values: list[str]) -> None:
    """Create a PostgreSQL enum type, silently skipping if it already exists."""
    val_list = ", ".join(f"'{v}'" for v in values)
    op.execute(
        f"""
        DO $$
        BEGIN
            CREATE TYPE {name} AS ENUM ({val_list});
        EXCEPTION
            WHEN duplicate_object THEN null;
        END
        $$;
        """
    )


# ── UPGRADE ──────────────────────────────────────────────────────────────

def upgrade() -> None:
    # ── 1. Create new enum types ─────────────────────────────────────────
    _create_enum_safe("currency_code", ["INR", "USD", "EUR"])
    _create_enum_safe("notification_timing", ["Morning", "Evening", "Custom"])
    _create_enum_safe("family_role", ["Admin", "Member", "Child"])
    _create_enum_safe("savings_goal_status", ["active", "completed", "archived"])
    _create_enum_safe("badge_category", ["streaks", "savings", "discipline", "social"])
    _create_enum_safe("challenge_type", ["spending_limit", "no_category", "save_amount", "zero_spend"])
    _create_enum_safe("challenge_status", ["active", "completed", "claimed", "expired"])
    _create_enum_safe("settlement_status", ["pending", "settled", "cancelled"])

    # ── 2. Tier 0 — no new FK dependencies ───────────────────────────────

    # user_preferences
    op.create_table(
        "user_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("currency", postgresql.ENUM(name="currency_code", create_type=False), nullable=False, server_default="INR"),
        sa.Column("default_monthly_income", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("financial_goals_preference", sa.Text(), nullable=False, server_default="Balanced"),
        sa.Column("preferred_start_day", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("monthly_saving_target_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("hourly_wage", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("active_month", sa.Date(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("default_monthly_income >= 0", name="user_preferences_income_chk"),
        sa.CheckConstraint(
            "monthly_saving_target_percent IS NULL OR monthly_saving_target_percent BETWEEN 0 AND 100",
            name="user_preferences_saving_target_chk",
        ),
        sa.CheckConstraint("preferred_start_day BETWEEN 1 AND 28", name="user_preferences_start_day_chk"),
        sa.CheckConstraint("hourly_wage >= 0", name="user_preferences_hourly_wage_chk"),
        sa.CheckConstraint(
            "active_month IS NULL OR extract(day from active_month) = 1",
            name="user_preferences_active_month_chk",
        ),
    )

    # notification_preferences
    op.create_table(
        "notification_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("budget_limit", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("overspending", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("goal_reminders", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("daily_spending", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("weekly_summary", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("achievements", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("subscription_renewal", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("timing", postgresql.ENUM(name="notification_timing", create_type=False), nullable=False, server_default="Evening"),
        sa.Column("custom_time", sa.Time(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "(timing = 'Custom' AND custom_time IS NOT NULL) OR (timing <> 'Custom' AND custom_time IS NULL)",
            name="notification_preferences_custom_time_chk",
        ),
    )

    # user_progress
    op.create_table(
        "user_progress",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("savings_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("savings_streak >= 0", name="user_progress_savings_streak_chk"),
        sa.CheckConstraint("xp >= 0", name="user_progress_xp_chk"),
        sa.CheckConstraint("level >= 1", name="user_progress_level_chk"),
    )

    # badges (system catalog — no user FK)
    op.create_table(
        "badges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("icon", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", postgresql.ENUM(name="badge_category", create_type=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("length(trim(code)) > 0", name="badges_code_chk"),
        sa.CheckConstraint("length(trim(name)) > 0", name="badges_name_chk"),
    )
    op.create_index("badges_code_uidx", "badges", [sa.text("lower(code)")], unique=True)

    # uploaded_files
    op.create_table(
        "uploaded_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_provider", sa.Text(), nullable=False, server_default="local"),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=True),
        sa.Column("content_type", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("checksum_sha256", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("size_bytes IS NULL OR size_bytes >= 0", name="uploaded_files_size_chk"),
    )
    op.create_index("uploaded_files_storage_key_uidx", "uploaded_files", ["storage_key"], unique=True)
    op.create_index("uploaded_files_user_idx", "uploaded_files", ["user_id", sa.text("created_at DESC")])

    # ── 3. Tier 1 — depends on users ─────────────────────────────────────

    # spending_categories
    op.create_table(
        "spending_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("icon", sa.Text(), nullable=False),
        sa.Column("color", sa.Text(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "(is_system = true AND user_id IS NULL) OR (is_system = false AND user_id IS NOT NULL)",
            name="spending_categories_owner_chk",
        ),
        sa.CheckConstraint("length(trim(slug)) > 0", name="spending_categories_slug_chk"),
        sa.CheckConstraint("length(trim(name)) > 0", name="spending_categories_name_chk"),
    )
    op.execute(
        """
        CREATE UNIQUE INDEX spending_categories_system_slug_uidx
            ON spending_categories (lower(slug))
            WHERE user_id IS NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX spending_categories_user_slug_uidx
            ON spending_categories (user_id, lower(slug))
            WHERE user_id IS NOT NULL
        """
    )

    # families
    op.create_table(
        "families",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False, server_default="Family Wallet"),
        sa.Column("currency", postgresql.ENUM(name="currency_code", create_type=False), nullable=False, server_default="INR"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("length(trim(name)) > 0", name="families_name_chk"),
    )
    op.create_index("families_owner_user_uidx", "families", ["owner_user_id"], unique=True)

    # savings_goals
    op.create_table(
        "savings_goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("icon", sa.Text(), nullable=False),
        sa.Column("color", sa.Text(), nullable=True),
        sa.Column("target_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("current_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("monthly_contribution", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("status", postgresql.ENUM(name="savings_goal_status", create_type=False), nullable=False, server_default="active"),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("length(trim(name)) > 0", name="savings_goals_name_chk"),
        sa.CheckConstraint("target_amount > 0", name="savings_goals_target_amount_chk"),
        sa.CheckConstraint("current_amount >= 0", name="savings_goals_current_amount_chk"),
        sa.CheckConstraint("monthly_contribution >= 0", name="savings_goals_monthly_contribution_chk"),
        sa.CheckConstraint(
            "(status <> 'archived' AND archived_at IS NULL) OR (status = 'archived' AND archived_at IS NOT NULL)",
            name="savings_goals_archived_at_chk",
        ),
    )
    op.create_index("savings_goals_user_status_idx", "savings_goals", ["user_id", "status", sa.text("created_at DESC")])

    # user_badges (junction)
    op.create_table(
        "user_badges",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("badge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("badges.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("user_badges_user_unlocked_idx", "user_badges", ["user_id", sa.text("unlocked_at DESC")])

    # ── 4. Tier 2 — depends on Tier 1 ───────────────────────────────────

    # monthly_budgets
    op.create_table(
        "monthly_budgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("income", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("extract(day from month) = 1", name="monthly_budgets_month_chk"),
        sa.CheckConstraint("income >= 0", name="monthly_budgets_income_chk"),
        sa.UniqueConstraint("user_id", "month", name="monthly_budgets_user_month_uidx"),
    )
    op.create_index("monthly_budgets_user_month_idx", "monthly_budgets", ["user_id", sa.text("month DESC")])

    # family_members
    op.create_table(
        "family_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("families.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("role", postgresql.ENUM(name="family_role", create_type=False), nullable=False, server_default="Member"),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("spending_limit", sa.Numeric(14, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("length(trim(name)) > 0", name="family_members_name_chk"),
        sa.CheckConstraint("spending_limit IS NULL OR spending_limit >= 0", name="family_members_spending_limit_chk"),
    )
    op.create_index("family_members_family_idx", "family_members", ["family_id", "is_active"])
    op.execute(
        """
        CREATE UNIQUE INDEX family_members_family_email_uidx
            ON family_members (family_id, lower(email))
            WHERE email IS NOT NULL
        """
    )

    # goal_contributions
    op.create_table(
        "goal_contributions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("savings_goals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("contributed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="goal_contributions_amount_chk"),
    )
    op.create_index("goal_contributions_goal_date_idx", "goal_contributions", ["goal_id", sa.text("contributed_at DESC")])

    # ── 5. Tier 3 — depends on Tier 2 ───────────────────────────────────

    # budget_category_allocations
    op.create_table(
        "budget_category_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("budget_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monthly_budgets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("spending_categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("planned_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("planned_amount >= 0", name="budget_category_allocations_amount_chk"),
        sa.UniqueConstraint("budget_id", "category_id", name="budget_category_allocations_budget_category_uidx"),
    )
    op.create_index("budget_category_allocations_budget_idx", "budget_category_allocations", ["budget_id"])

    # expenses
    op.create_table(
        "expenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("spending_categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("paid_by_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("receipt_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("uploaded_files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="expenses_amount_chk"),
    )
    op.create_index("expenses_user_date_idx", "expenses", ["user_id", sa.text("expense_date DESC"), "id"])
    op.create_index("expenses_user_category_date_idx", "expenses", ["user_id", "category_id", sa.text("expense_date DESC")])
    op.execute(
        """
        CREATE INDEX expenses_paid_by_member_idx
            ON expenses (paid_by_member_id)
            WHERE paid_by_member_id IS NOT NULL
        """
    )

    # settlements
    op.create_table(
        "settlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("families.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("family_members.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("to_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("family_members.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", postgresql.ENUM(name="currency_code", create_type=False), nullable=False, server_default="INR"),
        sa.Column("status", postgresql.ENUM(name="settlement_status", create_type=False), nullable=False, server_default="pending"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="settlements_amount_chk"),
        sa.CheckConstraint("from_member_id <> to_member_id", name="settlements_members_distinct_chk"),
        sa.CheckConstraint(
            "(status <> 'settled' AND settled_at IS NULL) OR (status = 'settled' AND settled_at IS NOT NULL)",
            name="settlements_settled_at_chk",
        ),
    )
    op.create_index("settlements_family_status_idx", "settlements", ["family_id", "status", sa.text("created_at DESC")])

    # ── 6. Tier 4 — depends on Tier 3 ───────────────────────────────────

    # expense_splits
    op.create_table(
        "expense_splits",
        sa.Column("expense_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("expenses.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("family_members.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("share_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("is_settled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("share_amount >= 0", name="expense_splits_share_amount_chk"),
        sa.CheckConstraint(
            "(is_settled = false AND settled_at IS NULL) OR (is_settled = true AND settled_at IS NOT NULL)",
            name="expense_splits_settled_at_chk",
        ),
    )
    op.create_index("expense_splits_member_idx", "expense_splits", ["member_id", "is_settled"])

    # challenges
    op.create_table(
        "challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("reward_xp", sa.Integer(), nullable=False),
        sa.Column("type", postgresql.ENUM(name="challenge_type", create_type=False), nullable=False),
        sa.Column("target_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("spending_categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("challenge_date", sa.Date(), nullable=False),
        sa.Column("status", postgresql.ENUM(name="challenge_status", create_type=False), nullable=False, server_default="active"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("reward_xp >= 0", name="challenges_reward_xp_chk"),
        sa.CheckConstraint("target_value IS NULL OR target_value >= 0", name="challenges_target_value_chk"),
        sa.CheckConstraint(
            "status NOT IN ('completed', 'claimed') OR completed_at IS NOT NULL",
            name="challenges_completed_at_chk",
        ),
        sa.CheckConstraint(
            "status <> 'claimed' OR claimed_at IS NOT NULL",
            name="challenges_claimed_at_chk",
        ),
    )
    op.create_index("challenges_user_date_idx", "challenges", ["user_id", sa.text("challenge_date DESC"), "status"])
    op.create_index(
        "challenges_user_date_title_uidx",
        "challenges",
        ["user_id", "challenge_date", sa.text("lower(title)")],
        unique=True,
    )


# ── DOWNGRADE ────────────────────────────────────────────────────────────

def downgrade() -> None:
    # Drop tables in reverse dependency order (Tier 4 → 0)

    # Tier 4
    op.drop_index("challenges_user_date_title_uidx", table_name="challenges")
    op.drop_index("challenges_user_date_idx", table_name="challenges")
    op.drop_table("challenges")

    op.drop_index("expense_splits_member_idx", table_name="expense_splits")
    op.drop_table("expense_splits")

    # Tier 3
    op.drop_index("settlements_family_status_idx", table_name="settlements")
    op.drop_table("settlements")

    op.execute("DROP INDEX IF EXISTS expenses_paid_by_member_idx")
    op.drop_index("expenses_user_category_date_idx", table_name="expenses")
    op.drop_index("expenses_user_date_idx", table_name="expenses")
    op.drop_table("expenses")

    op.drop_index("budget_category_allocations_budget_idx", table_name="budget_category_allocations")
    op.drop_table("budget_category_allocations")

    # Tier 2
    op.drop_index("goal_contributions_goal_date_idx", table_name="goal_contributions")
    op.drop_table("goal_contributions")

    op.execute("DROP INDEX IF EXISTS family_members_family_email_uidx")
    op.drop_index("family_members_family_idx", table_name="family_members")
    op.drop_table("family_members")

    op.drop_index("monthly_budgets_user_month_idx", table_name="monthly_budgets")
    op.drop_table("monthly_budgets")

    # Tier 1
    op.drop_index("user_badges_user_unlocked_idx", table_name="user_badges")
    op.drop_table("user_badges")

    op.drop_index("savings_goals_user_status_idx", table_name="savings_goals")
    op.drop_table("savings_goals")

    op.drop_index("families_owner_user_uidx", table_name="families")
    op.drop_table("families")

    op.execute("DROP INDEX IF EXISTS spending_categories_user_slug_uidx")
    op.execute("DROP INDEX IF EXISTS spending_categories_system_slug_uidx")
    op.drop_table("spending_categories")

    # Tier 0
    op.drop_index("uploaded_files_user_idx", table_name="uploaded_files")
    op.drop_index("uploaded_files_storage_key_uidx", table_name="uploaded_files")
    op.drop_table("uploaded_files")

    op.drop_index("badges_code_uidx", table_name="badges")
    op.drop_table("badges")

    op.drop_table("user_progress")
    op.drop_table("notification_preferences")
    op.drop_table("user_preferences")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS settlement_status")
    op.execute("DROP TYPE IF EXISTS challenge_status")
    op.execute("DROP TYPE IF EXISTS challenge_type")
    op.execute("DROP TYPE IF EXISTS badge_category")
    op.execute("DROP TYPE IF EXISTS savings_goal_status")
    op.execute("DROP TYPE IF EXISTS family_role")
    op.execute("DROP TYPE IF EXISTS notification_timing")
    op.execute("DROP TYPE IF EXISTS currency_code")
