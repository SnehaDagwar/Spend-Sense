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
    {
        "code": "early_bird",
        "name": "Early Bird",
        "icon": "zap",
        "description": "Log your first expense before 8 AM",
        "category": BadgeCategory.DISCIPLINE,
    },
    {
        "code": "week_warrior",
        "name": "Week Warrior",
        "icon": "flame",
        "description": "Maintain a 7-day logging streak",
        "category": BadgeCategory.STREAKS,
    },
    {
        "code": "penny_pincher",
        "name": "Penny Pincher",
        "icon": "shield",
        "description": "Stay under ₹200 for 3 days in a row",
        "category": BadgeCategory.DISCIPLINE,
    },
    {
        "code": "master_saver",
        "name": "Master Saver",
        "icon": "target",
        "description": "Contribute to 5 different goals",
        "category": BadgeCategory.SAVINGS,
    },
    {
        "code": "gold_standard",
        "name": "Gold Standard",
        "icon": "star",
        "description": "Complete 10 daily challenges",
        "category": BadgeCategory.STREAKS,
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
