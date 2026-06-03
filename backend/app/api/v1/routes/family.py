"""Family & Shared Finance routes.

All endpoints require a valid JWT Bearer access token.

Family CRUD:
  POST    /family                              — create a new family group
  GET     /family                              — list families the caller belongs to
  GET     /family/{family_id}                  — get full family detail + members
  PATCH   /family/{family_id}                  — update name / currency  (Admin+)
  DELETE  /family/{family_id}                  — hard-delete family       (Owner only)

Membership:
  POST    /family/{family_id}/invite           — invite a member by email  (Admin+)
  POST    /family/accept-invite                — accept an invitation token
  DELETE  /family/{family_id}/member/{member_id} — remove a member         (Admin+)
  DELETE  /family/{family_id}/leave            — leave a family

Analytics:
  GET     /family/{family_id}/analytics        — shared expense/budget/goal summary
"""

from __future__ import annotations

import uuid as _uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.family import (
    AcceptInviteRequest,
    FamilyAnalytics,
    FamilyCreate,
    FamilyDetailPublic,
    FamilyListResponse,
    FamilyMemberPublic,
    FamilyUpdate,
    InviteMemberRequest,
    InviteResponse,
)
from app.services.family import (
    FamilyConflictError,
    FamilyMemberNotFoundError,
    FamilyNotFoundError,
    FamilyPermissionError,
    FamilyService,
    InvitationError,
)

router = APIRouter(prefix="/family", tags=["family"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_uuid(raw: str, field_name: str) -> _uuid.UUID:
    """Parse a UUID path parameter, raising 422 on invalid format."""
    try:
        return _uuid.UUID(raw)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} must be a valid UUID.",
        )


