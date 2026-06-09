"""Gamification service — engines and public facade.

Contains:
- XPEngine: XP constants, level calculation
- StreakEngine: Incremental streak tracking
- BadgeEngine: Rule-based badge evaluation
- ChallengeEngine: Challenge lifecycle management
- EventDispatcher: Orchestration of event → badge/streak/XP
- GamificationService: Public facade for route handlers

All engines are plain classes composed inside GamificationService.
"""

from __future__ import annotations

import math
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Sequence

from sqlalchemy.orm import Session

from app.models.badge import Badge, UserBadge
from app.models.challenge import Challenge
from app.models.enums import (
    BadgeCategory,
    ChallengeStatus,
    ChallengeType,
    GamificationEventType,
    StreakType,
)
from app.models.progress import UserProgress
from app.models.streak import UserStreak
from app.repositories.gamification import GamificationRepository
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


# ═══════════════════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════════════════

class GamificationServiceError(Exception):
    """Base exception for GamificationService."""


class ChallengeNotFoundError(GamificationServiceError):
    """Raised when a challenge is not found or not owned by the user."""


class ChallengeAlreadyJoinedError(GamificationServiceError):
    """Raised when the user already has an active challenge for this date/type."""


class ChallengeNotCompletedError(GamificationServiceError):
    """Raised when attempting to claim XP on a non-completed challenge."""


# ═══════════════════════════════════════════════════════════════════════════
# XP Engine
# ═══════════════════════════════════════════════════════════════════════════

class XPEngine:
    """XP reward constants and level calculation."""

    # XP awarded per event type
    XP_REWARDS: dict[str, int] = {
        GamificationEventType.EXPENSE_CREATED.value: 5,
        GamificationEventType.BUDGET_CREATED.value: 20,
        GamificationEventType.SAVINGS_CONTRIBUTION.value: 15,
        GamificationEventType.SAVINGS_GOAL_CREATED.value: 10,
        GamificationEventType.SAVINGS_GOAL_COMPLETED.value: 100,
        GamificationEventType.CHALLENGE_COMPLETED.value: 0,  # uses challenge.reward_xp
        GamificationEventType.CHALLENGE_JOINED.value: 5,
        GamificationEventType.BUDGET_UNDER_LIMIT.value: 30,
    }

    # Bonus XP for badge unlocks and streak milestones
    XP_BADGE_EARNED = 25
    XP_STREAK_MILESTONE = 50

    @staticmethod
    def calculate_level(xp: int) -> int:
        """Level formula: level = floor(sqrt(xp / 100)) + 1.

        Level 1: 0 XP
        Level 2: 100 XP
        Level 3: 400 XP
        Level 4: 900 XP
        Level 5: 1600 XP
        """
        if xp < 0:
            return 1
        return int(math.sqrt(xp / 100)) + 1

    @staticmethod
    def xp_for_level(level: int) -> int:
        """XP required to reach a given level."""
        if level <= 1:
            return 0
        return (level - 1) ** 2 * 100

    @classmethod
    def level_progress_pct(cls, xp: int) -> Decimal:
        """Percentage progress toward the next level (0.00–100.00)."""
        current_level = cls.calculate_level(xp)
        current_level_xp = cls.xp_for_level(current_level)
        next_level_xp = cls.xp_for_level(current_level + 1)
        range_xp = next_level_xp - current_level_xp
        if range_xp <= 0:
            return Decimal("100.00")
        progress = ((xp - current_level_xp) / range_xp) * 100
        return Decimal(str(round(progress, 2)))

    @classmethod
    def get_event_xp(cls, event_type: str) -> int:
        """Get the XP reward for a given event type."""
        return cls.XP_REWARDS.get(event_type, 0)


# ═══════════════════════════════════════════════════════════════════════════
# Streak Engine
# ═══════════════════════════════════════════════════════════════════════════

