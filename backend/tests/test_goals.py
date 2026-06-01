"""Automated unit and integration tests for Phase 5: Savings Goals System.

Tests all service operations, input validations, progress calculations,
contribution logging, ownership checks, and API endpoints.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.goal import GoalContribution, SavingsGoal
from app.models.user import User
from app.models.enums import SavingsGoalStatus
from app.schemas.goal import (
    GoalCreate,
    GoalUpdate,
    GoalContributionCreate,
    GoalPublic,
    GoalListResponse,
    Milestone,
    GoalContributionPublic,
)
from app.services.goal import GoalService, GoalNotFoundError, InvalidStatusTransitionError


# ---------------------------------------------------------------------------
# Test Fixtures & Mocks
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_user() -> User:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "finance.ninja@example.com"
    user.display_name = "Ninja User"
    return user


@pytest.fixture
def mock_other_user() -> User:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "other.ninja@example.com"
    user.display_name = "Other User"
    return user


@pytest.fixture
def mock_db() -> Session:
    return MagicMock(spec=Session)


@pytest.fixture
def mock_goal(mock_user: User) -> SavingsGoal:
    goal = SavingsGoal(
        user_id=mock_user.id,
        name="Tesla Model Y",
        icon="car",
        color="red",
        description="Save for our family electric SUV",
        priority="high",
        category="transport",
        target_amount=Decimal("50000.00"),
        current_amount=Decimal("10000.00"),
        monthly_contribution=Decimal("1000.00"),
        target_date=datetime.now() + timedelta(days=365),
        status=SavingsGoalStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    goal.id = uuid.uuid4()
    return goal


# ---------------------------------------------------------------------------
# Route Handler / Endpoint Integration Tests
# ---------------------------------------------------------------------------

class TestGoalEndpoints:
    """Verifies routes protection, input payload parsing, and standard HTTP error handling."""

    @pytest.fixture(autouse=True)
    def setup_app_override(self, mock_user: User, mock_db: Session) -> None:
        """Override dependencies for route testing."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        yield
        app.dependency_overrides.clear()

    def _mock_public_goal(self) -> GoalPublic:
        return GoalPublic(
            id=uuid.uuid4(),
            title="Hawaii Trip",
            description="Leisure trip",
            icon="beach",
            color="blue",
            target_amount=Decimal("5000.00"),
            current_amount=Decimal("1000.00"),
            monthly_contribution=Decimal("250.00"),
            target_date=date.today() + timedelta(days=30),
            priority="medium",
            category="leisure",
            status=SavingsGoalStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            percentage_completed=Decimal("20.00"),
            remaining_amount=Decimal("4000.00"),
            estimated_completion_date=date.today() + timedelta(days=30),
            milestone_tracking=[
                Milestone(label="Start", percentage=0, amount=Decimal("0.00"), is_reached=True),
            ]
        )

    @patch("app.services.goal.GoalService.list_goals")
    def test_list_goals_endpoint(self, mock_list_goals: MagicMock, mock_user: User) -> None:
        mock_list_goals.return_value = []
        client = TestClient(app)

        response = client.get("/api/v1/goals")
        assert response.status_code == 200
        mock_list_goals.assert_called_once_with(user_id=mock_user.id, status=None)

    @patch("app.services.goal.GoalService.list_goals")
    def test_list_goals_endpoint_with_filter(self, mock_list_goals: MagicMock, mock_user: User) -> None:
        mock_list_goals.return_value = []
        client = TestClient(app)

        response = client.get("/api/v1/goals?status=active")
        assert response.status_code == 200
        mock_list_goals.assert_called_once_with(user_id=mock_user.id, status=SavingsGoalStatus.ACTIVE)

    def test_create_goal_endpoint_invalid_data(self) -> None:
        client = TestClient(app)

        # Invalid target amount (must be positive)
        payload = {
            "title": "Vacation",
            "icon": "plane",
            "targetAmount": -500,
            "currentAmount": 0,
            "monthlyContribution": 100,
        }
        response = client.post("/api/v1/goals", json=payload)
        assert response.status_code == 422

        # Invalid target date (must be in future)
        past_date = (date.today() - timedelta(days=2)).isoformat()
        payload = {
            "title": "Vacation",
            "icon": "plane",
            "targetAmount": 1000,
            "currentAmount": 0,
            "monthlyContribution": 100,
            "targetDate": past_date,
        }
        response = client.post("/api/v1/goals", json=payload)
        assert response.status_code == 422

    @patch("app.services.goal.GoalService.create_goal")
    def test_create_goal_endpoint_success(self, mock_create_goal: MagicMock) -> None:
        mock_create_goal.return_value = self._mock_public_goal()
        client = TestClient(app)
        future_date = (date.today() + timedelta(days=30)).isoformat()
        
        # Valid payload
        payload = {
            "title": "Hawaii Trip",
            "icon": "beach",
            "targetAmount": 5000,
            "currentAmount": 1000,
            "monthlyContribution": 250,
            "targetDate": future_date,
            "priority": "medium",
            "category": "leisure",
        }
        response = client.post("/api/v1/goals", json=payload)
        assert response.status_code == 201
        mock_create_goal.assert_called_once()

    @patch("app.services.goal.GoalService.get_goal")
    def test_get_goal_endpoint_not_found(self, mock_get_goal: MagicMock) -> None:
        mock_get_goal.side_effect = GoalNotFoundError("Not found")
        client = TestClient(app)

        rand_uuid = str(uuid.uuid4())
        response = client.get(f"/api/v1/goals/{rand_uuid}")
        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Not found"

    def test_get_goal_endpoint_invalid_uuid(self) -> None:
        client = TestClient(app)
        response = client.get("/api/v1/goals/not-a-uuid")
        assert response.status_code == 422

    @patch("app.services.goal.GoalService.update_goal")
    def test_update_goal_endpoint_invalid_transition(self, mock_update_goal: MagicMock) -> None:
        mock_update_goal.side_effect = InvalidStatusTransitionError("Illegal transition")
        client = TestClient(app)

        rand_uuid = str(uuid.uuid4())
        payload = {"status": "paused"}
        response = client.patch(f"/api/v1/goals/{rand_uuid}", json=payload)
        assert response.status_code == 400
        assert response.json()["error"]["message"] == "Illegal transition"

    @patch("app.services.goal.GoalService.add_contribution")
    def test_add_contribution_endpoint(self, mock_add_contribution: MagicMock) -> None:
        mock_add_contribution.return_value = self._mock_public_goal()
        client = TestClient(app)

        rand_uuid = str(uuid.uuid4())
        payload = {"amount": 500.50, "note": "Weekly contribution"}
        response = client.post(f"/api/v1/goals/{rand_uuid}/contributions", json=payload)
        assert response.status_code == 200
        mock_add_contribution.assert_called_once()


