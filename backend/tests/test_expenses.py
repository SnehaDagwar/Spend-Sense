"""Unit and integration tests for the Expense system.

Tests CRUD endpoint behaviour, service ownership checks, category
validation guards, and pagination cursor mechanics.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.category import SpendingCategory
from app.models.expense import Expense
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseFilters, ExpenseUpdate
from app.services.expense import (
    ExpenseCategoryError,
    ExpenseNotFoundError,
    ExpenseService,
    ExpenseServiceError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_expense_public_stub(expense: Expense) -> dict:
    return {
        "id": str(expense.id),
        "categoryId": str(expense.category_id),
        "amount": str(expense.amount),
        "currency": "INR",
        "expenseDate": expense.expense_date.isoformat(),
        "note": expense.note,
        "paymentMethod": expense.payment_method,
        "tags": expense.tags,
        "isRecurring": expense.is_recurring,
    }


# ---------------------------------------------------------------------------
# Endpoint Integration Tests
# ---------------------------------------------------------------------------

class TestExpenseEndpoints:
    """Verifies route-level HTTP responses and error mappings."""

    @pytest.fixture(autouse=True)
    def setup_app_override(self, mock_user: User, mock_db: MagicMock) -> None:
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        yield
        app.dependency_overrides.clear()

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    @patch("app.services.expense.ExpenseService.list_expenses")
    def test_list_expenses_returns_200(
        self, mock_list: MagicMock, mock_expense: Expense
    ) -> None:
        from app.schemas.expense import ExpenseListResponse, ExpensePublic

        mock_list.return_value = ([mock_expense], None)
        client = TestClient(app)

        response = client.get("/api/v1/expenses")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "items" in body
        assert body["totalReturned"] == 1
        mock_list.assert_called_once()

    @patch("app.services.expense.ExpenseService.list_expenses")
    def test_list_expenses_month_filter(
        self, mock_list: MagicMock, mock_expense: Expense
    ) -> None:
        mock_list.return_value = ([mock_expense], None)
        client = TestClient(app)

        response = client.get("/api/v1/expenses?month=2026-06")
        assert response.status_code == 200
        args, kwargs = mock_list.call_args
        assert kwargs["filters"].month == "2026-06"

    @patch("app.services.expense.ExpenseService.list_expenses")
    def test_list_expenses_invalid_month_format_returns_422(
        self, mock_list: MagicMock
    ) -> None:
        client = TestClient(app)
        response = client.get("/api/v1/expenses?month=June-2026")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # ------------------------------------------------------------------
    # GET single
    # ------------------------------------------------------------------

    @patch("app.services.expense.ExpenseService.get_expense")
    def test_get_expense_success(
        self, mock_get: MagicMock, mock_expense: Expense
    ) -> None:
        mock_get.return_value = mock_expense
        client = TestClient(app)

        response = client.get(f"/api/v1/expenses/{mock_expense.id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == str(mock_expense.id)

    @patch("app.services.expense.ExpenseService.get_expense")
    def test_get_expense_not_found_returns_404(
        self, mock_get: MagicMock
    ) -> None:
        mock_get.side_effect = ExpenseNotFoundError("Not found")
        client = TestClient(app)

        response = client.get(f"/api/v1/expenses/{uuid.uuid4()}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_expense_invalid_uuid_returns_422(self) -> None:
        client = TestClient(app)
        response = client.get("/api/v1/expenses/not-a-valid-uuid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @patch("app.services.expense.ExpenseService.create_expense")
    def test_create_expense_success(
        self, mock_create: MagicMock, mock_expense: Expense
    ) -> None:
        mock_create.return_value = mock_expense
        client = TestClient(app)

        payload = {
            "categoryId": str(mock_expense.category_id),
            "amount": "450.00",
            "expenseDate": date.today().isoformat(),
            "currency": "INR",
        }
        response = client.post("/api/v1/expenses", json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        mock_create.assert_called_once()

    @patch("app.services.expense.ExpenseService.create_expense")
    def test_create_expense_invalid_category_returns_422(
        self, mock_create: MagicMock
    ) -> None:
        mock_create.side_effect = ExpenseCategoryError("Category not accessible")
        client = TestClient(app)

        payload = {
            "categoryId": str(uuid.uuid4()),
            "amount": "100.00",
            "expenseDate": date.today().isoformat(),
            "currency": "INR",
        }
        response = client.post("/api/v1/expenses", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_expense_missing_required_fields_returns_422(self) -> None:
        client = TestClient(app)
        # Missing categoryId and expenseDate
        response = client.post("/api/v1/expenses", json={"amount": 100})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_expense_negative_amount_returns_422(self) -> None:
        client = TestClient(app)
        payload = {
            "categoryId": str(uuid.uuid4()),
            "amount": "-50.00",
            "expenseDate": date.today().isoformat(),
            "currency": "INR",
        }
        response = client.post("/api/v1/expenses", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # ------------------------------------------------------------------
    # Update (PATCH)
    # ------------------------------------------------------------------

    @patch("app.services.expense.ExpenseService.update_expense")
    def test_update_expense_success(
        self, mock_update: MagicMock, mock_expense: Expense
    ) -> None:
        mock_expense.note = "Updated note"
        mock_update.return_value = mock_expense
        client = TestClient(app)

        response = client.patch(
            f"/api/v1/expenses/{mock_expense.id}",
            json={"note": "Updated note"},
        )
        assert response.status_code == status.HTTP_200_OK
        mock_update.assert_called_once()

    @patch("app.services.expense.ExpenseService.update_expense")
    def test_update_expense_not_found_returns_404(
        self, mock_update: MagicMock
    ) -> None:
        mock_update.side_effect = ExpenseNotFoundError("Not found")
        client = TestClient(app)

        response = client.patch(
            f"/api/v1/expenses/{uuid.uuid4()}",
            json={"note": "Ghost edit"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.services.expense.ExpenseService.update_expense")
    def test_update_expense_bad_category_returns_422(
        self, mock_update: MagicMock
    ) -> None:
        mock_update.side_effect = ExpenseCategoryError("Archived category")
        client = TestClient(app)

        response = client.patch(
            f"/api/v1/expenses/{uuid.uuid4()}",
            json={"categoryId": str(uuid.uuid4())},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @patch("app.services.expense.ExpenseService.delete_expense")
    def test_delete_expense_success(
        self, mock_delete: MagicMock, mock_expense: Expense
    ) -> None:
        client = TestClient(app)

        response = client.delete(f"/api/v1/expenses/{mock_expense.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_delete.assert_called_once_with(
            user_id=mock_delete.call_args[1]["user_id"],
            expense_id=mock_expense.id,
        )

    @patch("app.services.expense.ExpenseService.delete_expense")
    def test_delete_expense_not_found_returns_404(
        self, mock_delete: MagicMock
    ) -> None:
        mock_delete.side_effect = ExpenseNotFoundError("Not found")
        client = TestClient(app)

        response = client.delete(f"/api/v1/expenses/{uuid.uuid4()}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Service Unit Tests
# ---------------------------------------------------------------------------

class TestExpenseService:
    """Verifies service-level business logic: ownership, category validation, etc."""

    def test_get_expense_owned_by_different_user_raises_not_found(
        self, mock_db: MagicMock, mock_expense: Expense, mock_other_user: User
    ) -> None:
        service = ExpenseService(mock_db)
        service.repo.get_by_id_and_user = MagicMock(return_value=None)

        with pytest.raises(ExpenseNotFoundError):
            service.get_expense(user_id=mock_other_user.id, expense_id=mock_expense.id)

    def test_create_expense_inaccessible_category_raises_error(
        self, mock_db: MagicMock, mock_user: User
    ) -> None:
        service = ExpenseService(mock_db)
        service.categories.get_by_id_for_user = MagicMock(return_value=None)

        payload = ExpenseCreate(
            category_id=uuid.uuid4(),
            amount=Decimal("100.00"),
            expense_date=date.today(),
            currency="INR",
        )

        with pytest.raises(ExpenseCategoryError) as exc_info:
            service.create_expense(user_id=mock_user.id, payload=payload)
        assert "not found or not accessible" in str(exc_info.value).lower()

    def test_create_expense_archived_category_raises_error(
        self, mock_db: MagicMock, mock_user: User, mock_system_category: SpendingCategory
    ) -> None:
        service = ExpenseService(mock_db)
        mock_system_category.is_archived = True
        service.categories.get_by_id_for_user = MagicMock(return_value=mock_system_category)

        payload = ExpenseCreate(
            category_id=mock_system_category.id,
            amount=Decimal("500.00"),
            expense_date=date.today(),
            currency="INR",
        )

        with pytest.raises(ExpenseCategoryError) as exc_info:
            service.create_expense(user_id=mock_user.id, payload=payload)
        assert "archived" in str(exc_info.value).lower()

    def test_delete_expense_not_owned_raises_not_found(
        self, mock_db: MagicMock, mock_expense: Expense, mock_other_user: User
    ) -> None:
        service = ExpenseService(mock_db)
        service.repo.get_by_id_and_user = MagicMock(return_value=None)

        with pytest.raises(ExpenseNotFoundError):
            service.delete_expense(user_id=mock_other_user.id, expense_id=mock_expense.id)

    def test_delete_expense_delegates_to_repo(
        self, mock_db: MagicMock, mock_expense: Expense, mock_user: User
    ) -> None:
        service = ExpenseService(mock_db)
        service.repo.get_by_id_and_user = MagicMock(return_value=mock_expense)
        service.repo.delete = MagicMock()

        service.delete_expense(user_id=mock_user.id, expense_id=mock_expense.id)

        service.repo.delete.assert_called_once_with(mock_expense)
        mock_db.commit.assert_called_once()

    def test_update_expense_new_category_archived_raises_error(
        self,
        mock_db: MagicMock,
        mock_expense: Expense,
        mock_user: User,
        mock_system_category: SpendingCategory,
    ) -> None:
        service = ExpenseService(mock_db)
        service.repo.get_by_id_and_user = MagicMock(return_value=mock_expense)
        mock_system_category.is_archived = True
        service.categories.get_by_id_for_user = MagicMock(return_value=mock_system_category)

        new_cat_id = uuid.uuid4()
        payload = ExpenseUpdate(category_id=new_cat_id)

        with pytest.raises(ExpenseCategoryError):
            service.update_expense(
                user_id=mock_user.id,
                expense_id=mock_expense.id,
                payload=payload,
            )

    def test_list_expenses_invalid_cursor_raises_service_error(
        self, mock_db: MagicMock, mock_user: User
    ) -> None:
        service = ExpenseService(mock_db)

        filters = ExpenseFilters(cursor="INVALIDCURSOR!!!")
        with pytest.raises(ExpenseServiceError) as exc_info:
            service.list_expenses(user_id=mock_user.id, filters=filters)
        assert "invalid cursor" in str(exc_info.value).lower()
