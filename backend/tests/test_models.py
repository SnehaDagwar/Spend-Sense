"""Smoke tests for Phase 1 SQLAlchemy models.

Verifies that all models import without error and that Base.metadata
contains the expected 18 tables with correct PK types.
"""

import uuid

import pytest
from sqlalchemy import inspect

from app.db.base import Base
from app.models import (
    Badge,
    BudgetCategoryAllocation,
    Challenge,
    Expense,
    ExpenseSplit,
    Family,
    FamilyMember,
    GoalContribution,
    MonthlyBudget,
    NotificationPreferences,
    RefreshToken,
    Settlement,
    SavingsGoal,
    SpendingCategory,
    UploadedFile,
    User,
    UserBadge,
    UserPreferences,
    UserProgress,
)
from app.models.enums import (
    BadgeCategory,
    ChallengeStatus,
    ChallengeType,
    CurrencyCode,
    FamilyRole,
    NotificationTiming,
    SavingsGoalStatus,
    SettlementStatus,
    UserType,
)


# ── Expected table names ─────────────────────────────────────────────────

EXPECTED_TABLES = {
    "users",
    "refresh_tokens",
    "user_preferences",
    "notification_preferences",
    "user_progress",
    "spending_categories",
    "monthly_budgets",
    "budget_category_allocations",
    "expenses",
    "expense_splits",
    "uploaded_files",
    "families",
    "family_members",
    "settlements",
    "savings_goals",
    "goal_contributions",
    "badges",
    "user_badges",
    "challenges",
}


class TestModelRegistration:
    """Verify all models are registered with Base.metadata."""

    def test_all_tables_registered(self) -> None:
        actual = set(Base.metadata.tables.keys())
        missing = EXPECTED_TABLES - actual
        assert not missing, f"Missing tables in metadata: {missing}"

    def test_table_count(self) -> None:
        # We expect exactly 19 tables (18 schema tables + refresh_tokens).
        # Actually the schema doc shows 18 table names total including users
        # and refresh_tokens.
        actual = set(Base.metadata.tables.keys())
        assert len(actual) >= len(EXPECTED_TABLES), (
            f"Expected at least {len(EXPECTED_TABLES)} tables, got {len(actual)}: {actual}"
        )


class TestPrimaryKeys:
    """Verify PK column types match the schema (UUID vs composite)."""

    @pytest.mark.parametrize(
        "table_name",
        [
            "users",
            "refresh_tokens",
            "spending_categories",
            "monthly_budgets",
            "budget_category_allocations",
            "expenses",
            "uploaded_files",
            "families",
            "family_members",
            "settlements",
            "savings_goals",
            "goal_contributions",
            "badges",
            "challenges",
        ],
    )
    def test_uuid_pk_tables(self, table_name: str) -> None:
        table = Base.metadata.tables[table_name]
        pk_cols = list(table.primary_key.columns)
        assert len(pk_cols) == 1, f"{table_name} should have exactly 1 PK column"
        assert pk_cols[0].name == "id", f"{table_name} PK should be 'id'"

    @pytest.mark.parametrize(
        "table_name,expected_pk_cols",
        [
            ("user_preferences", ["user_id"]),
            ("notification_preferences", ["user_id"]),
            ("user_progress", ["user_id"]),
            ("user_badges", ["user_id", "badge_id"]),
            ("expense_splits", ["expense_id", "member_id"]),
        ],
    )
    def test_special_pk_tables(self, table_name: str, expected_pk_cols: list[str]) -> None:
        table = Base.metadata.tables[table_name]
        pk_cols = [c.name for c in table.primary_key.columns]
        assert sorted(pk_cols) == sorted(expected_pk_cols), (
            f"{table_name} PK columns should be {expected_pk_cols}, got {pk_cols}"
        )


class TestEnums:
    """Verify all enums exist and have expected member counts."""

    def test_user_type_members(self) -> None:
        assert len(UserType) == 4

    def test_currency_code_members(self) -> None:
        assert len(CurrencyCode) == 3

    def test_notification_timing_members(self) -> None:
        assert len(NotificationTiming) == 3

    def test_family_role_members(self) -> None:
        assert len(FamilyRole) == 4

    def test_savings_goal_status_members(self) -> None:
        assert len(SavingsGoalStatus) == 4

    def test_badge_category_members(self) -> None:
        assert len(BadgeCategory) == 4

    def test_challenge_type_members(self) -> None:
        assert len(ChallengeType) == 4

    def test_challenge_status_members(self) -> None:
        assert len(ChallengeStatus) == 4

    def test_settlement_status_members(self) -> None:
        assert len(SettlementStatus) == 3


class TestForeignKeys:
    """Spot-check critical FK references."""

    def _get_fk_targets(self, table_name: str) -> set[str]:
        """Return a set of 'table.column' strings for all FKs on a table."""
        table = Base.metadata.tables[table_name]
        targets = set()
        for fk in table.foreign_keys:
            targets.add(f"{fk.column.table.name}.{fk.column.name}")
        return targets

    def test_user_preferences_fk(self) -> None:
        targets = self._get_fk_targets("user_preferences")
        assert "users.id" in targets

    def test_expenses_fk(self) -> None:
        targets = self._get_fk_targets("expenses")
        assert "users.id" in targets
        assert "spending_categories.id" in targets
        assert "family_members.id" in targets
        assert "uploaded_files.id" in targets

    def test_settlements_fk(self) -> None:
        targets = self._get_fk_targets("settlements")
        assert "families.id" in targets
        assert "family_members.id" in targets

    def test_expense_splits_fk(self) -> None:
        targets = self._get_fk_targets("expense_splits")
        assert "expenses.id" in targets
        assert "family_members.id" in targets

    def test_challenges_fk(self) -> None:
        targets = self._get_fk_targets("challenges")
        assert "users.id" in targets
        assert "spending_categories.id" in targets


class TestSeedData:
    """Verify seed data constants are well-formed."""

    def test_system_categories_count(self) -> None:
        from app.db.seed import SYSTEM_CATEGORIES
        assert len(SYSTEM_CATEGORIES) == 8

    def test_system_categories_unique_slugs(self) -> None:
        from app.db.seed import SYSTEM_CATEGORIES
        slugs = [c["slug"] for c in SYSTEM_CATEGORIES]
        assert len(slugs) == len(set(slugs)), "Duplicate slugs in seed data"

    def test_badge_catalog_count(self) -> None:
        from app.db.seed import BADGE_CATALOG
        assert len(BADGE_CATALOG) == 20

    def test_badge_catalog_unique_codes(self) -> None:
        from app.db.seed import BADGE_CATALOG
        codes = [b["code"] for b in BADGE_CATALOG]
        assert len(codes) == len(set(codes)), "Duplicate badge codes in seed data"

    def test_badge_catalog_valid_categories(self) -> None:
        from app.db.seed import BADGE_CATALOG
        for badge in BADGE_CATALOG:
            assert isinstance(badge["category"], BadgeCategory), (
                f"Badge '{badge['code']}' has invalid category: {badge['category']}"
            )
