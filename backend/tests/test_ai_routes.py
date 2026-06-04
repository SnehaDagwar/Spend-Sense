from __future__ import annotations

import uuid
from decimal import Decimal
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.insights import (
    FinancialSummaryInsight,
    SpendingPatternInsight,
    RecommendationsInsight,
    AnomaliesInsight,
    MonthlyReviewInsight,
)
from app.services.ai.providers import AIRateLimitError, AIProviderError


# ---------------------------------------------------------------------------
# Test Fixtures & Mocks
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_user() -> User:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.display_name = "Test User"
    user.user_type.value = "Professional"
    return user


@pytest.fixture
def mock_db() -> Session:
    return MagicMock(spec=Session)


# ---------------------------------------------------------------------------
# Route Handler / Endpoint Integration Tests
# ---------------------------------------------------------------------------

class TestInsightsEndpoints:
    """Verifies route protection, routing, and error transformations for Insights endpoints."""

    @pytest.fixture(autouse=True)
    def setup_app_override(self, mock_user: User, mock_db: Session) -> None:
        """Override current user and DB dependencies for route testing."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        yield
        app.dependency_overrides.clear()

    @patch("app.services.ai.service.AIService.get_summary_insight")
    def test_get_summary_insight_endpoint(self, mock_service: MagicMock) -> None:
        mock_service.return_value = FinancialSummaryInsight(
            health_score=80,
            health_summary="Great",
            budget_status="on_track",
            overspending_alerts=[],
            savings_opportunities=[]
        )
        client = TestClient(app)

        response = client.get("/api/v1/insights/summary?month=2026-05")
        assert response.status_code == 200
        mock_service.assert_called_once()
        args, kwargs = mock_service.call_args
        assert kwargs["month"] == "2026-05"

    @patch("app.services.ai.service.AIService.get_spending_patterns_insight")
    def test_get_spending_patterns_insight_endpoint(self, mock_service: MagicMock) -> None:
        mock_service.return_value = SpendingPatternInsight(
            dominant_categories=["Rent"],
            frequent_payment_methods=["UPI"],
            time_of_month_analysis="Spike early",
            unusual_volume_categories=[],
            subscription_detections=[]
        )
        client = TestClient(app)

        response = client.get("/api/v1/insights/spending-patterns?month=2026-05")
        assert response.status_code == 200
        mock_service.assert_called_once()

    @patch("app.services.ai.service.AIService.get_recommendations_insight")
    def test_get_recommendations_insight_endpoint(self, mock_service: MagicMock) -> None:
        mock_service.return_value = RecommendationsInsight(
            recommended_budgets=[],
            savings_actions=[],
            goal_milestone_suggestions=[]
        )
        client = TestClient(app)

        response = client.get("/api/v1/insights/recommendations")
        assert response.status_code == 200
        mock_service.assert_called_once()

    @patch("app.services.ai.service.AIService.get_anomalies_insight")
    def test_get_anomalies_insight_endpoint(self, mock_service: MagicMock) -> None:
        mock_service.return_value = AnomaliesInsight(anomalies=[])
        client = TestClient(app)

        response = client.get("/api/v1/insights/anomalies")
        assert response.status_code == 200
        mock_service.assert_called_once()

    @patch("app.services.ai.service.AIService.get_monthly_review_insight")
    def test_get_monthly_review_insight_endpoint(self, mock_service: MagicMock) -> None:
        mock_service.return_value = MonthlyReviewInsight(
            month="2026-05",
            net_savings=Decimal("1000.00"),
            savings_rate=10.0,
            top_spend_drivers=[],
            achievements=[],
            opportunities_for_next_month=[]
        )
        client = TestClient(app)

        response = client.get("/api/v1/insights/monthly-review?month=2026-05")
        assert response.status_code == 200
        mock_service.assert_called_once()

    def test_invalid_month_format_returns_validation_error(self) -> None:
        client = TestClient(app)
        response = client.get("/api/v1/insights/summary?month=invalid-date")
        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "validation_error"

    @patch("app.services.ai.service.AIService.get_summary_insight")
    def test_rate_limit_error_mapping(self, mock_service: MagicMock) -> None:
        mock_service.side_effect = AIRateLimitError("Limit exceeded")
        client = TestClient(app)

        response = client.get("/api/v1/insights/summary")
        assert response.status_code == 429
        body = response.json()
        assert body["error"]["code"] == "rate_limit_error"

    @patch("app.services.ai.service.AIService.get_summary_insight")
    def test_provider_error_mapping(self, mock_service: MagicMock) -> None:
        mock_service.side_effect = AIProviderError("Upstream error")
        client = TestClient(app)

        response = client.get("/api/v1/insights/summary")
        assert response.status_code == 502
        body = response.json()
        assert body["error"]["code"] == "bad_gateway"
