"""Category service.

Owns all business rules for spending categories:
- Only custom categories can be created by users (is_system is always false here)
- System categories are read-only (403 on mutation attempts)
- Slug must be unique within the user's custom scope
- Archiving a category with linked expenses requires the caller to pass force=True
"""

from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import SpendingCategory
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------

class CategoryServiceError(Exception):
    """Base for category service errors."""


class CategoryNotFoundError(CategoryServiceError):
    """Raised when a category is not found or not visible to the user."""


class SystemCategoryMutationError(CategoryServiceError):
    """Raised when attempting to mutate a system-owned category."""


class CategorySlugConflictError(CategoryServiceError):
    """Raised when a slug is already taken in the user's category scope."""


class CategoryInUseError(CategoryServiceError):
    """Raised when archiving a category that still has linked expenses."""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CategoryRepository(db)

    def list_categories(
        self,
        *,
        user_id: uuid.UUID,
        include_archived: bool = False,
    ) -> list[SpendingCategory]:
        return list(
            self.repo.list_visible(user_id=user_id, include_archived=include_archived)
        )

    def create_category(
        self,
        *,
        user_id: uuid.UUID,
        payload: CategoryCreate,
    ) -> SpendingCategory:
        if self.repo.slug_exists_for_user(slug=payload.slug, user_id=user_id):
            raise CategorySlugConflictError(
                f"A custom category with slug '{payload.slug}' already exists."
            )

        category = self.repo.create(
            user_id=user_id,
            slug=payload.slug,
            name=payload.name,
            icon=payload.icon,
            color=payload.color,
            display_order=payload.display_order,
        )

        try:
            self.db.flush()
            self.db.commit()
            self.db.refresh(category)
        except IntegrityError as exc:
            self.db.rollback()
            raise CategorySlugConflictError(
                "A category with this slug already exists."
            ) from exc

        return category

    def update_category(
        self,
        *,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        payload: CategoryUpdate,
    ) -> SpendingCategory:
        category = self.repo.get_by_id(category_id)

        if category is None:
            raise CategoryNotFoundError(f"Category {category_id} not found.")

        if category.is_system:
            raise SystemCategoryMutationError(
                "System categories cannot be modified."
            )

        # Verify the authenticated user owns this custom category
        if category.user_id != user_id:
            raise CategoryNotFoundError(
                f"Category {category_id} not found."  # deliberate opaque message
            )

        self.repo.update(
            category,
            name=payload.name,
            icon=payload.icon,
            color=payload.color,
            display_order=payload.display_order,
        )

        try:
            self.db.commit()
            self.db.refresh(category)
        except IntegrityError as exc:
            self.db.rollback()
            raise CategorySlugConflictError(
                "Update failed due to a conflict."
            ) from exc

        return category

    def delete_category(
        self,
        *,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        force: bool = False,
    ) -> None:
        """Soft-delete (archive) a custom category.

        Args:
            user_id: The authenticated user.
            category_id: The category to archive.
            force: If True, archive even when the category has linked expenses.
                   Expenses remain linked; they simply reference an archived
                   category until they are updated.

        Raises:
            CategoryNotFoundError: Category doesn't exist or user doesn't own it.
            SystemCategoryMutationError: Attempt to archive a system category.
            CategoryInUseError: Category has linked expenses and force=False.
        """
        category = self.repo.get_by_id(category_id)

        if category is None:
            raise CategoryNotFoundError(f"Category {category_id} not found.")

        if category.is_system:
            raise SystemCategoryMutationError(
                "System categories cannot be archived."
            )

        if category.user_id != user_id:
            raise CategoryNotFoundError(f"Category {category_id} not found.")

        if not force and self.repo.has_expenses(category_id):
            raise CategoryInUseError(
                "This category has linked expenses. "
                "Pass ?force=true to archive it anyway."
            )

        self.repo.archive(category)
        self.db.commit()