class StreakEngine:
    """Incremental streak tracking with O(1) updates per event."""

    def __init__(self, repo: GamificationRepository) -> None:
        self.repo = repo

    def update_daily_streak(
        self,
        user_id: uuid.UUID,
        event_date: date,
    ) -> UserStreak:
        """Update the daily expense logging streak.

        - If last_active was yesterday → increment
        - If last_active was today → no-op (return current)
        - Otherwise → reset to 1
        """
        streak_type = StreakType.DAILY_EXPENSE.value
        streak = self.repo.get_streak(user_id, streak_type)

        if streak is None:
            return self.repo.upsert_streak(
                user_id=user_id,
                streak_type=streak_type,
                current_count=1,
                longest_count=1,
                last_active_date=event_date,
            )

        if streak.last_active_date == event_date:
            # Already recorded today — no-op
            return streak

        yesterday = event_date - timedelta(days=1)
        if streak.last_active_date == yesterday:
            new_count = streak.current_count + 1
        else:
            new_count = 1

        return self.repo.upsert_streak(
            user_id=user_id,
            streak_type=streak_type,
            current_count=new_count,
            longest_count=max(streak.longest_count, new_count),
            last_active_date=event_date,
        )

    def update_weekly_streak(
        self,
        user_id: uuid.UUID,
        event_date: date,
    ) -> UserStreak:
        """Update the weekly activity streak.

        A "week" is defined as ISO week number.  If the user was active
        in the previous ISO week, the streak continues.
        """
        streak_type = StreakType.WEEKLY_ACTIVITY.value
        streak = self.repo.get_streak(user_id, streak_type)

        current_week = event_date.isocalendar()[1]
        current_year = event_date.isocalendar()[0]

        if streak is None:
            return self.repo.upsert_streak(
                user_id=user_id,
                streak_type=streak_type,
                current_count=1,
                longest_count=1,
                last_active_date=event_date,
            )

        if streak.last_active_date is not None:
            last_week = streak.last_active_date.isocalendar()[1]
            last_year = streak.last_active_date.isocalendar()[0]

            if last_year == current_year and last_week == current_week:
                # Same week — no-op
                return streak

            # Check if previous week (handle year boundary)
            prev_week_date = event_date - timedelta(weeks=1)
            prev_week = prev_week_date.isocalendar()[1]
            prev_year = prev_week_date.isocalendar()[0]

            if last_year == prev_year and last_week == prev_week:
                new_count = streak.current_count + 1
            else:
                new_count = 1
        else:
            new_count = 1

        return self.repo.upsert_streak(
            user_id=user_id,
            streak_type=streak_type,
            current_count=new_count,
            longest_count=max(streak.longest_count, new_count),
            last_active_date=event_date,
        )

    def update_monthly_streak(
        self,
        user_id: uuid.UUID,
        event_date: date,
    ) -> UserStreak:
        """Update the monthly budget streak.

        Tracks consecutive months where the user stayed under budget.
        """
        streak_type = StreakType.MONTHLY_BUDGET.value
        streak = self.repo.get_streak(user_id, streak_type)

        if streak is None:
            return self.repo.upsert_streak(
                user_id=user_id,
                streak_type=streak_type,
                current_count=1,
                longest_count=1,
                last_active_date=event_date,
            )

        if streak.last_active_date is not None:
            last_month = streak.last_active_date.month
            last_year = streak.last_active_date.year

            current_month = event_date.month
            current_year = event_date.year

            # Same month — no-op
            if last_year == current_year and last_month == current_month:
                return streak

            # Check if previous month
            if current_month == 1:
                expected_month = 12
                expected_year = current_year - 1
            else:
                expected_month = current_month - 1
                expected_year = current_year

            if last_year == expected_year and last_month == expected_month:
                new_count = streak.current_count + 1
            else:
                new_count = 1
        else:
            new_count = 1

        return self.repo.upsert_streak(
            user_id=user_id,
            streak_type=streak_type,
            current_count=new_count,
            longest_count=max(streak.longest_count, new_count),
            last_active_date=event_date,
        )


# ═══════════════════════════════════════════════════════════════════════════
# Badge Engine
# ═══════════════════════════════════════════════════════════════════════════

class BadgeRule:
    """Base class for badge evaluation rules."""

    def is_earned(self, repo: GamificationRepository, user_id: uuid.UUID) -> bool:
        raise NotImplementedError


