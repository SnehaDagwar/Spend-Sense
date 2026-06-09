"""Seed system spending categories and the initial badge catalog.

Run from the backend directory:

    python -m app.db.seed

The script is idempotent — it uses INSERT ... ON CONFLICT DO NOTHING
semantics so re-running it is safe.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.badge import Badge
from app.models.category import SpendingCategory
from app.models.enums import BadgeCategory


# ── System spending categories ───────────────────────────────────────────
# Matches the seed table in docs/postgresql-schema.md

SYSTEM_CATEGORIES: list[dict] = [
    {"slug": "food", "name": "Food", "icon": "UtensilsCrossed", "color": "hsl(var(--cat-food))", "display_order": 0},
    {"slug": "shopping", "name": "Shopping", "icon": "ShoppingBag", "color": "hsl(var(--cat-shopping))", "display_order": 1},
    {"slug": "recharge", "name": "Recharge", "icon": "Smartphone", "color": "hsl(var(--cat-recharge))", "display_order": 2},
    {"slug": "transport", "name": "Transport", "icon": "Bus", "color": "hsl(var(--cat-transport))", "display_order": 3},
    {"slug": "rent", "name": "Rent", "icon": "Home", "color": "hsl(var(--cat-rent))", "display_order": 4},
    {"slug": "medical", "name": "Medical", "icon": "Stethoscope", "color": "hsl(var(--cat-medical))", "display_order": 5},
    {"slug": "electricity", "name": "Electricity", "icon": "Zap", "color": "hsl(var(--cat-electricity))", "display_order": 6},
    {"slug": "others", "name": "Others", "icon": "MoreHorizontal", "color": "hsl(var(--cat-others))", "display_order": 7},
]


# ── Badge catalog ────────────────────────────────────────────────────────
# Extracted from the frontend BadgeGrid component (src/components/streaks/BadgeGrid.tsx)

BADGE_CATALOG: list[dict] = [
    # ── Expense Tracking ─────────────────────────────────────────────────
    {
        "code": "first_expense",
        "name": "First Expense",
        "icon": "receipt",
        "description": "Log your very first expense",
        "category": BadgeCategory.DISCIPLINE,
    },
    {
        "code": "expense_10",
        "name": "Expense Tracker",
        "icon": "clipboard-list",
        "description": "Log 10 expenses",
        "category": BadgeCategory.DISCIPLINE,
    },
    {
        "code": "expense_50",
        "name": "Expense Master",
        "icon": "bar-chart",
        "description": "Log 50 expenses",
        "category": BadgeCategory.DISCIPLINE,
    },
    {
        "code": "expense_100",
        "name": "Expense Legend",
        "icon": "crown",
        "description": "Log 100 expenses — legendary discipline!",
        "category": BadgeCategory.DISCIPLINE,
    },
    # ── Budget ───────────────────────────────────────────────────────────
    {
        "code": "budget_creator",
        "name": "Budget Creator",
        "icon": "calculator",
        "description": "Create your first monthly budget",
        "category": BadgeCategory.DISCIPLINE,
    },
    {
        "code": "budget_3_months",
        "name": "Budget Planner",
        "icon": "calendar",
        "description": "Create budgets for 3 different months",
        "category": BadgeCategory.DISCIPLINE,
    },
    {
        "code": "budget_discipline",
        "name": "Budget Discipline",
        "icon": "shield",
        "description": "Stay under budget for a full month",
        "category": BadgeCategory.DISCIPLINE,
    },
    {
        "code": "budget_discipline_3",
        "name": "Budget Master",
        "icon": "shield-check",
        "description": "Stay under budget for 3 consecutive months",
        "category": BadgeCategory.DISCIPLINE,
    },
    # ── Savings ──────────────────────────────────────────────────────────
    {
        "code": "savings_starter",
        "name": "Savings Starter",
        "icon": "piggy-bank",
        "description": "Create your first savings goal",
        "category": BadgeCategory.SAVINGS,
    },
    {
        "code": "savings_first_contrib",
        "name": "First Contribution",
        "icon": "coins",
        "description": "Make your first savings contribution",
        "category": BadgeCategory.SAVINGS,
    },
    {
        "code": "savings_master",
        "name": "Savings Master",
        "icon": "target",
        "description": "Complete a savings goal — target reached!",
        "category": BadgeCategory.SAVINGS,
    },
    {
        "code": "savings_3_goals",
        "name": "Goal Setter",
        "icon": "flag",
        "description": "Create 3 or more savings goals",
        "category": BadgeCategory.SAVINGS,
    },
    # ── Streaks ──────────────────────────────────────────────────────────
    {
        "code": "streak_3_day",
        "name": "3-Day Streak",
        "icon": "zap",
        "description": "Log expenses 3 days in a row",
        "category": BadgeCategory.STREAKS,
    },
    {
        "code": "streak_7_day",
        "name": "Weekly Warrior",
        "icon": "flame",
        "description": "Maintain a 7-day logging streak",
        "category": BadgeCategory.STREAKS,
    },
    {
        "code": "streak_30_day",
        "name": "Monthly Champion",
        "icon": "trophy",
        "description": "Log expenses every day for 30 days",
        "category": BadgeCategory.STREAKS,
    },
    {
        "code": "streak_weekly_4",
        "name": "4-Week Active",
        "icon": "activity",
        "description": "Stay active for 4 consecutive weeks",
        "category": BadgeCategory.STREAKS,
    },
    {
        "code": "streak_monthly_3",
        "name": "Quarterly Pro",
        "icon": "award",
        "description": "Maintain budget discipline for 3 consecutive months",
        "category": BadgeCategory.STREAKS,
    },
    # ── Challenge Achievements ───────────────────────────────────────────
    {
        "code": "no_spend_day",
        "name": "No-Spend Hero",
        "icon": "lock",
        "description": "Complete a zero-spend challenge",
        "category": BadgeCategory.DISCIPLINE,
    },
    {
        "code": "challenge_5",
        "name": "Challenge Seeker",
        "icon": "star",
        "description": "Complete 5 challenges",
        "category": BadgeCategory.DISCIPLINE,
    },
    {
        "code": "challenge_10",
        "name": "Challenge Champion",
        "icon": "medal",
        "description": "Complete 10 challenges — unstoppable!",
        "category": BadgeCategory.DISCIPLINE,
    },
]


def seed_system_categories(db: Session) -> int:
    """Insert system spending categories.

    Returns the number of rows inserted (skips existing).
    """
    inserted = 0
    for cat_data in SYSTEM_CATEGORIES:
        # Check if already exists by slug (case-insensitive)
        exists = db.execute(
            text(
                "SELECT 1 FROM spending_categories "
                "WHERE lower(slug) = lower(:slug) AND user_id IS NULL"
            ),
            {"slug": cat_data["slug"]},
        ).scalar()
        if exists:
            continue

        category = SpendingCategory(
            user_id=None,
            slug=cat_data["slug"],
            name=cat_data["name"],
            icon=cat_data["icon"],
            color=cat_data["color"],
            is_system=True,
            is_archived=False,
            display_order=cat_data["display_order"],
        )
        db.add(category)
        inserted += 1

    return inserted


def seed_badge_catalog(db: Session) -> int:
    """Insert the initial badge catalog.

    Returns the number of rows inserted (skips existing).
    """
    inserted = 0
    for badge_data in BADGE_CATALOG:
        exists = db.execute(
            text("SELECT 1 FROM badges WHERE lower(code) = lower(:code)"),
            {"code": badge_data["code"]},
        ).scalar()
        if exists:
            continue

        badge = Badge(
            code=badge_data["code"],
            name=badge_data["name"],
            icon=badge_data["icon"],
            description=badge_data["description"],
            category=badge_data["category"],
        )
        db.add(badge)
        inserted += 1

    return inserted


def run_seed() -> None:
    """Execute all seed operations."""
    db = SessionLocal()
    try:
        cat_count = seed_system_categories(db)
        badge_count = seed_badge_catalog(db)
        db.commit()
        print(f"Seed complete: {cat_count} categories, {badge_count} badges inserted.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
