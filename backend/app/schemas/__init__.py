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
]
