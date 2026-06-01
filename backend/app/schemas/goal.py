"""Pydantic schemas for savings goals and contributions."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import uuid
from typing import Annotated

from pydantic import Field, field_validator

from app.schemas.base import APIModel
from app.models.enums import SavingsGoalStatus


# ---------------------------------------------------------------------------
# Goal Contribution Schemas
# ---------------------------------------------------------------------------

class GoalContributionCreate(APIModel):
    """Payload to record a contribution."""

    amount: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    note: Annotated[str | None, Field(max_length=500)] = None

    @field_validator("note")
    @classmethod
    def validate_note(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class GoalContributionPublic(APIModel):
    """Goal contribution history item returned by API."""

    id: uuid.UUID
    goal_id: uuid.UUID
    amount: Decimal
    note: str | None
    contributed_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Milestone Schema
# ---------------------------------------------------------------------------

class Milestone(APIModel):
    """Dynamically evaluated progress milestone."""

    label: str
    percentage: int
    amount: Decimal
    is_reached: bool


# ---------------------------------------------------------------------------
# Savings Goal Request Schemas
# ---------------------------------------------------------------------------

class GoalCreate(APIModel):
    """Payload to create a new savings goal (POST /goals)."""

    title: Annotated[str, Field(min_length=1, max_length=100)]
    description: Annotated[str | None, Field(max_length=500)] = None
    icon: Annotated[str, Field(min_length=1, max_length=100)]
    color: Annotated[str | None, Field(max_length=100)] = None
    target_amount: Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]
    current_amount: Annotated[Decimal, Field(ge=Decimal("0.00"), decimal_places=2)] = Decimal("0.00")
    monthly_contribution: Annotated[Decimal, Field(ge=Decimal("0.00"), decimal_places=2)] = Decimal("0.00")
    target_date: date | None = None
    priority: str | None = None
    category: str | None = None
    status: SavingsGoalStatus = SavingsGoalStatus.ACTIVE

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty.")
        return v

    @field_validator("icon")
    @classmethod
    def validate_icon(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Icon cannot be empty.")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip().lower()
            if v not in ("low", "medium", "high"):
                raise ValueError("Priority must be one of 'low', 'medium', 'high'")
        return v

    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, v: date | None) -> date | None:
        if v is not None:
            if v < date.today():
                raise ValueError("Target date must be in the future.")
        return v


class GoalUpdate(APIModel):
    """Payload to update an existing savings goal (PATCH /goals/{id})."""

    title: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    description: Annotated[str | None, Field(max_length=500)] = None
    icon: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    color: Annotated[str | None, Field(max_length=100)] = None
    target_amount: Annotated[Decimal | None, Field(gt=Decimal("0.00"), decimal_places=2)] = None
    current_amount: Annotated[Decimal | None, Field(ge=Decimal("0.00"), decimal_places=2)] = None
    monthly_contribution: Annotated[Decimal | None, Field(ge=Decimal("0.00"), decimal_places=2)] = None
    target_date: date | None = None
    priority: str | None = None
    category: str | None = None
    status: SavingsGoalStatus | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Title cannot be empty.")
        return v

    @field_validator("icon")
    @classmethod
    def validate_icon(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Icon cannot be empty.")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip().lower()
            if v not in ("low", "medium", "high"):
                raise ValueError("Priority must be one of 'low', 'medium', 'high'")
        return v

    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, v: date | None) -> date | None:
        if v is not None:
            if v < date.today():
                raise ValueError("Target date must be in the future.")
        return v


# ---------------------------------------------------------------------------
# Savings Goal Response Schemas
# ---------------------------------------------------------------------------

class GoalPublic(APIModel):
    """Comprehensive savings goal representation returned by API."""

    id: uuid.UUID
    title: str = Field(validation_alias="name")
    description: str | None
    icon: str
    color: str | None
    target_amount: Decimal
    current_amount: Decimal
    monthly_contribution: Decimal
    target_date: date | None
    priority: str | None
    category: str | None
    status: SavingsGoalStatus
    created_at: datetime
    updated_at: datetime

    # Calculated metrics (progress tracking)
    percentage_completed: Decimal
    remaining_amount: Decimal
    estimated_completion_date: date | None
    milestone_tracking: list[Milestone]


class GoalListResponse(APIModel):
    """Response envelope for GET /goals."""

    items: list[GoalPublic]
