"""SQLAlchemy model exports.

Importing this package registers every model with ``Base.metadata`` so Alembic
auto-generation can detect all tables.
"""

# Enums (importable from app.models.enums or here)
from app.models.enums import (
    BadgeCategory,
    ChallengeStatus,
    ChallengeType,
    CurrencyCode,
    FamilyRole,
    GamificationEventType,
    NotificationTiming,
    PaymentMethod,
    SavingsGoalStatus,
    SettlementStatus,
    StreakType,
    UserType,
)

# Auth
from app.models.user import RefreshToken, User

# Profile extensions
from app.models.preferences import NotificationPreferences, UserPreferences
from app.models.progress import UserProgress

# Spending core
from app.models.category import SpendingCategory
from app.models.budget import BudgetCategoryAllocation, MonthlyBudget
from app.models.expense import Expense, ExpenseSplit
from app.models.upload import UploadedFile

# Family wallet
from app.models.family import Family, FamilyInvitation, FamilyMember, Settlement

# Goals
from app.models.goal import GoalContribution, SavingsGoal

# Gamification
from app.models.badge import Badge, UserBadge
from app.models.challenge import Challenge
from app.models.gamification_event import GamificationEvent
from app.models.streak import UserStreak

# Security & Audit
from app.models.audit_log import AuditLog

__all__ = [
    # Enums
    "BadgeCategory",
    "ChallengeStatus",
    "ChallengeType",
    "CurrencyCode",
    "FamilyRole",
    "GamificationEventType",
    "NotificationTiming",
    "PaymentMethod",
    "SavingsGoalStatus",
    "SettlementStatus",
    "StreakType",
    "UserType",
    # Auth
    "RefreshToken",
    "User",
    # Profile
    "NotificationPreferences",
    "UserPreferences",
    "UserProgress",
    # Spending
    "BudgetCategoryAllocation",
    "Expense",
    "ExpenseSplit",
    "MonthlyBudget",
    "SpendingCategory",
    "UploadedFile",
    # Family
    "Family",
    "FamilyInvitation",
    "FamilyMember",
    "Settlement",
    # Goals
    "GoalContribution",
    "SavingsGoal",
    # Gamification
    "Badge",
    "Challenge",
    "GamificationEvent",
    "UserBadge",
    "UserStreak",
    # Security & Audit
    "AuditLog",
]
