"""Repository for spending_categories table.

All database access for categories lives here.  Business rules (ownership
checks, system-category guards, slug conflict checks) live in the service
layer.
"""

from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session, joinedload

from app.models.category import SpendingCategory


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def list_visible(
        self,
        *,
        user_id: uuid.UUID,
        include_archived: bool = False,
    ) -> Sequence[SpendingCategory]:
        """Return system categories + user-owned custom categories.

        System categories always come first (ordered by display_order),
        then custom categories ordered by display_order.
        """
        stmt = (
            select(SpendingCategory)
            .where(
                or_(
                    SpendingCategory.user_id.is_(None),  # system
                    SpendingCategory.user_id == user_id,  # user's own
                )
            )
            .order_by(
                SpendingCategory.is_system.desc(),   # system first
                SpendingCategory.display_order.asc(),
                SpendingCategory.created_at.asc(),
            )
        )
        if not include_archived:
            stmt = stmt.where(SpendingCategory.is_archived.is_(False))

        return self.db.scalars(stmt).all()

    def get_by_id(self, category_id: uuid.UUID) -> Optional[SpendingCategory]:
        """Return a category by primary key (any scope)."""
        return self.db.scalar(
            select(SpendingCategory).where(SpendingCategory.id == category_id)
        )

    def get_by_id_for_user(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[SpendingCategory]:
        """Return a category visible to the user (system or owned custom)."""
        return self.db.scalar(
            select(SpendingCategory)
            .where(
                SpendingCategory.id == category_id,
                or_(
                    SpendingCategory.user_id.is_(None),
                    SpendingCategory.user_id == user_id,
                ),
            )
        )

    def get_custom_by_id_and_owner(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[SpendingCategory]:
        """Return a custom category owned by the given user, or None."""
        return self.db.scalar(
            select(SpendingCategory)
            .where(
                SpendingCategory.id == category_id,
                SpendingCategory.user_id == user_id,
                SpendingCategory.is_system.is_(False),
            )
        )

    def slug_exists_for_user(
        self,
        *,
        slug: str,
        user_id: uuid.UUID,
        exclude_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """True if a custom category with this slug already exists for the user."""
        stmt = select(SpendingCategory.id).where(
            SpendingCategory.user_id == user_id,
            func.lower(SpendingCategory.slug) == slug.lower(),
        )
        if exclude_id is not None:
            stmt = stmt.where(SpendingCategory.id != exclude_id)
        return self.db.scalar(stmt) is not None

    def has_expenses(self, category_id: uuid.UUID) -> bool:
        """True if any expense row references this category."""
        from app.models.expense import Expense

        stmt = select(Expense.id).where(Expense.category_id == category_id).limit(1)
        return self.db.scalar(stmt) is not None

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        user_id: uuid.UUID,
        slug: str,
        name: str,
        icon: str,
        color: str,
        display_order: int = 0,
    ) -> SpendingCategory:
        category = SpendingCategory(
            user_id=user_id,
            slug=slug.lower(),
            name=name,
            icon=icon,
            color=color,
            is_system=False,
            is_archived=False,
            display_order=display_order,
        )
        self.db.add(category)
        return category

    def update(
        self,
        category: SpendingCategory,
        *,
        name: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        display_order: Optional[int] = None,
    ) -> SpendingCategory:
        if name is not None:
            category.name = name
        if icon is not None:
            category.icon = icon
        if color is not None:
            category.color = color
        if display_order is not None:
            category.display_order = display_order
        return category

    def archive(self, category: SpendingCategory) -> SpendingCategory:
        category.is_archived = True
        return category