def _handle_service_errors(exc: Exception) -> HTTPException:
    """Map service-layer exceptions to appropriate HTTP responses."""
    if isinstance(exc, FamilyNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, FamilyPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, FamilyMemberNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, InvitationError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, FamilyConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    # Generic service error
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


# ---------------------------------------------------------------------------
# POST /family  — Create family
# ---------------------------------------------------------------------------

@router.post("", response_model=FamilyDetailPublic, status_code=status.HTTP_201_CREATED)
def create_family(
    payload: FamilyCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FamilyDetailPublic:
    """Create a new family group.

    The authenticated user becomes the Owner. Each user may own at most one family.
    Returns **409** if the user already owns a family.
    """
    service = FamilyService(db)
    try:
        return service.create_family(user=user, payload=payload)
    except Exception as exc:
        raise _handle_service_errors(exc) from exc


# ---------------------------------------------------------------------------
# GET /family  — List families
# ---------------------------------------------------------------------------

@router.get("", response_model=FamilyListResponse)
def list_families(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FamilyListResponse:
    """Return all family groups the authenticated user belongs to (as any role)."""
    service = FamilyService(db)
    return service.list_families(user_id=user.id)


# ---------------------------------------------------------------------------
# POST /family/accept-invite  — Accept invitation
# IMPORTANT: must be declared BEFORE /{family_id} to avoid routing ambiguity
# ---------------------------------------------------------------------------

@router.post(
    "/accept-invite",
    response_model=FamilyMemberPublic,
    status_code=status.HTTP_201_CREATED,
)
def accept_invite(
    payload: AcceptInviteRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FamilyMemberPublic:
    """Accept a family invitation using the raw token received from the inviter.

    - Returns **400** if the token is invalid, expired, already accepted, or revoked.
    - Returns **409** if the caller is already a member of the family.
    - The authenticated user's email must match the invited email address.
    """
    service = FamilyService(db)
    try:
        return service.accept_invite(user=user, payload=payload)
    except Exception as exc:
        raise _handle_service_errors(exc) from exc


# ---------------------------------------------------------------------------
# GET /family/{family_id}  — Get family detail
# ---------------------------------------------------------------------------

@router.get("/{family_id}", response_model=FamilyDetailPublic)
def get_family(
    family_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FamilyDetailPublic:
    """Return full family detail including the active member list.

    Returns **403** if the caller is not an active member of the family.
    Returns **404** if the family does not exist.
    """
    fid = _parse_uuid(family_id, "family_id")
    service = FamilyService(db)
    try:
        return service.get_family(user_id=user.id, family_id=fid)
    except Exception as exc:
        raise _handle_service_errors(exc) from exc


# ---------------------------------------------------------------------------
# PATCH /family/{family_id}  — Update family
# ---------------------------------------------------------------------------

@router.patch("/{family_id}", response_model=FamilyDetailPublic)
def update_family(
    family_id: str,
    payload: FamilyUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FamilyDetailPublic:
    """Update the family name and/or currency.

    Requires **Admin** or **Owner** role.
    Returns **403** if the caller is a plain Member.
    """
    fid = _parse_uuid(family_id, "family_id")
    service = FamilyService(db)
    try:
        return service.update_family(user_id=user.id, family_id=fid, payload=payload)
    except Exception as exc:
        raise _handle_service_errors(exc) from exc


# ---------------------------------------------------------------------------
# DELETE /family/{family_id}  — Delete family
# ---------------------------------------------------------------------------

@router.delete("/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_family(
    family_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Hard-delete a family and all associated members, expenses, and invitations.

    Requires **Owner** role. Returns **403** for Admin or Member callers.
    """
    fid = _parse_uuid(family_id, "family_id")
    service = FamilyService(db)
    try:
        service.delete_family(user_id=user.id, family_id=fid)
    except Exception as exc:
        raise _handle_service_errors(exc) from exc


# ---------------------------------------------------------------------------
# POST /family/{family_id}/invite  — Invite member
# ---------------------------------------------------------------------------

@router.post(
    "/{family_id}/invite",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
)
def invite_member(
    family_id: str,
    payload: InviteMemberRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InviteResponse:
    """Generate a single-use 72-hour invitation token for an email address.

    The **raw token** is returned in ``invitationToken`` — it is never stored
    on the server. Share it with the invitee via any messaging channel.

    Requires **Admin** or **Owner** role.
    Returns **409** if the email is already an active member or has a pending invitation.
    Returns **409** if the family has reached the maximum member limit (20).
    """
    fid = _parse_uuid(family_id, "family_id")
    service = FamilyService(db)
    try:
        return service.invite_member(user_id=user.id, family_id=fid, payload=payload)
    except Exception as exc:
        raise _handle_service_errors(exc) from exc


# ---------------------------------------------------------------------------
# DELETE /family/{family_id}/member/{member_id}  — Remove member
# ---------------------------------------------------------------------------

@router.delete(
    "/{family_id}/member/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_member(
    family_id: str,
    member_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Deactivate a family member.

    Requires **Admin** (can remove Members) or **Owner** (can remove Admins).
    - Returns **403** if the caller is a plain Member.
    - Returns **403** if an Admin tries to remove another Admin.
    - Returns **403** if the target is the Owner.
    - Returns **404** if the member is not found in this family.
    """
    fid = _parse_uuid(family_id, "family_id")
    mid = _parse_uuid(member_id, "member_id")
    service = FamilyService(db)
    try:
        service.remove_member(user_id=user.id, family_id=fid, member_id=mid)
    except Exception as exc:
        raise _handle_service_errors(exc) from exc


# ---------------------------------------------------------------------------
# DELETE /family/{family_id}/leave  — Leave family
# ---------------------------------------------------------------------------

@router.delete(
    "/{family_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
)
def leave_family(
    family_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Voluntarily leave a family group.

    - Returns **403** if the caller is the family Owner (delete the family instead).
    - Returns **403** if the caller is not a member of the family.
    """
    fid = _parse_uuid(family_id, "family_id")
    service = FamilyService(db)
    try:
        service.leave_family(user_id=user.id, family_id=fid)
    except Exception as exc:
        raise _handle_service_errors(exc) from exc


# ---------------------------------------------------------------------------
# GET /family/{family_id}/analytics  — Shared analytics
# ---------------------------------------------------------------------------

@router.get("/{family_id}/analytics", response_model=FamilyAnalytics)
def get_family_analytics(
    family_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FamilyAnalytics:
    """Return aggregated expense, budget, and savings goal data for the family.

    Requires active membership (any role).
    Returns **403** if the caller is not a member.
    """
    fid = _parse_uuid(family_id, "family_id")
    service = FamilyService(db)
    try:
        return service.get_shared_analytics(user_id=user.id, family_id=fid)
    except Exception as exc:
        raise _handle_service_errors(exc) from exc
