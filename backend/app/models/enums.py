"""Shared enum types used across SQLAlchemy models.

All PostgreSQL enum types are defined here so models can import them from
a single module and Alembic migrations can reference the canonical names.
"""

from __future__ import annotations

import enum


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    """Return the *values* list for a Python enum.

    Used as ``values_callable`` in SQLAlchemy ``Enum()`` columns so the DB
    enum entries match the human-readable value strings, not the Python
    member names.
    """
    return [item.value for item in enum_cls]


# ── Auth / User ──────────────────────────────────────────────────────────

class UserType(str, enum.Enum):
    STUDENT = "Student"
    FAMILY = "Family"
    PROFESSIONAL = "Professional"
    FREELANCER = "Freelancer"


# ── Preferences ──────────────────────────────────────────────────────────

class CurrencyCode(str, enum.Enum):
    INR = "INR"
    USD = "USD"
    EUR = "EUR"


# ── Expenses ─────────────────────────────────────────────────────────────

class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"
    WALLET = "wallet"
    OTHER = "other"


class NotificationTiming(str, enum.Enum):
    MORNING = "Morning"
    EVENING = "Evening"
    CUSTOM = "Custom"


# ── Family ───────────────────────────────────────────────────────────────

class FamilyRole(str, enum.Enum):
    ADMIN = "Admin"
    MEMBER = "Member"
    CHILD = "Child"


class SettlementStatus(str, enum.Enum):
    PENDING = "pending"
    SETTLED = "settled"
    CANCELLED = "cancelled"


# ── Goals ────────────────────────────────────────────────────────────────

class SavingsGoalStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    PAUSED = "paused"


# ── Gamification ─────────────────────────────────────────────────────────

class BadgeCategory(str, enum.Enum):
    STREAKS = "streaks"
    SAVINGS = "savings"
    DISCIPLINE = "discipline"
    SOCIAL = "social"


class ChallengeType(str, enum.Enum):
    SPENDING_LIMIT = "spending_limit"
    NO_CATEGORY = "no_category"
    SAVE_AMOUNT = "save_amount"
    ZERO_SPEND = "zero_spend"


class ChallengeStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CLAIMED = "claimed"
    EXPIRED = "expired"
