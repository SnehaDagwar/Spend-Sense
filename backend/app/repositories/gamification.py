"""Repository for gamification tables.

Handles all direct database operations for gamification events, streaks,
badge awards, progress mutations, and challenge CRUD.  Follows the same
Session-based pattern as GoalRepository.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import Sequence

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models.badge import Badge, UserBadge
from app.models.challenge import Challenge
from app.models.gamification_event import GamificationEvent
from app.models.progress import UserProgress
from app.models.streak import UserStreak
from app.models.enums import ChallengeStatus


class GamificationRepository:
    """Manages all database interactions for the gamification subsystem."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # -----------------------------------------------------------------------
    # Events
    # -----------------------------------------------------------------------

    def record_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        event_key: str,
        event_date: date,
        metadata: dict | None = None,
    ) -> GamificationEvent | None:
        """Record a gamification event.  Returns None if already exists (idempotent)."""
        # Check for existing event (dedup)
        existing = self.db.scalar(
            select(GamificationEvent).where(
                GamificationEvent.user_id == user_id,
                GamificationEvent.event_type == event_type,
                GamificationEvent.event_key == event_key,
            )
        )
        if existing is not None:
            return None

        event = GamificationEvent(
            user_id=user_id,
            event_type=event_type,
            event_key=event_key,
            event_date=event_date,
            metadata_=metadata,
        )
        self.db.add(event)
        return event

    def count_events(
        self,
        user_id: uuid.UUID,
        event_type: str,
        since: date | None = None,
    ) -> int:
        """Count gamification events of a given type for a user."""
        stmt = select(func.count()).select_from(GamificationEvent).where(
            GamificationEvent.user_id == user_id,
            GamificationEvent.event_type == event_type,
        )
        if since is not None:
            stmt = stmt.where(GamificationEvent.event_date >= since)
        return self.db.scalar(stmt) or 0

    def has_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        event_key: str | None = None,
    ) -> bool:
        """Check if an event exists."""
        stmt = select(GamificationEvent).where(
            GamificationEvent.user_id == user_id,
            GamificationEvent.event_type == event_type,
        )
        if event_key is not None:
            stmt = stmt.where(GamificationEvent.event_key == event_key)
        return self.db.scalar(stmt.limit(1)) is not None

    def get_distinct_event_dates(
        self,
        user_id: uuid.UUID,
        event_type: str,
    ) -> list[date]:
        """Get distinct dates for events of a given type, ordered ascending."""
        stmt = (
            select(GamificationEvent.event_date)
            .where(
                GamificationEvent.user_id == user_id,
                GamificationEvent.event_type == event_type,
            )
            .distinct()
            .order_by(GamificationEvent.event_date.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_events_in_range(
        self,
        user_id: uuid.UUID,
        event_type: str,
        date_from: date,
        date_to: date,
    ) -> Sequence[GamificationEvent]:
        """Get events within a date range."""
        stmt = select(GamificationEvent).where(
            GamificationEvent.user_id == user_id,
            GamificationEvent.event_type == event_type,
            GamificationEvent.event_date >= date_from,
            GamificationEvent.event_date <= date_to,
        )
        return self.db.scalars(stmt).all()

    # -----------------------------------------------------------------------
    # Streaks
    # -----------------------------------------------------------------------

    def get_streaks(self, user_id: uuid.UUID) -> Sequence[UserStreak]:
        """Get all streak records for a user."""
        stmt = select(UserStreak).where(UserStreak.user_id == user_id)
        return self.db.scalars(stmt).all()

    def get_streak(
        self,
        user_id: uuid.UUID,
        streak_type: str,
    ) -> UserStreak | None:
        """Get a specific streak record."""
        stmt = select(UserStreak).where(
            UserStreak.user_id == user_id,
            UserStreak.streak_type == streak_type,
        )
        return self.db.scalar(stmt)

    def upsert_streak(
        self,
        user_id: uuid.UUID,
        streak_type: str,
        current_count: int,
        longest_count: int,
        last_active_date: date,
    ) -> UserStreak:
        """Create or update a streak record."""
        streak = self.get_streak(user_id, streak_type)
        if streak is None:
            streak = UserStreak(
                user_id=user_id,
                streak_type=streak_type,
                current_count=current_count,
                longest_count=longest_count,
                last_active_date=last_active_date,
            )
            self.db.add(streak)
        else:
            streak.current_count = current_count
            streak.longest_count = max(streak.longest_count, longest_count)
            streak.last_active_date = last_active_date
        return streak

    # -----------------------------------------------------------------------
    # Progress (XP / Level)
    # -----------------------------------------------------------------------

    def get_or_create_progress(self, user_id: uuid.UUID) -> UserProgress:
        """Get or create the user_progress row."""
        stmt = select(UserProgress).where(UserProgress.user_id == user_id)
        progress = self.db.scalar(stmt)
        if progress is None:
            progress = UserProgress(user_id=user_id, xp=0, level=1, savings_streak=0)
            self.db.add(progress)
            self.db.flush()
        return progress

    def add_xp(self, user_id: uuid.UUID, amount: int) -> UserProgress:
        """Add XP to user progress and return updated progress.

        Uses SELECT ... FOR UPDATE to prevent concurrent double-counting.
        """
        stmt = (
            select(UserProgress)
            .where(UserProgress.user_id == user_id)
            .with_for_update()
        )
        progress = self.db.scalar(stmt)
        if progress is None:
            progress = UserProgress(user_id=user_id, xp=amount, level=1, savings_streak=0)
            self.db.add(progress)
            self.db.flush()
        else:
            progress.xp += amount
        return progress

    # -----------------------------------------------------------------------
    # Badges
    # -----------------------------------------------------------------------

    def get_badge_catalog(self) -> Sequence[Badge]:
        """Get the full badge catalog, ordered by category then name."""
        stmt = select(Badge).order_by(Badge.category, Badge.name)
        return self.db.scalars(stmt).all()

    def get_user_badges(self, user_id: uuid.UUID) -> Sequence[UserBadge]:
        """Get all badges unlocked by a user."""
        stmt = (
            select(UserBadge)
            .where(UserBadge.user_id == user_id)
            .order_by(UserBadge.unlocked_at.desc())
        )
        return self.db.scalars(stmt).all()

    def get_user_badge_codes(self, user_id: uuid.UUID) -> set[str]:
        """Get the set of badge codes already earned by the user."""
        stmt = (
            select(Badge.code)
            .join(UserBadge, UserBadge.badge_id == Badge.id)
            .where(UserBadge.user_id == user_id)
        )
        return set(self.db.scalars(stmt).all())

    def get_unearned_badge_codes(self, user_id: uuid.UUID) -> set[str]:
        """Get badge codes the user has NOT yet earned."""
        all_codes = set(self.db.scalars(select(Badge.code)).all())
        earned_codes = self.get_user_badge_codes(user_id)
        return all_codes - earned_codes

    def award_badge(self, user_id: uuid.UUID, badge_code: str) -> UserBadge | None:
        """Award a badge by code.  Returns None if already awarded or badge not found."""
        badge = self.db.scalar(
            select(Badge).where(func.lower(Badge.code) == badge_code.lower())
        )
        if badge is None:
            return None

        # Check if already awarded
        existing = self.db.scalar(
            select(UserBadge).where(
                UserBadge.user_id == user_id,
                UserBadge.badge_id == badge.id,
            )
        )
        if existing is not None:
            return None

        user_badge = UserBadge(
            user_id=user_id,
            badge_id=badge.id,
            unlocked_at=datetime.now(timezone.utc),
        )
        self.db.add(user_badge)
        return user_badge

    def get_badge_by_code(self, code: str) -> Badge | None:
        """Lookup a badge by its code."""
        return self.db.scalar(
            select(Badge).where(func.lower(Badge.code) == code.lower())
        )

    # -----------------------------------------------------------------------
    # Challenges
    # -----------------------------------------------------------------------

    def list_challenges(
        self,
        user_id: uuid.UUID,
        challenge_date: date | None = None,
        status: ChallengeStatus | None = None,
    ) -> Sequence[Challenge]:
        """List challenges for a user with optional filters."""
        stmt = select(Challenge).where(Challenge.user_id == user_id)
        if challenge_date is not None:
            stmt = stmt.where(Challenge.challenge_date == challenge_date)
        if status is not None:
            stmt = stmt.where(Challenge.status == status)
        stmt = stmt.order_by(Challenge.challenge_date.desc(), Challenge.created_at.desc())
        return self.db.scalars(stmt).all()

    def get_challenge(
        self,
        challenge_id: uuid.UUID,
    ) -> Challenge | None:
        """Get a single challenge by ID."""
        return self.db.scalar(
            select(Challenge).where(Challenge.id == challenge_id)
        )

    def create_challenge(
        self,
        user_id: uuid.UUID,
        title: str,
        description: str,
        reward_xp: int,
        challenge_type: str,
        challenge_date: date,
        target_value: Decimal | None = None,
        category_id: uuid.UUID | None = None,
    ) -> Challenge:
        """Create a new challenge instance."""
        challenge = Challenge(
            user_id=user_id,
            title=title,
            description=description,
            reward_xp=reward_xp,
            type=challenge_type,
            challenge_date=challenge_date,
            target_value=target_value,
            category_id=category_id,
            status=ChallengeStatus.ACTIVE,
        )
        self.db.add(challenge)
        return challenge

    def update_challenge_status(
        self,
        challenge: Challenge,
        new_status: ChallengeStatus,
    ) -> Challenge:
        """Update the status of a challenge."""
        now = datetime.now(timezone.utc)
        challenge.status = new_status
        if new_status == ChallengeStatus.COMPLETED:
            challenge.completed_at = now
        elif new_status == ChallengeStatus.CLAIMED:
            challenge.claimed_at = now
            if challenge.completed_at is None:
                challenge.completed_at = now
        return challenge

    def count_completed_challenges(self, user_id: uuid.UUID) -> int:
        """Count challenges with status completed or claimed."""
        stmt = (
            select(func.count())
            .select_from(Challenge)
            .where(
                Challenge.user_id == user_id,
                Challenge.status.in_([
                    ChallengeStatus.COMPLETED,
                    ChallengeStatus.CLAIMED,
                ]),
            )
        )
        return self.db.scalar(stmt) or 0

    def challenge_exists_for_date(
        self,
        user_id: uuid.UUID,
        challenge_date: date,
        title: str,
    ) -> bool:
        """Check if a challenge with the same title already exists for a date."""
        stmt = select(Challenge).where(
            Challenge.user_id == user_id,
            Challenge.challenge_date == challenge_date,
            func.lower(Challenge.title) == title.lower(),
        )
        return self.db.scalar(stmt.limit(1)) is not None
