"""Unit and integration tests for the Category system.

Tests CRUD endpoints, system-category immutability guards,
slug uniqueness enforcement, and soft-delete (archive) behaviour.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.category import SpendingCategory
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.category import (
    CategoryInUseError,
    CategoryNotFoundError,
    CategoryService,
    CategorySlugConflictError,
    SystemCategoryMutationError,
)


# ---------------------------------------------------------------------------
# Endpoint Integration Tests
# ---------------------------------------------------------------------------

class TestCategoryEndpoints:
    """Verifies route-level HTTP responses for category CRUD."""

    @pytest.fixture(autouse=True)
    def setup_app_override(self, mock_user: User, mock_db: MagicMock) -> None:
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        yield
        app.dependency_overrides.clear()

    @patch("app.services.category.CategoryService.list_categories")
    def test_list_categories_returns_200(
        self, mock_list: MagicMock, mock_system_category: SpendingCategory
    ) -> None:
        mock_list.return_value = [mock_system_category]
        client = TestClient(app)

        response = client.get("/api/v1/categories")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "items" in body
        assert len(body["items"]) == 1

    @patch("app.services.category.CategoryService.create_category")
    def test_create_custom_category_success(
        self, mock_create: MagicMock, mock_custom_category: SpendingCategory
    ) -> None:
        mock_create.return_value = mock_custom_category
        client = TestClient(app)

        payload = {
            "slug": "my-coffee",
            "name": "Coffee",
            "icon": "Coffee",
            "color": "#6B8EFF",
        }
        response = client.post("/api/v1/categories", json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        mock_create.assert_called_once()

    @patch("app.services.category.CategoryService.create_category")
    def test_create_category_duplicate_slug_returns_409(
        self, mock_create: MagicMock
    ) -> None:
        mock_create.side_effect = CategorySlugConflictError("Slug taken")
        client = TestClient(app)

        payload = {"slug": "my-coffee", "name": "Coffee 2", "icon": "Coffee", "color": "#FFF"}
        response = client.post("/api/v1/categories", json=payload)
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_category_missing_name_returns_422(self) -> None:
        client = TestClient(app)
        response = client.post("/api/v1/categories", json={"slug": "no-name", "icon": "x", "color": "#f"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("app.services.category.CategoryService.delete_category")
    def test_delete_category_success(
        self, mock_delete: MagicMock, mock_custom_category: SpendingCategory
    ) -> None:
        client = TestClient(app)
        response = client.delete(f"/api/v1/categories/{mock_custom_category.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_delete.assert_called_once()

    @patch("app.services.category.CategoryService.delete_category")
    def test_delete_system_category_returns_403(
        self, mock_delete: MagicMock, mock_system_category: SpendingCategory
    ) -> None:
        mock_delete.side_effect = SystemCategoryMutationError("System categories cannot be archived.")
        client = TestClient(app)

        response = client.delete(f"/api/v1/categories/{mock_system_category.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "system" in response.json()["error"]["message"].lower()

    @patch("app.services.category.CategoryService.delete_category")
    def test_delete_category_in_use_returns_409(
        self, mock_delete: MagicMock, mock_custom_category: SpendingCategory
    ) -> None:
        mock_delete.side_effect = CategoryInUseError("Category has linked expenses.")
        client = TestClient(app)

        response = client.delete(f"/api/v1/categories/{mock_custom_category.id}")
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "linked expenses" in response.json()["error"]["message"].lower()

    @patch("app.services.category.CategoryService.delete_category")
    def test_delete_category_force_flag_accepted(
        self, mock_delete: MagicMock, mock_custom_category: SpendingCategory
    ) -> None:
        client = TestClient(app)
        response = client.delete(f"/api/v1/categories/{mock_custom_category.id}?force=true")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        _, kwargs = mock_delete.call_args
        assert kwargs["force"] is True


# ---------------------------------------------------------------------------
# Service Unit Tests
# ---------------------------------------------------------------------------

class TestCategoryService:
    """Verifies CategoryService business rules without HTTP layer."""

    def test_create_category_duplicate_slug_raises_error(
        self, mock_db: MagicMock, mock_user: User
    ) -> None:
        service = CategoryService(mock_db)
        service.repo.slug_exists_for_user = MagicMock(return_value=True)

        payload = CategoryCreate(slug="existing-slug", name="Existing", icon="x", color="#000")
        with pytest.raises(CategorySlugConflictError) as exc_info:
            service.create_category(user_id=mock_user.id, payload=payload)
        assert "existing-slug" in str(exc_info.value)

    def test_delete_system_category_raises_mutation_error(
        self,
        mock_db: MagicMock,
        mock_user: User,
        mock_system_category: SpendingCategory,
    ) -> None:
        service = CategoryService(mock_db)
        service.repo.get_by_id = MagicMock(return_value=mock_system_category)

        with pytest.raises(SystemCategoryMutationError):
            service.delete_category(user_id=mock_user.id, category_id=mock_system_category.id)

    def test_delete_category_not_owned_raises_not_found(
        self,
        mock_db: MagicMock,
        mock_user: User,
        mock_other_user: User,
        mock_custom_category: SpendingCategory,
    ) -> None:
        service = CategoryService(mock_db)
        # Category is owned by mock_user, not mock_other_user
        service.repo.get_by_id = MagicMock(return_value=mock_custom_category)

        with pytest.raises(CategoryNotFoundError):
            service.delete_category(
                user_id=mock_other_user.id,
                category_id=mock_custom_category.id,
            )

    def test_delete_category_in_use_without_force_raises_error(
        self,
        mock_db: MagicMock,
        mock_user: User,
        mock_custom_category: SpendingCategory,
    ) -> None:
        service = CategoryService(mock_db)
        service.repo.get_by_id = MagicMock(return_value=mock_custom_category)
        service.repo.has_expenses = MagicMock(return_value=True)

        with pytest.raises(CategoryInUseError) as exc_info:
            service.delete_category(
                user_id=mock_user.id,
                category_id=mock_custom_category.id,
                force=False,
            )
        assert "force=true" in str(exc_info.value).lower()

    def test_delete_category_in_use_with_force_archives(
        self,
        mock_db: MagicMock,
        mock_user: User,
        mock_custom_category: SpendingCategory,
    ) -> None:
        service = CategoryService(mock_db)
        service.repo.get_by_id = MagicMock(return_value=mock_custom_category)
        service.repo.has_expenses = MagicMock(return_value=True)
        service.repo.archive = MagicMock()

        # force=True bypasses the in-use guard
        service.delete_category(
            user_id=mock_user.id,
            category_id=mock_custom_category.id,
            force=True,
        )
        service.repo.archive.assert_called_once_with(mock_custom_category)
        mock_db.commit.assert_called_once()

    def test_update_system_category_raises_mutation_error(
        self,
        mock_db: MagicMock,
        mock_user: User,
        mock_system_category: SpendingCategory,
    ) -> None:
        service = CategoryService(mock_db)
        service.repo.get_by_id = MagicMock(return_value=mock_system_category)

        payload = CategoryUpdate(name="Hacked System Category")
        with pytest.raises(SystemCategoryMutationError):
            service.update_category(
                user_id=mock_user.id,
                category_id=mock_system_category.id,
                payload=payload,
            )

    def test_update_category_not_found_raises_error(
        self, mock_db: MagicMock, mock_user: User
    ) -> None:
        service = CategoryService(mock_db)
        service.repo.get_by_id = MagicMock(return_value=None)

        payload = CategoryUpdate(name="Ghost")
        with pytest.raises(CategoryNotFoundError):
            service.update_category(
                user_id=mock_user.id,
                category_id=uuid.uuid4(),
                payload=payload,
            )