class CountRule(BadgeRule):
    """Badge awarded when event count >= threshold."""

    def __init__(self, event_type: str, threshold: int) -> None:
        self.event_type = event_type
        self.threshold = threshold

    def is_earned(self, repo: GamificationRepository, user_id: uuid.UUID) -> bool:
        count = repo.count_events(user_id, self.event_type)
        return count >= self.threshold


class StreakRule(BadgeRule):
    """Badge awarded when streak length >= threshold."""

    def __init__(self, streak_type: str, threshold: int) -> None:
        self.streak_type = streak_type
        self.threshold = threshold

    def is_earned(self, repo: GamificationRepository, user_id: uuid.UUID) -> bool:
        streak = repo.get_streak(user_id, self.streak_type)
        if streak is None:
            return False
        # Check both current and longest — once earned, stays earned
        return streak.longest_count >= self.threshold


class CompletionRule(BadgeRule):
    """Badge awarded on first occurrence of an event type."""

    def __init__(self, event_type: str) -> None:
        self.event_type = event_type

    def is_earned(self, repo: GamificationRepository, user_id: uuid.UUID) -> bool:
        return repo.has_event(user_id, self.event_type)


class ChallengeCountRule(BadgeRule):
    """Badge awarded when completed challenge count >= threshold."""

    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    def is_earned(self, repo: GamificationRepository, user_id: uuid.UUID) -> bool:
        count = repo.count_completed_challenges(user_id)
        return count >= self.threshold


class DistinctMonthBudgetRule(BadgeRule):
    """Badge awarded when budget_created events span N+ distinct months."""

    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    def is_earned(self, repo: GamificationRepository, user_id: uuid.UUID) -> bool:
        dates = repo.get_distinct_event_dates(
            user_id, GamificationEventType.BUDGET_CREATED.value,
        )
        months = {(d.year, d.month) for d in dates}
        return len(months) >= self.threshold


class ConsecutiveBudgetDisciplineRule(BadgeRule):
    """Badge for staying under budget N consecutive months."""

    def __init__(self, consecutive_months: int) -> None:
        self.consecutive_months = consecutive_months

    def is_earned(self, repo: GamificationRepository, user_id: uuid.UUID) -> bool:
        dates = repo.get_distinct_event_dates(
            user_id, GamificationEventType.BUDGET_UNDER_LIMIT.value,
        )
        if len(dates) < self.consecutive_months:
            return False

        # Extract (year, month) tuples sorted chronologically
        months = sorted({(d.year, d.month) for d in dates})
        if len(months) < self.consecutive_months:
            return False

        # Check for any run of consecutive months >= threshold
        run = 1
        for i in range(1, len(months)):
            prev_y, prev_m = months[i - 1]
            curr_y, curr_m = months[i]
            # Expected next month
            if prev_m == 12:
                exp_y, exp_m = prev_y + 1, 1
            else:
                exp_y, exp_m = prev_y, prev_m + 1

            if curr_y == exp_y and curr_m == exp_m:
                run += 1
            else:
                run = 1

            if run >= self.consecutive_months:
                return True

        return run >= self.consecutive_months


class MultiGoalRule(BadgeRule):
    """Badge for creating N+ savings goals."""

    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    def is_earned(self, repo: GamificationRepository, user_id: uuid.UUID) -> bool:
        count = repo.count_events(
            user_id, GamificationEventType.SAVINGS_GOAL_CREATED.value,
        )
        return count >= self.threshold


# ── Badge Rule Registry ──────────────────────────────────────────────────

