"""Category routes.

All endpoints require a valid JWT access token (Bearer).

GET  /categories                — list system + custom categories
POST /categories                — create a custom category
PATCH /categories/{category_id} — update a custom category
DELETE /categories/{category_id} — soft-archive a custom category
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryListResponse,
    CategoryPublic,
    CategoryUpdate,
)
from app.services.category import (
    CategoryInUseError,
    CategoryNotFoundError,
    CategoryService,
    CategorySlugConflictError,
    SystemCategoryMutationError,
)

router = APIRouter(prefix="/categories", tags=["categories"])


# ---------------------------------------------------------------------------
# GET /categories
# ---------------------------------------------------------------------------

@router.get("", response_model=CategoryListResponse)
def list_categories(
    include_archived: Annotated[
        bool,
        Query(alias="includeArchived", description="Include archived categories in the response."),
    ] = False,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> CategoryListResponse:
    """Return system categories and the user's custom categories.

    System categories are returned first, ordered by ``display_order``,
    followed by the user's custom categories.
    """
    service = CategoryService(db)
    items = service.list_categories(
        user_id=user.id,
        include_archived=include_archived,
    )
    return CategoryListResponse(items=items)


# ---------------------------------------------------------------------------
# POST /categories
# ---------------------------------------------------------------------------

@router.post("", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> CategoryPublic:
    """Create a custom category for the authenticated user."""
    service = CategoryService(db)
    try:
        category = service.create_category(user_id=user.id, payload=payload)
    except CategorySlugConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return CategoryPublic.model_validate(category)


# ---------------------------------------------------------------------------
# PATCH /categories/{category_id}
# ---------------------------------------------------------------------------

@router.patch("/{category_id}", response_model=CategoryPublic)
def update_category(
    category_id: str,
    payload: CategoryUpdate,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> CategoryPublic:
    """Update a custom category.  System categories return 403."""
    import uuid as _uuid

    try:
        cat_uuid = _uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="category_id must be a valid UUID.",
        )

    service = CategoryService(db)
    try:
        category = service.update_category(
            user_id=user.id,
            category_id=cat_uuid,
            payload=payload,
        )
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SystemCategoryMutationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except CategorySlugConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return CategoryPublic.model_validate(category)


# ---------------------------------------------------------------------------
# DELETE /categories/{category_id}
# ---------------------------------------------------------------------------

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    force: Annotated[
        bool,
        Query(description="Archive even if the category has linked expenses."),
    ] = False,
    user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> None:
    """Soft-archive a custom category.

    - Returns **403** if the category is a system category.
    - Returns **404** if the category does not exist or is not owned by the user.
    - Returns **409** if the category has linked expenses and ``force`` is ``false``.
    """
    import uuid as _uuid

    try:
        cat_uuid = _uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="category_id must be a valid UUID.",
        )

    service = CategoryService(db)
    try:
        service.delete_category(user_id=user.id, category_id=cat_uuid, force=force)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SystemCategoryMutationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except CategoryInUseError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
