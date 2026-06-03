"""Repository for families, family_members, and family_invitations tables.

All direct database query and persistence operations for the Family system live
here. Business logic, permission checks, and token generation belong in the
FamilyService layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import CurrencyCode, FamilyRole, SavingsGoalStatus
from app.models.expense import Expense
from app.models.family import Family, FamilyInvitation, FamilyMember
from app.models.goal import SavingsGoal
from app.schemas.family import FamilyCreate, FamilyUpdate


class FamilyRepository:
    """Manages all database interactions for families, members, and invitations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # -----------------------------------------------------------------------
    # Family Reads
    # -----------------------------------------------------------------------

    def get_by_id(self, family_id: uuid.UUID) -> Family | None:
        """Retrieve a family by its UUID."""
        stmt = select(Family).where(Family.id == family_id)
        return self.db.scalar(stmt)

    def get_by_owner(self, user_id: uuid.UUID) -> Family | None:
        """Retrieve the family owned by a user (one owner → one family)."""
        stmt = select(Family).where(Family.owner_user_id == user_id)
        return self.db.scalar(stmt)

    def list_for_user(self, user_id: uuid.UUID) -> Sequence[Family]:
        """Return all families where the user is an active member (or owner).

        Joins through family_members so membership-only families are included.
        """
        stmt = (
            select(Family)
            .join(FamilyMember, FamilyMember.family_id == Family.id)
            .where(FamilyMember.user_id == user_id)
            .where(FamilyMember.is_active.is_(True))
            .order_by(Family.created_at.desc())
        )
        return self.db.scalars(stmt).all()

    def count_active_members(self, family_id: uuid.UUID) -> int:
        """Return the number of active members in a family."""
        stmt = (
            select(func.count())
            .select_from(FamilyMember)
            .where(FamilyMember.family_id == family_id)
            .where(FamilyMember.is_active.is_(True))
        )
        return self.db.scalar(stmt) or 0

    # -----------------------------------------------------------------------
    # Family Writes
    # -----------------------------------------------------------------------

    def create(
        self,
        owner_user_id: uuid.UUID,
        owner_name: str,
        owner_email: str | None,
        payload: FamilyCreate,
    ) -> Family:
        """Create a new family and add the owner as the first member (Owner role).

        Both the Family and its owner FamilyMember record are added to the
        session but NOT committed — commit responsibility belongs to the service.
        """
        family = Family(
            owner_user_id=owner_user_id,
            name=payload.name,
            currency=payload.currency,
        )
        self.db.add(family)
        self.db.flush()  # obtain family.id before creating the member FK

        # Auto-create the Owner's FamilyMember entry.
        owner_member = FamilyMember(
            family_id=family.id,
            user_id=owner_user_id,
            name=owner_name,
            role=FamilyRole.OWNER,
            email=owner_email,
            is_active=True,
        )
        self.db.add(owner_member)
        return family

    def update(self, family: Family, payload: FamilyUpdate) -> Family:
        """Apply a partial update to a family record."""
        if payload.name is not None:
            family.name = payload.name
        if payload.currency is not None:
            family.currency = payload.currency
        return family

    def delete(self, family: Family) -> None:
        """Hard-delete a family and all cascaded children."""
        self.db.delete(family)

    # -----------------------------------------------------------------------
    # Member Reads
    # -----------------------------------------------------------------------

    def get_member_by_id(self, member_id: uuid.UUID) -> FamilyMember | None:
        """Retrieve a member by UUID."""
        stmt = select(FamilyMember).where(FamilyMember.id == member_id)
        return self.db.scalar(stmt)

    def get_member_by_user(
        self, family_id: uuid.UUID, user_id: uuid.UUID
    ) -> FamilyMember | None:
        """Retrieve a member by their linked user account within a family."""
        stmt = (
            select(FamilyMember)
            .where(FamilyMember.family_id == family_id)
            .where(FamilyMember.user_id == user_id)
            .where(FamilyMember.is_active.is_(True))
        )
        return self.db.scalar(stmt)

    def get_member_by_email(
        self, family_id: uuid.UUID, email: str
    ) -> FamilyMember | None:
        """Retrieve an active member by email (case-insensitive) within a family."""
        stmt = (
            select(FamilyMember)
            .where(FamilyMember.family_id == family_id)
            .where(func.lower(FamilyMember.email) == email.lower())
            .where(FamilyMember.is_active.is_(True))
        )
        return self.db.scalar(stmt)

    def list_active_members(self, family_id: uuid.UUID) -> Sequence[FamilyMember]:
        """Return all active members for a family, ordered by role then name."""
        stmt = (
            select(FamilyMember)
            .where(FamilyMember.family_id == family_id)
            .where(FamilyMember.is_active.is_(True))
            .order_by(FamilyMember.created_at.asc())
        )
        return self.db.scalars(stmt).all()

    # -----------------------------------------------------------------------
    # Member Writes
    # -----------------------------------------------------------------------

    def add_member(
        self,
        family_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        role: FamilyRole,
        email: str | None = None,
        avatar_url: str | None = None,
        spending_limit: Decimal | None = None,
    ) -> FamilyMember:
        """Create a new active FamilyMember record (not yet committed)."""
        member = FamilyMember(
            family_id=family_id,
            user_id=user_id,
            name=name,
            role=role,
            email=email,
            avatar_url=avatar_url,
            spending_limit=spending_limit,
            is_active=True,
        )
        self.db.add(member)
        return member

    def deactivate_member(self, member: FamilyMember) -> None:
        """Soft-delete a member by setting is_active = False."""
        member.is_active = False

    # -----------------------------------------------------------------------
    # Invitation Reads
    # -----------------------------------------------------------------------

    def get_invitation_by_token_hash(self, token_hash: str) -> FamilyInvitation | None:
        """Retrieve an invitation by the SHA-256 hash of the raw token."""
        stmt = select(FamilyInvitation).where(
            FamilyInvitation.token_hash == token_hash
        )
        return self.db.scalar(stmt)

    def get_pending_invitation_by_email(
        self, family_id: uuid.UUID, email: str
    ) -> FamilyInvitation | None:
        """Return an outstanding (not accepted/revoked/expired) invitation for an email."""
        now = datetime.utcnow()
        stmt = (
            select(FamilyInvitation)
            .where(FamilyInvitation.family_id == family_id)
            .where(func.lower(FamilyInvitation.email) == email.lower())
            .where(FamilyInvitation.accepted_at.is_(None))
            .where(FamilyInvitation.revoked_at.is_(None))
            .where(FamilyInvitation.expires_at > now)
        )
        return self.db.scalar(stmt)

    # -----------------------------------------------------------------------
    # Invitation Writes
    # -----------------------------------------------------------------------

    def create_invitation(
        self,
        family_id: uuid.UUID,
        invited_by_id: uuid.UUID,
        email: str,
        role: FamilyRole,
        token_hash: str,
        expires_at: datetime,
    ) -> FamilyInvitation:
        """Persist a new invitation record (not yet committed)."""
        invitation = FamilyInvitation(
            family_id=family_id,
            invited_by_id=invited_by_id,
            email=email.lower(),
            role=role,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(invitation)
        return invitation

    def mark_invitation_accepted(
        self, invitation: FamilyInvitation, accepted_at: datetime
    ) -> None:
        """Mark an invitation as accepted (single-use terminal state)."""
        invitation.accepted_at = accepted_at

    def revoke_invitation(
        self, invitation: FamilyInvitation, revoked_at: datetime
    ) -> None:
        """Mark an invitation as revoked."""
        invitation.revoked_at = revoked_at

    # -----------------------------------------------------------------------
    # Shared Analytics Reads
    # -----------------------------------------------------------------------

    def get_shared_expense_totals(
        self, family_id: uuid.UUID
    ) -> dict:
        """Aggregate expense data across all active members of a family."""
        from sqlalchemy import case

        # Get all active member user_ids for this family
        member_ids_stmt = (
            select(FamilyMember.user_id)
            .where(FamilyMember.family_id == family_id)
            .where(FamilyMember.is_active.is_(True))
            .where(FamilyMember.user_id.is_not(None))
        )
        member_user_ids = [row for row in self.db.scalars(member_ids_stmt).all()]

        if not member_user_ids:
            return {
                "total_amount": Decimal("0.00"),
                "expense_count": 0,
                "current_month_total": Decimal("0.00"),
            }

        from datetime import date

        today = date.today()
        month_start = date(today.year, today.month, 1)

        total_stmt = (
            select(
                func.coalesce(func.sum(Expense.amount), Decimal("0.00")).label("total"),
                func.count(Expense.id).label("count"),
                func.coalesce(
                    func.sum(
                        case(
                            (Expense.expense_date >= month_start, Expense.amount),
                            else_=Decimal("0.00"),
                        )
                    ),
                    Decimal("0.00"),
                ).label("month_total"),
            )
            .where(Expense.user_id.in_(member_user_ids))
        )

        row = self.db.execute(total_stmt).one()
        return {
            "total_amount": row.total or Decimal("0.00"),
            "expense_count": row.count or 0,
            "current_month_total": row.month_total or Decimal("0.00"),
        }

    def get_shared_goal_totals(self, family_id: uuid.UUID) -> dict:
        """Aggregate savings goal data across all active members of a family."""
        member_ids_stmt = (
            select(FamilyMember.user_id)
            .where(FamilyMember.family_id == family_id)
            .where(FamilyMember.is_active.is_(True))
            .where(FamilyMember.user_id.is_not(None))
        )
        member_user_ids = list(self.db.scalars(member_ids_stmt).all())

        if not member_user_ids:
            return {
                "total_goals": 0,
                "active_goals": 0,
                "completed_goals": 0,
                "total_saved": Decimal("0.00"),
                "total_target": Decimal("0.00"),
            }

        goals: Sequence[SavingsGoal] = self.db.scalars(
            select(SavingsGoal).where(SavingsGoal.user_id.in_(member_user_ids))
        ).all()

        total_goals = len(goals)
        active_goals = sum(1 for g in goals if g.status == SavingsGoalStatus.ACTIVE)
        completed_goals = sum(1 for g in goals if g.status == SavingsGoalStatus.COMPLETED)
        total_saved = sum((g.current_amount for g in goals), Decimal("0.00"))
        total_target = sum((g.target_amount for g in goals), Decimal("0.00"))

        return {
            "total_goals": total_goals,
            "active_goals": active_goals,
            "completed_goals": completed_goals,
            "total_saved": total_saved,
            "total_target": total_target,
        }
