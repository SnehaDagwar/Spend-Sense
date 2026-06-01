"""Savings goals routes.

All endpoints require a valid JWT access token (Bearer).

GET    /goals                         — list goals
POST   /goals                         — create a goal
GET    /goals/{goal_id}               — view details of a goal
PATCH  /goals/{goal_id}               — update a goal
DELETE /goals/{goal_id}               — delete a goal
POST   /goals/{goal_id}/contributions — record a contribution
GET    /goals/{goal_id}/contributions — list contribution history
"""

from typing import Annotated
import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.enums import SavingsGoalStatus
from app.schemas.goal import (
    GoalCreate,
    GoalListResponse,
    GoalPublic,
    GoalUpdate,
    GoalContributionCreate,
    GoalContributionPublic,
)
from app.services.goal import (
    GoalNotFoundError,
    GoalService,
    InvalidStatusTransitionError,
)

router = APIRouter(prefix="/goals", tags=["goals"])


# ---------------------------------------------------------------------------
# GET /goals
# ---------------------------------------------------------------------------

@router.get("", response_model=GoalListResponse)
def list_goals(
    status_filter: Annotated[
        SavingsGoalStatus | None,
        Query(alias="status", description="Filter goals by status."),
    ] = None,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> GoalListResponse:
    """Return all savings goals for the authenticated user, optionally filtered by status."""
    service = GoalService(db)
    goals = service.list_goals(user_id=user.id, status=status_filter)
    return GoalListResponse(items=goals)


# ---------------------------------------------------------------------------
# POST /goals
# ---------------------------------------------------------------------------

@router.post("", response_model=GoalPublic, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> GoalPublic:
    """Create a new savings goal for the authenticated user."""
    service = GoalService(db)
    return service.create_goal(user_id=user.id, payload=payload)


# ---------------------------------------------------------------------------
# GET /goals/{goal_id}
# ---------------------------------------------------------------------------

@router.get("/{goal_id}", response_model=GoalPublic)
def get_goal(
    goal_id: str,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> GoalPublic:
    """Retrieve details for a specific savings goal, including live progress metrics.

    Returns **404** if the goal does not exist or is not owned by the user.
    """
    try:
        goal_uuid = _uuid.UUID(goal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="goal_id must be a valid UUID.",
        )

    service = GoalService(db)
    try:
        return service.get_goal(user_id=user.id, goal_id=goal_uuid)
    except GoalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# PATCH /goals/{goal_id}
# ---------------------------------------------------------------------------

@router.patch("/{goal_id}", response_model=GoalPublic)
def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> GoalPublic:
    """Update properties of a savings goal.

    - Returns **404** if the goal does not exist or is not owned by the user.
    - Returns **400** if an invalid status transition is requested (e.g. active to paused on a reached goal).
    """
    try:
        goal_uuid = _uuid.UUID(goal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="goal_id must be a valid UUID.",
        )

    service = GoalService(db)
    try:
        return service.update_goal(user_id=user.id, goal_id=goal_uuid, payload=payload)
    except GoalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# DELETE /goals/{goal_id}
# ---------------------------------------------------------------------------

@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: str,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> None:
    """Delete a savings goal.

    Returns **404** if the goal does not exist or is not owned by the user.
    """
    try:
        goal_uuid = _uuid.UUID(goal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="goal_id must be a valid UUID.",
        )

    service = GoalService(db)
    try:
        service.delete_goal(user_id=user.id, goal_id=goal_uuid)
    except GoalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# POST /goals/{goal_id}/contributions
# ---------------------------------------------------------------------------

@router.post("/{goal_id}/contributions", response_model=GoalPublic)
def add_contribution(
    goal_id: str,
    payload: GoalContributionCreate,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> GoalPublic:
    """Atomically record a contribution to a savings goal, updating current amount and checking completed state.

    Returns **404** if the goal does not exist or is not owned by the user.
    """
    try:
        goal_uuid = _uuid.UUID(goal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="goal_id must be a valid UUID.",
        )

    service = GoalService(db)
    try:
        return service.add_contribution(
            user_id=user.id,
            goal_id=goal_uuid,
            amount=payload.amount,
            note=payload.note,
        )
    except GoalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# GET /goals/{goal_id}/contributions
# ---------------------------------------------------------------------------

@router.get("/{goal_id}/contributions", response_model=list[GoalContributionPublic])
def list_contributions(
    goal_id: str,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> list[GoalContributionPublic]:
    """Retrieve the contribution history for a savings goal.

    Returns **404** if the goal does not exist or is not owned by the user.
    """
    try:
        goal_uuid = _uuid.UUID(goal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="goal_id must be a valid UUID.",
        )

    service = GoalService(db)
    try:
        items = service.list_contributions(user_id=user.id, goal_id=goal_uuid)
        return [GoalContributionPublic.model_validate(item) for item in items]
    except GoalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
