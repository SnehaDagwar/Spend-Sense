"""Gamification routes.

All endpoints require a valid JWT access token (Bearer).

GET    /gamification/profile                — gamification profile with XP, level, badges, streaks
GET    /gamification/badges                 — full badge catalog with unlock state
GET    /gamification/streaks                — streak data for the user
GET    /gamification/challenges             — challenge list (with auto-generation)
POST   /gamification/challenges/{id}/join   — join an active challenge
"""

from typing import Annotated
import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.enums import ChallengeStatus
from app.schemas.gamification import (
    BadgeListResponse,
    ChallengeListResponse,
    ChallengePublic,
    GamificationProfileResponse,
    StreakListResponse,
)
from app.services.gamification import (
    ChallengeAlreadyJoinedError,
    ChallengeNotFoundError,
    GamificationService,
)

router = APIRouter(prefix="/gamification", tags=["gamification"])


# ---------------------------------------------------------------------------
# GET /gamification/profile
# ---------------------------------------------------------------------------

@router.get("/profile", response_model=GamificationProfileResponse)
def get_profile(
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> GamificationProfileResponse:
    """Return the gamification profile for the authenticated user.

    Includes XP, level, level progress, badge counts, current streaks,
    and recently earned badges.
    """
    service = GamificationService(db)
    profile = service.get_profile(user_id=user.id)
    db.commit()
    return profile


# ---------------------------------------------------------------------------
# GET /gamification/badges
# ---------------------------------------------------------------------------

@router.get("/badges", response_model=BadgeListResponse)
def get_badges(
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> BadgeListResponse:
    """Return the full badge catalog with unlock state for the authenticated user."""
    service = GamificationService(db)
    return service.get_badges(user_id=user.id)


# ---------------------------------------------------------------------------
# GET /gamification/streaks
# ---------------------------------------------------------------------------

@router.get("/streaks", response_model=StreakListResponse)
def get_streaks(
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> StreakListResponse:
    """Return all streak data for the authenticated user.

    Includes daily expense logging streak, weekly activity streak,
    and monthly budget discipline streak.
    """
    service = GamificationService(db)
    return service.get_streaks(user_id=user.id)


# ---------------------------------------------------------------------------
# GET /gamification/challenges
# ---------------------------------------------------------------------------

@router.get("/challenges", response_model=ChallengeListResponse)
def get_challenges(
    challenge_date: Annotated[
        str | None,
        Query(
            alias="date",
            description="Filter challenges by date (YYYY-MM-DD). "
            "Defaults to today and auto-generates if none exist.",
        ),
    ] = None,
    status_filter: Annotated[
        ChallengeStatus | None,
        Query(
            alias="status",
            description="Filter by challenge status.",
        ),
    ] = None,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> ChallengeListResponse:
    """List challenges for the authenticated user.

    If no challenges exist for the requested date, default daily
    challenges are generated automatically.
    """
    from datetime import date

    parsed_date = None
    if challenge_date is not None:
        try:
            parsed_date = date.fromisoformat(challenge_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="date must be a valid YYYY-MM-DD string.",
            )

    service = GamificationService(db)
    result = service.get_challenges(
        user_id=user.id,
        challenge_date=parsed_date,
        status=status_filter,
    )
    db.commit()
    return result


# ---------------------------------------------------------------------------
# POST /gamification/challenges/{challenge_id}/join
# ---------------------------------------------------------------------------

@router.post(
    "/challenges/{challenge_id}/join",
    response_model=ChallengePublic,
)
def join_challenge(
    challenge_id: str,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> ChallengePublic:
    """Join an active challenge.

    Records a gamification event and awards join XP.

    Returns **404** if the challenge does not exist or is not owned by the user.
    Returns **409** if the challenge is not in 'active' status.
    """
    try:
        cid = _uuid.UUID(challenge_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="challenge_id must be a valid UUID.",
        )

    service = GamificationService(db)
    try:
        return service.join_challenge(user_id=user.id, challenge_id=cid)
    except ChallengeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ChallengeAlreadyJoinedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