# ---------------------------------------------------------------------------
# Business Service logic Tests
# ---------------------------------------------------------------------------

class TestGoalService:
    """Verifies calculations, status transitions, validation guards, and ownership checks."""

    def test_progress_calculation_math(self, mock_db: Session, mock_goal: SavingsGoal) -> None:
        service = GoalService(mock_db)

        # 10000 saved out of 50000 = 20.00%
        # remaining = 40000
        # monthly = 1000, so months remaining = 40
        metrics = service._calculate_progress(mock_goal)

        assert metrics["percentage_completed"] == Decimal("20.00")
        assert metrics["remaining_amount"] == Decimal("40000.00")
        
        # Est completion: 40 months from now (40 months ceil = 40)
        expected_date = service._add_months(date.today(), 40.0)
        assert metrics["estimated_completion_date"] == expected_date

        # Check milestones:
        # Start (0%): 0 reached
        # 25% (12500): not reached
        # 50% (25000): not reached
        # 75% (37500): not reached
        # 100% (50000): not reached
        milestones = metrics["milestone_tracking"]
        assert len(milestones) == 5
        assert milestones[0].is_reached is True  # 0%
        assert milestones[1].is_reached is False # 25%

    def test_progress_calculation_completed(self, mock_db: Session, mock_goal: SavingsGoal) -> None:
        service = GoalService(mock_db)
        mock_goal.current_amount = Decimal("55000.00") # Exceeds target

        metrics = service._calculate_progress(mock_goal)

        assert metrics["percentage_completed"] == Decimal("100.00")
        assert metrics["remaining_amount"] == Decimal("0.00")
        assert metrics["estimated_completion_date"] == date.today()

        # All milestones reached
        assert all(m.is_reached for m in metrics["milestone_tracking"])

    def test_progress_calculation_no_monthly_contribution(self, mock_db: Session, mock_goal: SavingsGoal) -> None:
        service = GoalService(mock_db)
        mock_goal.monthly_contribution = Decimal("0.00")
        
        future_date = date.today() + timedelta(days=90)
        mock_goal.target_date = datetime.combine(future_date, datetime.min.time())

        metrics = service._calculate_progress(mock_goal)
        assert metrics["estimated_completion_date"] == future_date

    def test_ownership_enforcement(self, mock_db: Session, mock_goal: SavingsGoal, mock_other_user: User) -> None:
        service = GoalService(mock_db)
        
        # Inject mock repo behavior
        service.repo.get_by_id = MagicMock(return_value=mock_goal)

        # Attempt to read, edit, delete, or contribute to another user's goal should raise GoalNotFoundError
        with pytest.raises(GoalNotFoundError):
            service.get_goal(user_id=mock_other_user.id, goal_id=mock_goal.id)

        with pytest.raises(GoalNotFoundError):
            service.update_goal(
                user_id=mock_other_user.id,
                goal_id=mock_goal.id,
                payload=GoalUpdate(title="Hacked"),
            )

        with pytest.raises(GoalNotFoundError):
            service.delete_goal(user_id=mock_other_user.id, goal_id=mock_goal.id)

        with pytest.raises(GoalNotFoundError):
            service.add_contribution(
                user_id=mock_other_user.id,
                goal_id=mock_goal.id,
                amount=Decimal("10.00"),
            )

    def test_invalid_status_transition_completed_to_paused(self, mock_db: Session, mock_goal: SavingsGoal, mock_user: User) -> None:
        service = GoalService(mock_db)
        
        # If goal is already completed (current >= target)
        mock_goal.current_amount = Decimal("50000.00")
        service.repo.get_by_id = MagicMock(return_value=mock_goal)

        # Transitioning back to paused/active on a fully funded goal should raise an error
        with pytest.raises(InvalidStatusTransitionError):
            service.update_goal(
                user_id=mock_user.id,
                goal_id=mock_goal.id,
                payload=GoalUpdate(status=SavingsGoalStatus.PAUSED),
            )

    def test_add_contribution_increments_and_completes(self, mock_db: Session, mock_goal: SavingsGoal, mock_user: User) -> None:
        service = GoalService(mock_db)
        service.repo.get_by_id = MagicMock(return_value=mock_goal)
        service.repo.create_contribution = MagicMock()

        # Goal target is 50000, current is 10000.
        # Add a contribution of 40000.
        # It should bring the current amount to 50000 and automatically flip status to completed.
        assert mock_goal.status == SavingsGoalStatus.ACTIVE
        
        res = service.add_contribution(
            user_id=mock_user.id,
            goal_id=mock_goal.id,
            amount=Decimal("40000.00"),
            note="Big milestone boost",
        )

        assert mock_goal.current_amount == Decimal("50000.00")
        assert mock_goal.status == SavingsGoalStatus.COMPLETED
        assert res.percentage_completed == Decimal("100.00")
        
        # Verify db persistence layer calls
        service.repo.create_contribution.assert_called_once_with(
            goal_id=mock_goal.id,
            amount=Decimal("40000.00"),
            note="Big milestone boost",
        )
