"""Business service for savings goals and contributions.

Handles ownership verification, progress calculations, milestone mapping,
contributions, and status transitions.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import math
import uuid
from typing import Sequence

from sqlalchemy.orm import Session

from app.models.goal import GoalContribution, SavingsGoal
from app.models.enums import SavingsGoalStatus
from app.repositories.goal import GoalRepository
from app.schemas.goal import (
    GoalCreate,
    GoalUpdate,
    GoalPublic,
    Milestone,
)


class GoalServiceError(Exception):
    """Base exception for GoalService errors."""
    pass


class GoalNotFoundError(GoalServiceError):
    """Raised when a goal is not found or not owned by the user."""
    pass


class InvalidStatusTransitionError(GoalServiceError):
    """Raised when an illegal status transition is requested."""
    pass


class GoalService:
    """Orchestrates all business operations for savings goals."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = GoalRepository(db)

    # -----------------------------------------------------------------------
    # Dynamic calculations
    # -----------------------------------------------------------------------

    def _calculate_progress(self, goal: SavingsGoal) -> dict:
        """Compute live progress metrics for a savings goal."""
        target = goal.target_amount
        current = goal.current_amount

        # 1. Percentage completed (capped at 100.00)
        if target > 0:
            percentage = min(Decimal("100.00"), (current / target) * 100)
        else:
            percentage = Decimal("0.00")
        
        # Round to two decimal places
        percentage = percentage.quantize(Decimal("0.01"))

        # 2. Remaining amount
        remaining = max(Decimal("0.00"), target - current)

        # 3. Estimated completion date
        est_date = None
        if current >= target:
            # Already completed
            est_date = date.today()
        elif goal.monthly_contribution > 0:
            months_remaining = float(remaining / goal.monthly_contribution)
            est_date = self._add_months(date.today(), months_remaining)
        else:
            # Fall back to target_date if defined
            if goal.target_date is not None:
                if isinstance(goal.target_date, datetime):
                    est_date = goal.target_date.date()
                else:
                    est_date = goal.target_date

        # 4. Milestone tracking
        milestones = []
        milestone_definitions = [
            ("Start", 0),
            ("25% Reached", 25),
            ("Halfway", 50),
            ("75% Reached", 75),
            ("Completed", 100),
        ]
        for label, pct in milestone_definitions:
            milestone_amount = (target * Decimal(pct) / 100).quantize(Decimal("0.01"))
            milestones.append(
                Milestone(
                    label=label,
                    percentage=pct,
                    amount=milestone_amount,
                    is_reached=current >= milestone_amount,
                )
            )

        return {
            "percentage_completed": percentage,
            "remaining_amount": remaining,
            "estimated_completion_date": est_date,
            "milestone_tracking": milestones,
        }

    @staticmethod
    def _add_months(start_date: date, months_to_add: float) -> date:
        """Safely add a fractional or whole number of months to a date, handles year wrap."""
        if months_to_add <= 0:
            return start_date
        
        total_months_ceil = math.ceil(months_to_add)
        year = start_date.year
        month = start_date.month + total_months_ceil
        
        year += (month - 1) // 12
        month = (month - 1) % 12 + 1
        
        # Adjust for calendar month bounds (e.g. Feb 30 -> Feb 28)
        is_leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        days_in_months = [
            31, 29 if is_leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
        ]
        day = min(start_date.day, days_in_months[month - 1])
        return date(year, month, day)

    def _to_public_schema(self, goal: SavingsGoal) -> GoalPublic:
        """Translate a SQLAlchemy model + live progress dict into a public Pydantic model."""
        metrics = self._calculate_progress(goal)
        
        # Extract date from datetime if necessary
        t_date = None
        if goal.target_date is not None:
            if isinstance(goal.target_date, datetime):
                t_date = goal.target_date.date()
            else:
                t_date = goal.target_date

        return GoalPublic(
            id=goal.id,
            title=goal.name,  # maps DB name to API title
            description=goal.description,
            icon=goal.icon,
            color=goal.color,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            monthly_contribution=goal.monthly_contribution,
            target_date=t_date,
            priority=goal.priority,
            category=goal.category,
            status=goal.status,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
            percentage_completed=metrics["percentage_completed"],
            remaining_amount=metrics["remaining_amount"],
            estimated_completion_date=metrics["estimated_completion_date"],
            milestone_tracking=metrics["milestone_tracking"],
        )

    # -----------------------------------------------------------------------
    # Goal Service Operations
    # -----------------------------------------------------------------------

    def get_goal(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> GoalPublic:
        """Retrieve a goal, verifying user ownership, and computing progress metrics."""
        goal = self.repo.get_by_id(goal_id)
        if goal is None or goal.user_id != user_id:
            raise GoalNotFoundError("Savings goal not found or not owned by user.")
        return self._to_public_schema(goal)

    def list_goals(
        self,
        user_id: uuid.UUID,
        status: SavingsGoalStatus | None = None,
    ) -> list[GoalPublic]:
        """List all goals for the user, calculating progress metrics for each."""
        goals = self.repo.list_by_user(user_id=user_id, status=status)
        return [self._to_public_schema(g) for g in goals]

    def create_goal(self, user_id: uuid.UUID, payload: GoalCreate) -> GoalPublic:
        """Create a new savings goal and evaluate its initial progress state."""
        # Auto-complete status check on initial value if current_amount >= target_amount
        if payload.current_amount >= payload.target_amount:
            payload.status = SavingsGoalStatus.COMPLETED

        goal = self.repo.create(user_id=user_id, payload=payload)
        self.db.commit()
        self.db.refresh(goal)
        return self._to_public_schema(goal)

    def update_goal(
        self,
        user_id: uuid.UUID,
        goal_id: uuid.UUID,
        payload: GoalUpdate,
    ) -> GoalPublic:
        """Update goal parameters and run transitions/validation rules."""
        goal = self.repo.get_by_id(goal_id)
        if goal is None or goal.user_id != user_id:
            raise GoalNotFoundError("Savings goal not found or not owned by user.")

        # Prepare future target and current values to validate status updates
        new_target = payload.target_amount if payload.target_amount is not None else goal.target_amount
        new_current = payload.current_amount if payload.current_amount is not None else goal.current_amount
        new_status = payload.status if payload.status is not None else goal.status

        # 1. Ownership & Status transition checks
        if payload.status is not None:
            # Target status pause/active for already reached amount
            if payload.status in (SavingsGoalStatus.PAUSED, SavingsGoalStatus.ACTIVE):
                if new_current >= new_target:
                    raise InvalidStatusTransitionError(
                        "Cannot set status to active or paused for a completed goal "
                        "unless target amount is greater than current amount."
                    )
            
            # Archive behavior
            if payload.status == SavingsGoalStatus.ARCHIVED:
                goal.archived_at = datetime.now()
            elif goal.status == SavingsGoalStatus.ARCHIVED and payload.status != SavingsGoalStatus.ARCHIVED:
                goal.archived_at = None

        # 2. Auto-complete check: if updated amounts lead to current >= target, force complete status
        if new_current >= new_target and new_status != SavingsGoalStatus.ARCHIVED:
            goal.status = SavingsGoalStatus.COMPLETED
        elif payload.status is not None:
            goal.status = payload.status

        # 3. Apply standard field modifications
        if payload.title is not None:
            goal.name = payload.title
        if payload.description is not None:
            goal.description = payload.description
        if payload.icon is not None:
            goal.icon = payload.icon
        if payload.color is not None:
            goal.color = payload.color
        if payload.target_amount is not None:
            goal.target_amount = payload.target_amount
        if payload.current_amount is not None:
            goal.current_amount = payload.current_amount
        if payload.monthly_contribution is not None:
            goal.monthly_contribution = payload.monthly_contribution
        if payload.target_date is not None:
            # Map target_date date object to datetime
            goal.target_date = datetime.combine(payload.target_date, datetime.min.time())
        elif "target_date" in payload.model_fields_set and payload.target_date is None:
            goal.target_date = None
        if payload.priority is not None:
            goal.priority = payload.priority
        if payload.category is not None:
            goal.category = payload.category

        self.db.commit()
        self.db.refresh(goal)
        return self._to_public_schema(goal)

    def delete_goal(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
        """Delete a savings goal."""
        goal = self.repo.get_by_id(goal_id)
        if goal is None or goal.user_id != user_id:
            raise GoalNotFoundError("Savings goal not found or not owned by user.")
        self.repo.delete(goal)
        self.db.commit()

    # -----------------------------------------------------------------------
    # Contribution Services
    # -----------------------------------------------------------------------

    def add_contribution(
        self,
        user_id: uuid.UUID,
        goal_id: uuid.UUID,
        amount: Decimal,
        note: str | None = None,
    ) -> GoalPublic:
        """Atomically record a contribution, increment current_amount, and check completed state."""
        goal = self.repo.get_by_id(goal_id)
        if goal is None or goal.user_id != user_id:
            raise GoalNotFoundError("Savings goal not found or not owned by user.")

        # Increment current_amount
        goal.current_amount += amount

        # Auto-complete state update
        if goal.current_amount >= goal.target_amount and goal.status != SavingsGoalStatus.ARCHIVED:
            goal.status = SavingsGoalStatus.COMPLETED

        # Create log record
        self.repo.create_contribution(goal_id=goal_id, amount=amount, note=note)

        self.db.commit()
        self.db.refresh(goal)
        return self._to_public_schema(goal)

    def list_contributions(
        self,
        user_id: uuid.UUID,
        goal_id: uuid.UUID,
    ) -> list[GoalContribution]:
        """List all contributions made to a savings goal, verifying ownership."""
        goal = self.repo.get_by_id(goal_id)
        if goal is None or goal.user_id != user_id:
            raise GoalNotFoundError("Savings goal not found or not owned by user.")
        return list(self.repo.get_contributions_by_goal(goal_id))
