"""Repository for savings_goals and goal_contributions tables.

Handles all direct database query and persistency operations.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import GoalContribution, SavingsGoal
from app.models.enums import SavingsGoalStatus
from app.schemas.goal import GoalCreate


class GoalRepository:
    """Manages all database interactions for Savings Goals and Contributions."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # -----------------------------------------------------------------------
    # Savings Goal Reads & Writes
    # -----------------------------------------------------------------------

    def get_by_id(self, goal_id: uuid.UUID) -> SavingsGoal | None:
        """Retrieve a savings goal by its unique ID."""
        statement = select(SavingsGoal).where(SavingsGoal.id == goal_id)
        return self.db.scalar(statement)

    def list_by_user(
        self,
        user_id: uuid.UUID,
        status: SavingsGoalStatus | None = None,
    ) -> Sequence[SavingsGoal]:
        """List all savings goals for a specific user, with an optional status filter.

        Goals are sorted by created_at DESC (newest first).
        """
        statement = select(SavingsGoal).where(SavingsGoal.user_id == user_id)
        if status is not None:
            statement = statement.where(SavingsGoal.status == status)
        
        statement = statement.order_by(SavingsGoal.created_at.desc())
        return self.db.scalars(statement).all()

    def create(self, user_id: uuid.UUID, payload: GoalCreate) -> SavingsGoal:
        """Create a new savings goal record for the user."""
        goal = SavingsGoal(
            user_id=user_id,
            name=payload.title,  # maps Pydantic 'title' to DB column 'name'
            description=payload.description,
            icon=payload.icon,
            color=payload.color,
            target_amount=payload.target_amount,
            current_amount=payload.current_amount,
            monthly_contribution=payload.monthly_contribution,
            target_date=payload.target_date,
            status=payload.status,
            priority=payload.priority,
            category=payload.category,
        )
        self.db.add(goal)
        return goal

    def delete(self, goal: SavingsGoal) -> None:
        """Delete a savings goal from the database."""
        self.db.delete(goal)

    # -----------------------------------------------------------------------
    # Contribution Reads & Writes
    # -----------------------------------------------------------------------

    def create_contribution(
        self,
        goal_id: uuid.UUID,
        amount: Decimal,
        note: str | None = None,
    ) -> GoalContribution:
        """Record a new contribution to a goal."""
        contribution = GoalContribution(
            goal_id=goal_id,
            amount=amount,
            note=note,
        )
        self.db.add(contribution)
        return contribution

    def get_contributions_by_goal(self, goal_id: uuid.UUID) -> Sequence[GoalContribution]:
        """Retrieve the contribution history for a given goal ID, ordered by contributed_at DESC."""
        statement = select(GoalContribution).where(
            GoalContribution.goal_id == goal_id
        ).order_by(GoalContribution.contributed_at.desc())
        return self.db.scalars(statement).all()