# Maps badge_code → (rule, event_types_that_trigger_evaluation)
BADGE_RULES: dict[str, tuple[BadgeRule, list[str]]] = {
    # Expense tracking
    "first_expense": (
        CountRule(GamificationEventType.EXPENSE_CREATED.value, 1),
        [GamificationEventType.EXPENSE_CREATED.value],
    ),
    "expense_10": (
        CountRule(GamificationEventType.EXPENSE_CREATED.value, 10),
        [GamificationEventType.EXPENSE_CREATED.value],
    ),
    "expense_50": (
        CountRule(GamificationEventType.EXPENSE_CREATED.value, 50),
        [GamificationEventType.EXPENSE_CREATED.value],
    ),
    "expense_100": (
        CountRule(GamificationEventType.EXPENSE_CREATED.value, 100),
        [GamificationEventType.EXPENSE_CREATED.value],
    ),
    # Budget
    "budget_creator": (
        CountRule(GamificationEventType.BUDGET_CREATED.value, 1),
        [GamificationEventType.BUDGET_CREATED.value],
    ),
    "budget_3_months": (
        DistinctMonthBudgetRule(3),
        [GamificationEventType.BUDGET_CREATED.value],
    ),
    "budget_discipline": (
        ConsecutiveBudgetDisciplineRule(1),
        [GamificationEventType.BUDGET_UNDER_LIMIT.value],
    ),
    "budget_discipline_3": (
        ConsecutiveBudgetDisciplineRule(3),
        [GamificationEventType.BUDGET_UNDER_LIMIT.value],
    ),
    # Savings
    "savings_starter": (
        CompletionRule(GamificationEventType.SAVINGS_GOAL_CREATED.value),
        [GamificationEventType.SAVINGS_GOAL_CREATED.value],
    ),
    "savings_first_contrib": (
        CompletionRule(GamificationEventType.SAVINGS_CONTRIBUTION.value),
        [GamificationEventType.SAVINGS_CONTRIBUTION.value],
    ),
    "savings_master": (
        CompletionRule(GamificationEventType.SAVINGS_GOAL_COMPLETED.value),
        [GamificationEventType.SAVINGS_GOAL_COMPLETED.value],
    ),
    "savings_3_goals": (
        MultiGoalRule(3),
        [GamificationEventType.SAVINGS_GOAL_CREATED.value],
    ),
    # Streaks
    "streak_3_day": (
        StreakRule(StreakType.DAILY_EXPENSE.value, 3),
        [GamificationEventType.EXPENSE_CREATED.value],
    ),
    "streak_7_day": (
        StreakRule(StreakType.DAILY_EXPENSE.value, 7),
        [GamificationEventType.EXPENSE_CREATED.value],
    ),
    "streak_30_day": (
        StreakRule(StreakType.DAILY_EXPENSE.value, 30),
        [GamificationEventType.EXPENSE_CREATED.value],
    ),
    "streak_weekly_4": (
        StreakRule(StreakType.WEEKLY_ACTIVITY.value, 4),
        [GamificationEventType.EXPENSE_CREATED.value],
    ),
    "streak_monthly_3": (
        StreakRule(StreakType.MONTHLY_BUDGET.value, 3),
        [GamificationEventType.BUDGET_UNDER_LIMIT.value],
    ),
    # Challenges & discipline
    "no_spend_day": (
        ChallengeCountRule(1),  # At least 1 completed challenge (first no-spend)
        [GamificationEventType.CHALLENGE_COMPLETED.value],
    ),
    "challenge_5": (
        ChallengeCountRule(5),
        [GamificationEventType.CHALLENGE_COMPLETED.value],
    ),
    "challenge_10": (
        ChallengeCountRule(10),
        [GamificationEventType.CHALLENGE_COMPLETED.value],
    ),
}

# Pre-computed reverse index: event_type → badge_codes to evaluate
EVENT_TO_BADGES: dict[str, list[str]] = {}
for _code, (_rule, _event_types) in BADGE_RULES.items():
    for _et in _event_types:
        EVENT_TO_BADGES.setdefault(_et, []).append(_code)


class BadgeEngine:
    """Evaluates badge rules for a user after an event."""

    def __init__(self, repo: GamificationRepository) -> None:
        self.repo = repo

    def evaluate_for_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
    ) -> list[str]:
        """Check unearned badges triggered by this event type.

        Returns a list of newly awarded badge codes.
        """
        candidate_codes = EVENT_TO_BADGES.get(event_type, [])
        if not candidate_codes:
            return []

        earned_codes = self.repo.get_user_badge_codes(user_id)
        newly_awarded: list[str] = []

        for code in candidate_codes:
            if code in earned_codes:
                continue

            rule, _ = BADGE_RULES[code]
            if rule.is_earned(self.repo, user_id):
                result = self.repo.award_badge(user_id, code)
                if result is not None:
                    newly_awarded.append(code)

        return newly_awarded


# ═══════════════════════════════════════════════════════════════════════════
# Challenge Engine
# ═══════════════════════════════════════════════════════════════════════════

