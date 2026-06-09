"""Pydantic schemas for gamification endpoints.

Covers profile, badges, streaks, challenges, and event recording.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import uuid

from pydantic import Field

from app.schemas.base import APIModel
from app.models.enums import BadgeCategory, ChallengeStatus, ChallengeType


# ---------------------------------------------------------------------------
# Badge Schemas
# ---------------------------------------------------------------------------

class BadgePublic(APIModel):
    """Single badge with its unlock state for the authenticated user."""

    id: uuid.UUID
    code: str
    name: str
    icon: str
    description: str
    category: BadgeCategory
    is_unlocked: bool = False
    unlocked_at: datetime | None = None


class BadgeListResponse(APIModel):
    """Response for GET /gamification/badges."""

    items: list[BadgePublic]
    total_unlocked: int
    total_available: int


# ---------------------------------------------------------------------------
# Streak Schemas
# ---------------------------------------------------------------------------

class StreakPublic(APIModel):
    """Single streak counter for the authenticated user."""

    streak_type: str
    current_count: int
    longest_count: int
    last_active_date: date | None = None
    is_active: bool = False


class StreakListResponse(APIModel):
    """Response for GET /gamification/streaks."""

    items: list[StreakPublic]


# ---------------------------------------------------------------------------
# Challenge Schemas
# ---------------------------------------------------------------------------

class ChallengePublic(APIModel):
    """Single challenge instance."""

    id: uuid.UUID
    title: str
    description: str
    reward_xp: int
    type: ChallengeType
    target_value: Decimal | None = None
    category_id: uuid.UUID | None = None
    challenge_date: date
    status: ChallengeStatus
    progress_pct: Decimal = Decimal("0.00")
    completed_at: datetime | None = None
    claimed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ChallengeListResponse(APIModel):
    """Response for GET /gamification/challenges."""

    items: list[ChallengePublic]


# ---------------------------------------------------------------------------
# Profile / Progress Schemas
# ---------------------------------------------------------------------------

class RecentBadge(APIModel):
    """A recently earned badge shown on the profile."""

    code: str
    name: str
    icon: str
    unlocked_at: datetime


class GamificationProfileResponse(APIModel):
    """Response for GET /gamification/profile."""

    xp: int
    level: int
    level_progress_pct: Decimal
    xp_current_level: int
    xp_next_level: int
    total_badges_earned: int
    total_badges_available: int
    total_challenges_completed: int
    current_streaks: list[StreakPublic]
    recent_badges: list[RecentBadge]


# ---------------------------------------------------------------------------
# Event Recording (internal, not directly exposed via routes)
# ---------------------------------------------------------------------------

class GamificationEventRecord(APIModel):
    """Result of recording a gamification event."""

    event_type: str
    xp_earned: int = 0
    new_badges: list[str] = Field(default_factory=list)
    streak_updates: list[str] = Field(default_factory=list)
    level_up: bool = False
    new_level: int | None = None
