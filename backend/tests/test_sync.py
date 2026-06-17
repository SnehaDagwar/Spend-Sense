import pytest
import uuid
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.category import SpendingCategory
from app.models.expense import Expense
from app.models.budget import MonthlyBudget

class TestSyncEndpoints:
    """Verifies pull and push database sync routes and auth gates."""

    @pytest.fixture(autouse=True)
    def setup_app_override(self, mock_user: User, mock_db: MagicMock) -> None:
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        yield
        app.dependency_overrides.clear()

    @patch("app.services.sync_service.SyncService.pull_changes")
    def test_pull_changes_returns_200(self, mock_pull: MagicMock) -> None:
        mock_pull.return_value = {
            "changes": {
                "expenses": {"created": [], "updated": [], "deleted": []},
                "budgets": {"created": [], "updated": [], "deleted": []},
                "categories": {"created": [], "updated": [], "deleted": []},
                "goals": {"created": [], "updated": [], "deleted": []}
            },
            "timestamp": "2026-06-17T12:00:00Z"
        }
        
        client = TestClient(app)
        response = client.get("/api/v1/sync/pull")
        assert response.status_code == status.HTTP_200_OK
        
        body = response.json()
        assert "changes" in body
        assert "timestamp" in body
        mock_pull.assert_called_once()

    @patch("app.services.sync_service.SyncService.push_changes")
    def test_push_changes_returns_200(self, mock_push: MagicMock) -> None:
        mock_push.return_value = {"status": "success"}
        
        payload = {
            "changes": {
                "expenses": {
                    "created": [],
                    "updated": [],
                    "deleted": []
                }
            },
            "lastPulledAt": "2026-06-17T12:00:00Z"
        }
        
        client = TestClient(app)
        response = client.post("/api/v1/sync/push", json=payload)
        assert response.status_code == status.HTTP_200_OK
        
        body = response.json()
        assert body == {"status": "success"}
        mock_push.assert_called_once()