# Default challenge templates for daily generation
DAILY_CHALLENGE_TEMPLATES = [
    {
        "title": "Zero Spend Day",
        "description": "Don't log any expenses today. Keep your wallet closed!",
        "reward_xp": 30,
        "type": ChallengeType.ZERO_SPEND.value,
        "target_value": None,
    },
    {
        "title": "Budget Saver",
        "description": "Keep your daily spending under ₹500 today.",
        "reward_xp": 20,
        "type": ChallengeType.SPENDING_LIMIT.value,
        "target_value": Decimal("500.00"),
    },
    {
        "title": "Savings Boost",
        "description": "Make a contribution to any savings goal today.",
        "reward_xp": 25,
        "type": ChallengeType.SAVE_AMOUNT.value,
        "target_value": Decimal("100.00"),
    },
]


class ChallengeEngine:
    """Manages the challenge lifecycle."""

    def __init__(self, repo: GamificationRepository) -> None:
        self.repo = repo

    def get_or_generate_challenges(
        self,
        user_id: uuid.UUID,
        target_date: date,
    ) -> Sequence[Challenge]:
        """Idempotent daily challenge generation.

        Returns existing challenges for the date, or creates defaults if none exist.
        """
        existing = self.repo.list_challenges(user_id, challenge_date=target_date)
        if existing:
            return existing

        # Generate from templates
        created: list[Challenge] = []
        for template in DAILY_CHALLENGE_TEMPLATES:
            if not self.repo.challenge_exists_for_date(
                user_id, target_date, template["title"],
            ):
                challenge = self.repo.create_challenge(
                    user_id=user_id,
                    title=template["title"],
                    description=template["description"],
                    reward_xp=template["reward_xp"],
                    challenge_type=template["type"],
                    challenge_date=target_date,
                    target_value=template.get("target_value"),
                )
                created.append(challenge)

        return created or list(
            self.repo.list_challenges(user_id, challenge_date=target_date),
        )


# ═══════════════════════════════════════════════════════════════════════════
# Event Dispatcher
# ═══════════════════════════════════════════════════════════════════════════

class EventDispatcher:
    """Orchestrates the evaluation pipeline after recording an event."""

    def __init__(self, repo: GamificationRepository) -> None:
        self.repo = repo
        self.badge_engine = BadgeEngine(repo)
        self.streak_engine = StreakEngine(repo)

    def dispatch(
        self,
        user_id: uuid.UUID,
        event_type: str,
        event_key: str,
        event_date: date,
        metadata: dict | None = None,
    ) -> GamificationEventRecord:
        """Record event, evaluate badges, update streaks, award XP.

        Returns a summary of what happened.
        """
        # 1. Record the event (idempotent)
        event = self.repo.record_event(
            user_id=user_id,
            event_type=event_type,
            event_key=event_key,
            event_date=event_date,
            metadata=metadata,
        )
        if event is None:
            # Duplicate event — return no-op result
            return GamificationEventRecord(event_type=event_type)

        # 2. Award base XP for the event
        base_xp = XPEngine.get_event_xp(event_type)
        total_xp = base_xp

        # 3. Update streaks if applicable
        streak_updates: list[str] = []
        if event_type == GamificationEventType.EXPENSE_CREATED.value:
            self.streak_engine.update_daily_streak(user_id, event_date)
            self.streak_engine.update_weekly_streak(user_id, event_date)
            streak_updates.extend(["daily_expense", "weekly_activity"])
        elif event_type == GamificationEventType.BUDGET_UNDER_LIMIT.value:
            self.streak_engine.update_monthly_streak(user_id, event_date)
            streak_updates.append("monthly_budget")

        # 4. Evaluate badges
        new_badges = self.badge_engine.evaluate_for_event(user_id, event_type)
        total_xp += len(new_badges) * XPEngine.XP_BADGE_EARNED

        # 5. Grant XP and update level
        level_up = False
        new_level = None
        if total_xp > 0:
            progress = self.repo.add_xp(user_id, total_xp)
            computed_level = XPEngine.calculate_level(progress.xp)
            if computed_level > progress.level:
                level_up = True
                new_level = computed_level
                progress.level = computed_level

        return GamificationEventRecord(
            event_type=event_type,
            xp_earned=total_xp,
            new_badges=new_badges,
            streak_updates=streak_updates,
            level_up=level_up,
            new_level=new_level,
        )


