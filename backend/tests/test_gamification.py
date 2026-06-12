"""Unit and integration tests for the Gamification system.

Tests XPEngine level math, StreakEngine progression logic,
BadgeEngine rule evaluation, ChallengeEngine lifecycle,
and GamificationService route handlers.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import (
    ChallengeStatus,
    ChallengeType,
    GamificationEventType,
    StreakType,
)
from app.models.user import User
from app.services.gamification import (
    BadgeEngine,
    ChallengeAlreadyJoinedError,
    ChallengeNotFoundError,
    CountRule,
    StreakEngine,
    StreakRule,
    XPEngine,
)


# ---------------------------------------------------------------------------
# XP Engine Tests
# ---------------------------------------------------------------------------

class TestXPEngine:
    """Verifies level calculation and XP reward lookups."""

    def test_level_1_at_zero_xp(self) -> None:
        assert XPEngine.calculate_level(0) == 1

    def test_level_2_at_100_xp(self) -> None:
        assert XPEngine.calculate_level(100) == 2

    def test_level_3_at_400_xp(self) -> None:
        assert XPEngine.calculate_level(400) == 3

    def test_level_4_at_900_xp(self) -> None:
        assert XPEngine.calculate_level(900) == 4

    def test_level_5_at_1600_xp(self) -> None:
        assert XPEngine.calculate_level(1600) == 5

    def test_negative_xp_returns_level_1(self) -> None:
        assert XPEngine.calculate_level(-500) == 1

    def test_xp_for_level_1_is_zero(self) -> None:
        assert XPEngine.xp_for_level(1) == 0

    def test_xp_for_level_2_is_100(self) -> None:
        assert XPEngine.xp_for_level(2) == 100

    def test_xp_for_level_3_is_400(self) -> None:
        assert XPEngine.xp_for_level(3) == 400

    def test_level_progress_pct_midway(self) -> None:
        # Level 2 requires 100–400 XP. At 250 XP → (150/300)*100 = 50.0%
        pct = XPEngine.level_progress_pct(250)
        assert pct == Decimal("50.0")

    def test_level_progress_pct_at_level_boundary(self) -> None:
        # Exactly at level 2 threshold (100 XP) → 0% through to level 3
        pct = XPEngine.level_progress_pct(100)
        assert pct == Decimal("0.0")

    def test_event_xp_expense_created(self) -> None:
        xp = XPEngine.get_event_xp(GamificationEventType.EXPENSE_CREATED.value)
        assert xp == 5

    def test_event_xp_budget_created(self) -> None:
        xp = XPEngine.get_event_xp(GamificationEventType.BUDGET_CREATED.value)
        assert xp == 20

    def test_event_xp_goal_completed(self) -> None:
        xp = XPEngine.get_event_xp(GamificationEventType.SAVINGS_GOAL_COMPLETED.value)
        assert xp == 100

    def test_event_xp_unknown_event_returns_zero(self) -> None:
        xp = XPEngine.get_event_xp("nonexistent_event_type")
        assert xp == 0


# ---------------------------------------------------------------------------
# Streak Engine Tests
# ---------------------------------------------------------------------------

class TestStreakEngine:
    """Verifies daily/weekly/monthly streak increment and reset logic."""

    def _mock_repo(self) -> MagicMock:
        return MagicMock()

    def test_daily_streak_first_expense_creates_streak_of_1(self) -> None:
        repo = self._mock_repo()
        repo.get_streak.return_value = None  # no existing streak
        mock_streak = MagicMock()
        mock_streak.current_count = 1
        repo.upsert_streak.return_value = mock_streak

        engine = StreakEngine(repo)
        result = engine.update_daily_streak(uuid.uuid4(), date.today())

        repo.upsert_streak.assert_called_once()
        call_kwargs = repo.upsert_streak.call_args[1]
        assert call_kwargs["current_count"] == 1
        assert call_kwargs["longest_count"] == 1

    def test_daily_streak_increments_on_consecutive_day(self) -> None:
        repo = self._mock_repo()
        today = date.today()
        yesterday = today - timedelta(days=1)

        existing = MagicMock()
        existing.last_active_date = yesterday
        existing.current_count = 5
        existing.longest_count = 10
        repo.get_streak.return_value = existing
        repo.upsert_streak.return_value = MagicMock()

        engine = StreakEngine(repo)
        engine.update_daily_streak(uuid.uuid4(), today)

        call_kwargs = repo.upsert_streak.call_args[1]
        assert call_kwargs["current_count"] == 6
        assert call_kwargs["longest_count"] == 10  # no new record

    def test_daily_streak_resets_on_gap(self) -> None:
        repo = self._mock_repo()
        today = date.today()
        two_days_ago = today - timedelta(days=2)

        existing = MagicMock()
        existing.last_active_date = two_days_ago
        existing.current_count = 15
        existing.longest_count = 20
        repo.get_streak.return_value = existing
        repo.upsert_streak.return_value = MagicMock()

        engine = StreakEngine(repo)
        engine.update_daily_streak(uuid.uuid4(), today)

        call_kwargs = repo.upsert_streak.call_args[1]
        assert call_kwargs["current_count"] == 1  # reset
        assert call_kwargs["longest_count"] == 20  # longest preserved

    def test_daily_streak_noop_on_same_day(self) -> None:
        repo = self._mock_repo()
        today = date.today()

        existing = MagicMock()
        existing.last_active_date = today
        existing.current_count = 3
        repo.get_streak.return_value = existing

        engine = StreakEngine(repo)
        result = engine.update_daily_streak(uuid.uuid4(), today)

        # Should return existing without calling upsert
        repo.upsert_streak.assert_not_called()
        assert result == existing

    def test_daily_streak_updates_longest_on_new_record(self) -> None:
        repo = self._mock_repo()
        today = date.today()
        yesterday = today - timedelta(days=1)

        existing = MagicMock()
        existing.last_active_date = yesterday
        existing.current_count = 10
        existing.longest_count = 10  # tied for longest
        repo.get_streak.return_value = existing
        repo.upsert_streak.return_value = MagicMock()

        engine = StreakEngine(repo)
        engine.update_daily_streak(uuid.uuid4(), today)

        call_kwargs = repo.upsert_streak.call_args[1]
        assert call_kwargs["current_count"] == 11
        assert call_kwargs["longest_count"] == 11  # new record!

    def test_monthly_streak_increments_on_consecutive_month(self) -> None:
        repo = self._mock_repo()

        # Active in May, now it's June
        last_may = date(2026, 5, 15)
        first_june = date(2026, 6, 1)

        existing = MagicMock()
        existing.last_active_date = last_may
        existing.current_count = 4
        existing.longest_count = 6
        repo.get_streak.return_value = existing
        repo.upsert_streak.return_value = MagicMock()

        engine = StreakEngine(repo)
        engine.update_monthly_streak(uuid.uuid4(), first_june)

        call_kwargs = repo.upsert_streak.call_args[1]
        assert call_kwargs["current_count"] == 5

    def test_monthly_streak_resets_on_skipped_month(self) -> None:
        repo = self._mock_repo()

        # Active in April, now it's June (skipped May)
        last_april = date(2026, 4, 30)
        first_june = date(2026, 6, 1)

        existing = MagicMock()
        existing.last_active_date = last_april
        existing.current_count = 12
        existing.longest_count = 12
        repo.get_streak.return_value = existing
        repo.upsert_streak.return_value = MagicMock()

        engine = StreakEngine(repo)
        engine.update_monthly_streak(uuid.uuid4(), first_june)

        call_kwargs = repo.upsert_streak.call_args[1]
        assert call_kwargs["current_count"] == 1  # reset


# ---------------------------------------------------------------------------
# Badge Engine Tests
# ---------------------------------------------------------------------------

class TestBadgeEngine:
    """Verifies badge rule evaluation and deduplication."""

    def test_count_rule_not_met(self) -> None:
        rule = CountRule(GamificationEventType.EXPENSE_CREATED.value, threshold=10)
        repo = MagicMock()
        repo.count_events.return_value = 5

        assert not rule.is_earned(repo, uuid.uuid4())

    def test_count_rule_met(self) -> None:
        rule = CountRule(GamificationEventType.EXPENSE_CREATED.value, threshold=10)
        repo = MagicMock()
        repo.count_events.return_value = 10

        assert rule.is_earned(repo, uuid.uuid4())

    def test_streak_rule_met_via_longest(self) -> None:
        rule = StreakRule(StreakType.DAILY_EXPENSE.value, threshold=7)
        repo = MagicMock()

        streak = MagicMock()
        streak.longest_count = 7  # achieved the 7-day streak historically
        streak.current_count = 2  # currently only 2
        repo.get_streak.return_value = streak

        assert rule.is_earned(repo, uuid.uuid4())

    def test_streak_rule_no_streak_returns_false(self) -> None:
        rule = StreakRule(StreakType.DAILY_EXPENSE.value, threshold=7)
        repo = MagicMock()
        repo.get_streak.return_value = None

        assert not rule.is_earned(repo, uuid.uuid4())

    def test_badge_engine_skips_already_earned_badges(self) -> None:
        repo = MagicMock()
        user_id = uuid.uuid4()

        # Simulate all candidate badges are already earned
        repo.get_user_badge_codes.return_value = {"first_expense", "expense_10", "expense_50", "expense_100", "streak_3_day", "streak_7_day", "streak_30_day", "streak_weekly_4"}

        engine = BadgeEngine(repo)
        newly_awarded = engine.evaluate_for_event(
            user_id, GamificationEventType.EXPENSE_CREATED.value
        )

        assert newly_awarded == []
        repo.award_badge.assert_not_called()

    def test_badge_engine_awards_first_expense_badge(self) -> None:
        repo = MagicMock()
        user_id = uuid.uuid4()

        # No badges yet, expense count = 1
        repo.get_user_badge_codes.return_value = set()
        repo.count_events.return_value = 1
        repo.get_streak.return_value = None
        repo.award_badge.return_value = MagicMock()

        engine = BadgeEngine(repo)
        newly_awarded = engine.evaluate_for_event(
            user_id, GamificationEventType.EXPENSE_CREATED.value
        )

        assert "first_expense" in newly_awarded

    def test_badge_engine_unknown_event_returns_empty(self) -> None:
        repo = MagicMock()
        engine = BadgeEngine(repo)

        result = engine.evaluate_for_event(uuid.uuid4(), "totally_unknown_event")
        assert result == []


# ---------------------------------------------------------------------------
# Gamification Route Handler Tests
# ---------------------------------------------------------------------------

class TestGamificationEndpoints:
    """Verifies HTTP responses for gamification route handlers."""

    @pytest.fixture(autouse=True)
    def setup_app_override(self, mock_user: User, mock_db: MagicMock) -> None:
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        yield
        app.dependency_overrides.clear()

    @patch("app.services.gamification.GamificationService.get_profile")
    def test_get_profile_endpoint(self, mock_get_profile: MagicMock) -> None:
        from app.schemas.gamification import GamificationProfileResponse
        from decimal import Decimal

        mock_get_profile.return_value = GamificationProfileResponse(
            xp=500,
            level=3,
            level_progress_pct=Decimal("25.00"),
            xp_current_level=400,
            xp_next_level=900,
            total_badges_earned=5,
            total_badges_available=20,
            total_challenges_completed=3,
            current_streaks=[],
            recent_badges=[],
        )
        client = TestClient(app)

        response = client.get("/api/v1/gamification/profile")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["xp"] == 500
        assert body["level"] == 3
        assert body["totalBadgesEarned"] == 5

    @patch("app.services.gamification.GamificationService.get_badges")
    def test_get_badges_endpoint(self, mock_get_badges: MagicMock) -> None:
        from app.schemas.gamification import BadgeListResponse
        mock_get_badges.return_value = BadgeListResponse(
            items=[], total_unlocked=0, total_available=20
        )
        client = TestClient(app)

        response = client.get("/api/v1/gamification/badges")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["totalAvailable"] == 20

    @patch("app.services.gamification.GamificationService.get_streaks")
    def test_get_streaks_endpoint(self, mock_get_streaks: MagicMock) -> None:
        from app.schemas.gamification import StreakListResponse
        mock_get_streaks.return_value = StreakListResponse(items=[])
        client = TestClient(app)

        response = client.get("/api/v1/gamification/streaks")
        assert response.status_code == status.HTTP_200_OK

    @patch("app.services.gamification.GamificationService.get_challenges")
    def test_get_challenges_endpoint_default_date(
        self, mock_get_challenges: MagicMock
    ) -> None:
        from app.schemas.gamification import ChallengeListResponse
        mock_get_challenges.return_value = ChallengeListResponse(items=[])
        client = TestClient(app)

        response = client.get("/api/v1/gamification/challenges")
        assert response.status_code == status.HTTP_200_OK
        mock_get_challenges.assert_called_once()

    def test_get_challenges_invalid_date_returns_422(self) -> None:
        client = TestClient(app)
        response = client.get("/api/v1/gamification/challenges?date=not-a-date")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("app.services.gamification.GamificationService.join_challenge")
    def test_join_challenge_success(
        self, mock_join: MagicMock
    ) -> None:
        from app.schemas.gamification import ChallengePublic
        from app.models.enums import ChallengeStatus, ChallengeType
        from decimal import Decimal
        import datetime

        challenge_id = uuid.uuid4()
        mock_join.return_value = ChallengePublic(
            id=challenge_id,
            title="Zero Spend Day",
            description="Keep wallet closed!",
            reward_xp=30,
            type=ChallengeType.ZERO_SPEND,
            challenge_date=date.today(),
            status=ChallengeStatus.ACTIVE,
            target_value=None,
            created_at=datetime.datetime(2026, 6, 12, 20, 0, 0),
            updated_at=datetime.datetime(2026, 6, 12, 20, 0, 0),
        )
        client = TestClient(app)

        response = client.post(f"/api/v1/gamification/challenges/{challenge_id}/join")
        assert response.status_code == status.HTTP_200_OK
        mock_join.assert_called_once()

    @patch("app.services.gamification.GamificationService.join_challenge")
    def test_join_challenge_not_found_returns_404(
        self, mock_join: MagicMock
    ) -> None:
        mock_join.side_effect = ChallengeNotFoundError("Challenge not found")
        client = TestClient(app)

        response = client.post(f"/api/v1/gamification/challenges/{uuid.uuid4()}/join")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.services.gamification.GamificationService.join_challenge")
    def test_join_challenge_already_joined_returns_409(
        self, mock_join: MagicMock
    ) -> None:
        mock_join.side_effect = ChallengeAlreadyJoinedError("Already joined")
        client = TestClient(app)

        response = client.post(f"/api/v1/gamification/challenges/{uuid.uuid4()}/join")
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_join_challenge_invalid_uuid_returns_422(self) -> None:
        client = TestClient(app)
        response = client.post("/api/v1/gamification/challenges/not-a-uuid/join")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
