"""Business service for the Family & Shared Finance system.

Handles:
- Family lifecycle (create, list, get, update, delete)
- Membership management (invite, accept, remove, leave)
- Role-based permission checks via FamilyPermissionGuard
- Invitation token generation and validation
- Shared analytics aggregation
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Sequence

import uuid

from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.models.enums import FamilyRole
from app.models.family import Family, FamilyMember
from app.models.user import User
from app.repositories.family import FamilyRepository
from app.repositories.user import UserRepository
from app.schemas.family import (
    AcceptInviteRequest,
    FamilyAnalytics,
    FamilyCreate,
    FamilyDetailPublic,
    FamilyListResponse,
    FamilyMemberPublic,
    FamilyPublic,
    FamilyUpdate,
    InviteMemberRequest,
    InviteResponse,
    SharedBudgetSummary,
    SharedExpenseSummary,
    SharedGoalSummary,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INVITATION_TOKEN_BYTES = 64          # 512-bit entropy — brute-force proof
INVITATION_TTL_HOURS = 72            # 3-day window for acceptance
MAX_FAMILY_MEMBERS = 20              # soft ceiling enforced at service layer


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class FamilyServiceError(Exception):
    """Base exception for FamilyService errors."""


class FamilyNotFoundError(FamilyServiceError):
    """Raised when a family does not exist or the caller has no access."""


class FamilyPermissionError(FamilyServiceError):
    """Raised when the caller lacks the required role for an action."""


class FamilyMemberNotFoundError(FamilyServiceError):
    """Raised when a specific member record cannot be located."""


class InvitationError(FamilyServiceError):
    """Raised for invitation validation failures (expired, used, not found)."""


class FamilyConflictError(FamilyServiceError):
    """Raised on duplicate member, already-owner, or member-cap violations."""


# ---------------------------------------------------------------------------
# Permission Guard
# ---------------------------------------------------------------------------

class FamilyPermissionGuard:
    """Centralised RBAC gate for family operations.

    Call ``require(member, action)`` before any mutating operation. The guard
    raises ``FamilyPermissionError`` with a human-readable reason when the
    caller's role is insufficient.
    """

    # Actions that only the family owner may perform.
    _OWNER_ONLY = frozenset({
        "delete_family",
        "promote_to_admin",
        "demote_admin",
        "transfer_ownership",
    })

    # Actions that owner OR admin may perform.
    _ADMIN_OR_ABOVE = frozenset({
        "invite_member",
        "remove_member",
        "update_family",
    })

    def require(self, member: FamilyMember | None, action: str) -> None:
        """Assert that ``member`` may perform ``action``.

        Raises ``FamilyPermissionError`` if the member is None (not a member
        of the family) or has insufficient role for the requested action.
        """
        if member is None:
            raise FamilyPermissionError("You are not a member of this family.")

        role = member.role

        if action in self._OWNER_ONLY:
            if role != FamilyRole.OWNER:
                raise FamilyPermissionError(
                    f"Only the family Owner can perform '{action}'."
                )

        elif action in self._ADMIN_OR_ABOVE:
            if role not in (FamilyRole.OWNER, FamilyRole.ADMIN):
                raise FamilyPermissionError(
                    f"Owner or Admin role is required to perform '{action}'."
                )

        # MEMBER-level actions (view_family, leave_family, etc.) are implicitly
        # allowed for any non-None member — no further check needed.


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def _member_to_public(member: FamilyMember) -> FamilyMemberPublic:
    return FamilyMemberPublic(
        id=member.id,
        family_id=member.family_id,
        user_id=member.user_id,
        name=member.name,
        role=member.role,
        email=member.email,
        avatar_url=member.avatar_url,
        spending_limit=member.spending_limit,
        is_active=member.is_active,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


def _family_to_detail(
    family: Family, members: Sequence[FamilyMember]
) -> FamilyDetailPublic:
    return FamilyDetailPublic(
        id=family.id,
        owner_user_id=family.owner_user_id,
        name=family.name,
        currency=family.currency,
        members=[_member_to_public(m) for m in members],
        created_at=family.created_at,
        updated_at=family.updated_at,
    )


def _family_to_public(family: Family, member_count: int) -> FamilyPublic:
    return FamilyPublic(
        id=family.id,
        owner_user_id=family.owner_user_id,
        name=family.name,
        currency=family.currency,
        member_count=member_count,
        created_at=family.created_at,
        updated_at=family.updated_at,
    )


# ---------------------------------------------------------------------------
# FamilyService
# ---------------------------------------------------------------------------

class FamilyService:
    """Orchestrates all business operations for the Family system."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = FamilyRepository(db)
        self.guard = FamilyPermissionGuard()

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _resolve_caller(
        self, user_id: uuid.UUID, family_id: uuid.UUID
    ) -> FamilyMember | None:
        """Return the active FamilyMember record for user within family, or None."""
        return self.repo.get_member_by_user(family_id=family_id, user_id=user_id)

    def _require_family(self, family_id: uuid.UUID) -> Family:
        """Return family or raise FamilyNotFoundError."""
        family = self.repo.get_by_id(family_id)
        if family is None:
            raise FamilyNotFoundError("Family not found.")
        return family

    # -----------------------------------------------------------------------
    # Family Lifecycle
    # -----------------------------------------------------------------------

    def create_family(
        self, user: User, payload: FamilyCreate
    ) -> FamilyDetailPublic:
        """Create a new family group. Each user may own at most one family."""
        existing = self.repo.get_by_owner(user.id)
        if existing is not None:
            raise FamilyConflictError(
                "You already own a family group. "
                "Delete it or transfer ownership before creating a new one."
            )

        family = self.repo.create(
            owner_user_id=user.id,
            owner_name=user.display_name,
            owner_email=user.email,
            payload=payload,
        )
        self.db.commit()
        self.db.refresh(family)

        members = list(self.repo.list_active_members(family.id))
        return _family_to_detail(family, members)

    def list_families(self, user_id: uuid.UUID) -> FamilyListResponse:
        """List all families where the caller is an active member."""
        families = self.repo.list_for_user(user_id=user_id)
        items = []
        for f in families:
            count = self.repo.count_active_members(f.id)
            items.append(_family_to_public(f, count))
        return FamilyListResponse(items=items, total=len(items))

    def get_family(
        self, user_id: uuid.UUID, family_id: uuid.UUID
    ) -> FamilyDetailPublic:
        """Return full family detail. Caller must be an active member."""
        family = self._require_family(family_id)
        caller = self._resolve_caller(user_id, family_id)
        self.guard.require(caller, "view_family")

        members = list(self.repo.list_active_members(family_id))
        return _family_to_detail(family, members)

    def update_family(
        self,
        user_id: uuid.UUID,
        family_id: uuid.UUID,
        payload: FamilyUpdate,
    ) -> FamilyDetailPublic:
        """Update family name or currency. Requires Admin or Owner role."""
        family = self._require_family(family_id)
        caller = self._resolve_caller(user_id, family_id)
        self.guard.require(caller, "update_family")

        if payload.name is None and payload.currency is None:
            raise FamilyServiceError("At least one field must be provided to update.")

        self.repo.update(family, payload)
        self.db.commit()
        self.db.refresh(family)

        members = list(self.repo.list_active_members(family_id))
        return _family_to_detail(family, members)

    def delete_family(
        self, user_id: uuid.UUID, family_id: uuid.UUID
    ) -> None:
        """Hard-delete a family and all cascaded data. Requires Owner role."""
        family = self._require_family(family_id)
        caller = self._resolve_caller(user_id, family_id)
        self.guard.require(caller, "delete_family")

        self.repo.delete(family)
        self.db.commit()

    # -----------------------------------------------------------------------
    # Invitation Flow
    # -----------------------------------------------------------------------

    def invite_member(
        self,
        user_id: uuid.UUID,
        family_id: uuid.UUID,
        payload: InviteMemberRequest,
    ) -> InviteResponse:
        """Generate and persist an invitation token.

        Returns the raw token for the inviter to share out-of-band. The raw
        token is never stored — only its SHA-256 hash is persisted.

        Permission: Owner or Admin.
        """
        family = self._require_family(family_id)
        caller = self._resolve_caller(user_id, family_id)
        self.guard.require(caller, "invite_member")

        # Capacity check
        current_count = self.repo.count_active_members(family_id)
        if current_count >= MAX_FAMILY_MEMBERS:
            raise FamilyConflictError(
                f"Family has reached the maximum of {MAX_FAMILY_MEMBERS} members."
            )

        # Duplicate active member check
        existing_member = self.repo.get_member_by_email(family_id, payload.email)
        if existing_member is not None:
            raise FamilyConflictError(
                f"{payload.email} is already an active member of this family."
            )

        # Duplicate pending invitation check
        pending = self.repo.get_pending_invitation_by_email(family_id, payload.email)
        if pending is not None:
            raise FamilyConflictError(
                f"An active invitation for {payload.email} already exists. "
                "Revoke it before sending a new one."
            )

        # Generate token
        raw_token = secrets.token_urlsafe(INVITATION_TOKEN_BYTES)
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=INVITATION_TTL_HOURS)

        invitation = self.repo.create_invitation(
            family_id=family_id,
            invited_by_id=caller.id,  # type: ignore[union-attr]
            email=payload.email,
            role=payload.role,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.commit()
        self.db.refresh(invitation)

        return InviteResponse(
            invitation_id=invitation.id,
            family_id=invitation.family_id,
            email=invitation.email,
            role=invitation.role,
            invitation_token=raw_token,  # returned once, never stored
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )

    def accept_invite(
        self, user: User, payload: AcceptInviteRequest
    ) -> FamilyMemberPublic:
        """Validate the invitation token and create a FamilyMember for the caller.

        Validation rules:
        1. Token hash must exist in family_invitations.
        2. Invitation must not be expired (expires_at > now).
        3. Invitation must not already be accepted or revoked.
        4. Caller's email must match the invited email (case-insensitive).
        5. Caller must not already be an active member of the family.
        """
        token_hash = hash_token(payload.token)
        invitation = self.repo.get_invitation_by_token_hash(token_hash)

        if invitation is None:
            raise InvitationError("Invitation token is invalid.")

        now = datetime.now(timezone.utc)

        if invitation.accepted_at is not None:
            raise InvitationError("This invitation has already been accepted.")

        if invitation.revoked_at is not None:
            raise InvitationError("This invitation has been revoked.")

        # Compare expiry (make expires_at timezone-aware if stored as naive UTC)
        expires_at = invitation.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            raise InvitationError("This invitation has expired.")

        # Email ownership check
        if user.email.lower() != invitation.email.lower():
            raise InvitationError(
                "This invitation was sent to a different email address."
            )

        # Duplicate membership guard
        existing = self.repo.get_member_by_user(invitation.family_id, user.id)
        if existing is not None:
            raise FamilyConflictError("You are already a member of this family.")

        # Create member record
        member = self.repo.add_member(
            family_id=invitation.family_id,
            user_id=user.id,
            name=user.display_name,
            role=invitation.role,
            email=user.email,
        )

        # Mark invitation accepted
        self.repo.mark_invitation_accepted(invitation, accepted_at=now)

        self.db.commit()
        self.db.refresh(member)

        return _member_to_public(member)

    # -----------------------------------------------------------------------
    # Membership Management
    # -----------------------------------------------------------------------

    def remove_member(
        self,
        user_id: uuid.UUID,
        family_id: uuid.UUID,
        member_id: uuid.UUID,
    ) -> None:
        """Deactivate a family member. Requires Admin or Owner role.

        Constraints:
        - An Owner cannot be removed (ownership must be transferred first).
        - An Admin cannot remove another Admin (Owner-only action).
        - A member cannot remove themselves — use leave_family instead.
        """
        self._require_family(family_id)
        caller = self._resolve_caller(user_id, family_id)
        self.guard.require(caller, "remove_member")

        target = self.repo.get_member_by_id(member_id)
        if target is None or target.family_id != family_id or not target.is_active:
            raise FamilyMemberNotFoundError("Member not found in this family.")

        # Cannot remove the Owner
        if target.role == FamilyRole.OWNER:
            raise FamilyPermissionError(
                "The family Owner cannot be removed. Transfer ownership first."
            )

        # Admin cannot remove another Admin — only Owner can
        if (
            target.role == FamilyRole.ADMIN
            and caller is not None
            and caller.role != FamilyRole.OWNER
        ):
            raise FamilyPermissionError(
                "Only the family Owner can remove an Admin."
            )

        # Cannot remove yourself via this endpoint
        if caller is not None and target.id == caller.id:
            raise FamilyPermissionError(
                "Cannot remove yourself. Use the leave endpoint instead."
            )

        self.repo.deactivate_member(target)
        self.db.commit()

    def leave_family(
        self, user_id: uuid.UUID, family_id: uuid.UUID
    ) -> None:
        """Allow a member to voluntarily leave a family.

        The Owner cannot leave (they must delete the family or transfer ownership).
        """
        self._require_family(family_id)
        caller = self._resolve_caller(user_id, family_id)
        self.guard.require(caller, "leave_family")

        if caller is not None and caller.role == FamilyRole.OWNER:
            raise FamilyPermissionError(
                "The Owner cannot leave the family. "
                "Delete the family or transfer ownership first."
            )

        self.repo.deactivate_member(caller)  # type: ignore[arg-type]
        self.db.commit()

    # -----------------------------------------------------------------------
    # Shared Analytics
    # -----------------------------------------------------------------------

    def get_shared_analytics(
        self, user_id: uuid.UUID, family_id: uuid.UUID
    ) -> FamilyAnalytics:
        """Return aggregated analytics for a family. Requires membership."""
        family = self._require_family(family_id)
        caller = self._resolve_caller(user_id, family_id)
        self.guard.require(caller, "view_family")

        expense_data = self.repo.get_shared_expense_totals(family_id)
        goal_data = self.repo.get_shared_goal_totals(family_id)
        member_count = self.repo.count_active_members(family_id)

        return FamilyAnalytics(
            family_id=family.id,
            family_name=family.name,
            expenses=SharedExpenseSummary(
                total_amount=expense_data["total_amount"],
                expense_count=expense_data["expense_count"],
                top_category=None,  # reserved for future AI insights
                current_month_total=expense_data["current_month_total"],
            ),
            budget=SharedBudgetSummary(
                total_planned=expense_data.get("total_planned", 0),  # type: ignore[arg-type]
                total_spent=expense_data["total_amount"],
                total_remaining=max(  # type: ignore[type-var]
                    expense_data.get("total_planned", 0) - expense_data["total_amount"], 0
                ),
                member_count=member_count,
            ),
            goals=SharedGoalSummary(
                total_goals=goal_data["total_goals"],
                active_goals=goal_data["active_goals"],
                completed_goals=goal_data["completed_goals"],
                total_saved=goal_data["total_saved"],
                total_target=goal_data["total_target"],
            ),
            generated_at=datetime.now(timezone.utc),
        )
