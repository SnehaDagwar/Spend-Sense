"""Pydantic schemas for the Family & Shared Finance system.

Covers:
- Family CRUD (create, update, public response)
- Member representation
- Invitation lifecycle (invite request, response, accept request)
- Shared analytics (expenses, budgets, goals)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator

from app.schemas.base import APIModel
from app.models.enums import CurrencyCode, FamilyRole


# ---------------------------------------------------------------------------
# Member Schemas
# ---------------------------------------------------------------------------

class FamilyMemberPublic(APIModel):
    """Public representation of a single family member."""

    id: uuid.UUID
    family_id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    role: FamilyRole
    email: str | None
    avatar_url: str | None
    spending_limit: Decimal | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Family Create / Update Schemas
# ---------------------------------------------------------------------------

class FamilyCreate(APIModel):
    """Payload for POST /family — creates a new family group."""

    name: Annotated[str, Field(min_length=1, max_length=100)] = "Family Wallet"
    currency: CurrencyCode = CurrencyCode.INR

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Family name cannot be blank.")
        return v


class FamilyUpdate(APIModel):
    """Payload for PATCH /family/{family_id} — updates name and/or currency."""

    name: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    currency: CurrencyCode | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Family name cannot be blank.")
        return v


# ---------------------------------------------------------------------------
# Family Response Schemas
# ---------------------------------------------------------------------------

class FamilyPublic(APIModel):
    """Lightweight family summary returned in list responses."""

    id: uuid.UUID
    owner_user_id: uuid.UUID
    name: str
    currency: CurrencyCode
    member_count: int
    created_at: datetime
    updated_at: datetime


class FamilyDetailPublic(APIModel):
    """Full family detail with embedded member list."""

    id: uuid.UUID
    owner_user_id: uuid.UUID
    name: str
    currency: CurrencyCode
    members: list[FamilyMemberPublic]
    created_at: datetime
    updated_at: datetime


class FamilyListResponse(APIModel):
    """Response envelope for GET /family."""

    items: list[FamilyPublic]
    total: int


# ---------------------------------------------------------------------------
# Invitation Schemas
# ---------------------------------------------------------------------------

class InviteMemberRequest(APIModel):
    """Payload for POST /family/{family_id}/invite."""

    email: Annotated[str, Field(min_length=3, max_length=320)]
    role: FamilyRole = FamilyRole.MEMBER

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or v.index("@") < 1:
            raise ValueError("A valid email address is required.")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: FamilyRole) -> FamilyRole:
        # Only Admin and Member can be invited — Owner is auto-assigned at creation.
        if v == FamilyRole.OWNER:
            raise ValueError("Cannot invite a member with the Owner role.")
        if v == FamilyRole.CHILD:
            raise ValueError(
                "The Child role is deprecated. Use Member instead."
            )
        return v


class InviteResponse(APIModel):
    """Returned after a successful invite creation.

    The ``invitation_token`` is the raw token the inviter must share with
    the recipient out-of-band. It is returned exactly once and never stored.
    """

    invitation_id: uuid.UUID
    family_id: uuid.UUID
    email: str
    role: FamilyRole
    invitation_token: str
    expires_at: datetime
    created_at: datetime


class AcceptInviteRequest(APIModel):
    """Payload for POST /family/accept-invite."""

    token: Annotated[str, Field(min_length=10, description="Raw invitation token received from the inviter.")]


# ---------------------------------------------------------------------------
# Shared Analytics Schemas
# ---------------------------------------------------------------------------

class SharedExpenseSummary(APIModel):
    """Aggregated shared expense data for a family."""

    total_amount: Decimal
    expense_count: int
    top_category: str | None
    current_month_total: Decimal


class SharedBudgetSummary(APIModel):
    """Family budget overview — aggregated across all members."""

    total_planned: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    member_count: int


class SharedGoalSummary(APIModel):
    """Summary of savings goals owned by family members."""

    total_goals: int
    active_goals: int
    completed_goals: int
    total_saved: Decimal
    total_target: Decimal


class FamilyAnalytics(APIModel):
    """Aggregated analytics for a family group."""

    family_id: uuid.UUID
    family_name: str
    expenses: SharedExpenseSummary
    budget: SharedBudgetSummary
    goals: SharedGoalSummary
    generated_at: datetime
