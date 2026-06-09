"""Pydantic schema exports."""

from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.budget import (
    AllocationAnalytics,
    AllocationPublic,
    AllocationUpsert,
    BudgetAnalytics,
    BudgetCreate,
    BudgetFilters,
    BudgetListItem,
    BudgetListResponse,
    BudgetPublic,
    BudgetUpdate,
)
from app.schemas.category import (
    CategoryCreate,
    CategoryListResponse,
    CategoryPublic,
    CategoryUpdate,
)
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseFilters,
    ExpenseListResponse,
    ExpensePublic,
    ExpenseUpdate,
)
from app.schemas.user import UserPublic
from app.schemas.goal import (
    GoalCreate,
    GoalUpdate,
    GoalPublic,
    GoalListResponse,
    GoalContributionCreate,
    GoalContributionPublic,
)
from app.schemas.report import (
    ReportFilters,
    MonthlyReportResponse,
    CategoryReportItem,
    CategoryReportResponse,
    GoalReportResponse,
)
from app.schemas.family import (
    AcceptInviteRequest,
    FamilyAnalytics,
    FamilyCreate,
    FamilyDetailPublic,
    FamilyListResponse,
    FamilyMemberPublic,
    FamilyPublic,
    FamilyUpdate,
    InviteMemberRequest,
    InviteResponse,
    SharedBudgetSummary,
    SharedExpenseSummary,
    SharedGoalSummary,
)
from app.schemas.insights import (
    SubscriptionDetection,
    FinancialSummaryInsight,
    SpendingPatternInsight,
    CategoryRecommendation,
    RecommendationsInsight,
    AnomalyItem,
    AnomaliesInsight,
    MonthlyReviewInsight,
)
from app.schemas.gamification import (
    BadgeListResponse,
    BadgePublic,
    ChallengeListResponse,
    ChallengePublic,
    GamificationEventRecord,
    GamificationProfileResponse,
    RecentBadge,
    StreakListResponse,
    StreakPublic,
)

__all__ = [
    # Auth
    "AuthResponse",
    "LoginRequest",
    "LogoutRequest",
    "RefreshTokenRequest",
    "RegisterRequest",
    "TokenResponse",
    # User
    "UserPublic",
    # Goals
    "GoalCreate",
    "GoalUpdate",
    "GoalPublic",
    "GoalListResponse",
    "GoalContributionCreate",
    "GoalContributionPublic",
    # Reports
    "ReportFilters",
    "MonthlyReportResponse",
    "CategoryReportItem",
    "CategoryReportResponse",
    "GoalReportResponse",
    # Categories

    "CategoryCreate",
    "CategoryListResponse",
    "CategoryPublic",
    "CategoryUpdate",
    # Expenses
    "ExpenseCreate",
    "ExpenseFilters",
    "ExpenseListResponse",
    "ExpensePublic",
    "ExpenseUpdate",
    # Budgets
    "AllocationAnalytics",
    "AllocationPublic",
    "AllocationUpsert",
    "BudgetAnalytics",
    "BudgetCreate",
    "BudgetFilters",
    "BudgetListItem",
    "BudgetListResponse",
    "BudgetPublic",
    "BudgetUpdate",
    # Family
    "AcceptInviteRequest",
    "FamilyAnalytics",
    "FamilyCreate",
    "FamilyDetailPublic",
    "FamilyListResponse",
    "FamilyMemberPublic",
    "FamilyPublic",
    "FamilyUpdate",
    "InviteMemberRequest",
    "InviteResponse",
    "SharedBudgetSummary",
    "SharedExpenseSummary",
    "SharedGoalSummary",
    # Insights
    "SubscriptionDetection",
    "FinancialSummaryInsight",
    "SpendingPatternInsight",
    "CategoryRecommendation",
    "RecommendationsInsight",
    "AnomalyItem",
    "AnomaliesInsight",
    "MonthlyReviewInsight",
    # Gamification
    "BadgeListResponse",
    "BadgePublic",
    "ChallengeListResponse",
    "ChallengePublic",
    "GamificationEventRecord",
    "GamificationProfileResponse",
    "RecentBadge",
    "StreakListResponse",
    "StreakPublic",
]