# ═══════════════════════════════════════════════════════════════════════════
# Gamification Service (Public Facade)
# ═══════════════════════════════════════════════════════════════════════════

class GamificationService:
    """Public facade for all gamification operations.

    Route handlers should instantiate this with a DB session and delegate
    all logic here.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = GamificationRepository(db)
        self.dispatcher = EventDispatcher(self.repo)
        self.challenge_engine = ChallengeEngine(self.repo)

    # -------------------------------------------------------------------
    # Profile
    # -------------------------------------------------------------------

    def get_profile(self, user_id: uuid.UUID) -> GamificationProfileResponse:
        """Build the full gamification profile for a user."""
        progress = self.repo.get_or_create_progress(user_id)

        # Badge counts
        catalog = self.repo.get_badge_catalog()
        user_badges = self.repo.get_user_badges(user_id)
        earned_badge_ids = {ub.badge_id for ub in user_badges}

        # Recent badges (last 5)
        recent: list[RecentBadge] = []
        badge_map = {b.id: b for b in catalog}
        for ub in user_badges[:5]:
            badge = badge_map.get(ub.badge_id)
            if badge:
                recent.append(RecentBadge(
                    code=badge.code,
                    name=badge.name,
                    icon=badge.icon,
                    unlocked_at=ub.unlocked_at,
                ))

        # Streaks
        streaks = self.repo.get_streaks(user_id)
        streak_items = self._streaks_to_public(streaks)

        # Challenge stats
        completed_challenges = self.repo.count_completed_challenges(user_id)

        # Level calculations
        level = XPEngine.calculate_level(progress.xp)
        level_pct = XPEngine.level_progress_pct(progress.xp)
        xp_current = XPEngine.xp_for_level(level)
        xp_next = XPEngine.xp_for_level(level + 1)

        # Keep level in sync
        if progress.level != level:
            progress.level = level

        self.db.flush()

        return GamificationProfileResponse(
            xp=progress.xp,
            level=level,
            level_progress_pct=level_pct,
            xp_current_level=xp_current,
            xp_next_level=xp_next,
            total_badges_earned=len(earned_badge_ids),
            total_badges_available=len(catalog),
            total_challenges_completed=completed_challenges,
            current_streaks=streak_items,
            recent_badges=recent,
        )

    # -------------------------------------------------------------------
    # Badges
    # -------------------------------------------------------------------

    def get_badges(self, user_id: uuid.UUID) -> BadgeListResponse:
        """Get the full badge catalog with unlock state for the user."""
        catalog = self.repo.get_badge_catalog()
        user_badges = self.repo.get_user_badges(user_id)
        earned_map: dict[uuid.UUID, datetime] = {
            ub.badge_id: ub.unlocked_at for ub in user_badges
        }

        items: list[BadgePublic] = []
        for badge in catalog:
            unlocked_at = earned_map.get(badge.id)
            items.append(BadgePublic(
                id=badge.id,
                code=badge.code,
                name=badge.name,
                icon=badge.icon,
                description=badge.description,
                category=badge.category,
                is_unlocked=unlocked_at is not None,
                unlocked_at=unlocked_at,
            ))

        return BadgeListResponse(
            items=items,
            total_unlocked=len(earned_map),
            total_available=len(catalog),
        )

    # -------------------------------------------------------------------
    # Streaks
    # -------------------------------------------------------------------

    def get_streaks(self, user_id: uuid.UUID) -> StreakListResponse:
        """Get all streak data for a user."""
        streaks = self.repo.get_streaks(user_id)
        items = self._streaks_to_public(streaks)

        # Ensure all streak types are represented
        existing_types = {s.streak_type for s in items}
        for st in StreakType:
            if st.value not in existing_types:
                items.append(StreakPublic(
                    streak_type=st.value,
                    current_count=0,
                    longest_count=0,
                    last_active_date=None,
                    is_active=False,
                ))

        return StreakListResponse(items=items)

    def _streaks_to_public(self, streaks: Sequence[UserStreak]) -> list[StreakPublic]:
        """Convert streak models to public schemas."""
        today = date.today()
        items: list[StreakPublic] = []
        for s in streaks:
            is_active = False
            if s.last_active_date is not None:
                if s.streak_type == StreakType.DAILY_EXPENSE.value:
                    is_active = (today - s.last_active_date).days <= 1
                elif s.streak_type == StreakType.WEEKLY_ACTIVITY.value:
                    is_active = (today - s.last_active_date).days <= 7
                elif s.streak_type == StreakType.MONTHLY_BUDGET.value:
                    is_active = (today - s.last_active_date).days <= 31

            items.append(StreakPublic(
                streak_type=s.streak_type,
                current_count=s.current_count,
                longest_count=s.longest_count,
                last_active_date=s.last_active_date,
                is_active=is_active,
            ))
        return items

    # -------------------------------------------------------------------
    # Challenges
    # -------------------------------------------------------------------

    def get_challenges(
        self,
        user_id: uuid.UUID,
        challenge_date: date | None = None,
        status: ChallengeStatus | None = None,
    ) -> ChallengeListResponse:
        """List challenges, generating today's if needed."""
        target_date = challenge_date or date.today()

        # Ensure challenges exist for the target date
        self.challenge_engine.get_or_generate_challenges(user_id, target_date)
        self.db.flush()

        # Now list with filters
        challenges = self.repo.list_challenges(
            user_id,
            challenge_date=challenge_date,
            status=status,
        )

        items = [self._challenge_to_public(c) for c in challenges]
        return ChallengeListResponse(items=items)

    def join_challenge(
        self,
        user_id: uuid.UUID,
        challenge_id: uuid.UUID,
    ) -> ChallengePublic:
        """Join / acknowledge an existing challenge.

        The challenge must belong to the user and be in 'active' status.
        Records a challenge_joined event.
        """
        challenge = self.repo.get_challenge(challenge_id)
        if challenge is None or challenge.user_id != user_id:
            raise ChallengeNotFoundError(
                "Challenge not found or not owned by user.",
            )

        if challenge.status != ChallengeStatus.ACTIVE:
            raise ChallengeAlreadyJoinedError(
                f"Challenge is not active (current status: {challenge.status.value}).",
            )

        # Record the join event
        self.dispatcher.dispatch(
            user_id=user_id,
            event_type=GamificationEventType.CHALLENGE_JOINED.value,
            event_key=str(challenge_id),
            event_date=challenge.challenge_date,
            metadata={"challenge_id": str(challenge_id), "type": challenge.type.value},
        )

        self.db.commit()
        self.db.refresh(challenge)
        return self._challenge_to_public(challenge)

    def _challenge_to_public(self, c: Challenge) -> ChallengePublic:
        """Convert a Challenge model to a public schema."""
        # Compute progress percentage for display
        progress_pct = Decimal("0.00")
        if c.status in (ChallengeStatus.COMPLETED, ChallengeStatus.CLAIMED):
            progress_pct = Decimal("100.00")

        # Determine the correct challenge_date value
        challenge_date_val = c.challenge_date
        if isinstance(challenge_date_val, datetime):
            challenge_date_val = challenge_date_val.date()

        return ChallengePublic(
            id=c.id,
            title=c.title,
            description=c.description,
            reward_xp=c.reward_xp,
            type=c.type,
            target_value=c.target_value,
            category_id=c.category_id,
            challenge_date=challenge_date_val,
            status=c.status,
            progress_pct=progress_pct,
            completed_at=c.completed_at,
            claimed_at=c.claimed_at,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )

    # -------------------------------------------------------------------
    # Event Recording (called from other services)
    # -------------------------------------------------------------------

    def record_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        event_key: str,
        event_date: date | None = None,
        metadata: dict | None = None,
    ) -> GamificationEventRecord:
        """Record a gamification event and trigger all evaluations.

        This is the main entry point for other services to integrate
        with the gamification engine.
        """
        actual_date = event_date or date.today()
        return self.dispatcher.dispatch(
            user_id=user_id,
            event_type=event_type,
            event_key=event_key,
            event_date=actual_date,
            metadata=metadata,
        )
