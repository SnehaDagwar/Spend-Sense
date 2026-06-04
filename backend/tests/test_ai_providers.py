from __future__ import annotations

import json
from decimal import Decimal
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.insights import (
    FinancialSummaryInsight,
    SpendingPatternInsight,
    RecommendationsInsight,
    AnomaliesInsight,
    MonthlyReviewInsight,
)
from app.services.ai.providers import (
    AIConfigurationError,
    AIProviderError,
    AIRateLimitError,
    AIProviderFactory,
    extract_json,
    MockProvider,
    GeminiProvider,
    OpenAIProvider,
    ClaudeProvider,
)
from app.core.config import settings


# ---------------------------------------------------------------------------
# Test JSON Extraction
# ---------------------------------------------------------------------------

def test_extract_json_plain() -> None:
    raw = '{"healthScore": 85}'
    assert extract_json(raw) == raw


def test_extract_json_markdown() -> None:
    raw = '```json\n{"healthScore": 85}\n```'
    assert extract_json(raw) == '{"healthScore": 85}'


def test_extract_json_conversational() -> None:
    raw = 'Here is the result:\n{"healthScore": 85}\nHope this helps!'
    assert extract_json(raw) == '{"healthScore": 85}'


# ---------------------------------------------------------------------------
# Test Mock Provider
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_mock_provider_generates_correct_models() -> None:
    provider = MockProvider()
    
    summary = await provider.generate_structured_response("sys", "user", FinancialSummaryInsight)
    assert isinstance(summary, FinancialSummaryInsight)
    assert summary.health_score > 0
    assert summary.budget_status in ("on_track", "at_risk", "critical")

    patterns = await provider.generate_structured_response("sys", "user", SpendingPatternInsight)
    assert isinstance(patterns, SpendingPatternInsight)
    assert len(patterns.dominant_categories) > 0
    assert len(patterns.subscription_detections) > 0

    recommendations = await provider.generate_structured_response("sys", "user", RecommendationsInsight)
    assert isinstance(recommendations, RecommendationsInsight)
    assert len(recommendations.savings_actions) > 0

    anomalies = await provider.generate_structured_response("sys", "user", AnomaliesInsight)
    assert isinstance(anomalies, AnomaliesInsight)
    assert len(anomalies.anomalies) > 0

    review = await provider.generate_structured_response("sys", "user", MonthlyReviewInsight)
    assert isinstance(review, MonthlyReviewInsight)
    assert review.savings_rate >= 0.0


# ---------------------------------------------------------------------------
# Test Gemini Provider
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_gemini_provider_success(mock_post: AsyncMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": '{"healthScore": 90, "healthSummary": "Good", "budgetStatus": "on_track", "overspendingAlerts": [], "savingsOpportunities": []}'}]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    provider = GeminiProvider(api_key="test-key", model="gemini-1.5-flash")
    result = await provider.generate_structured_response("system", "user", FinancialSummaryInsight)
    
    assert isinstance(result, FinancialSummaryInsight)
    assert result.health_score == 90
    assert result.budget_status == "on_track"


@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_gemini_provider_rate_limit(mock_post: AsyncMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Quota exceeded"
    mock_post.return_value = mock_response

    provider = GeminiProvider(api_key="test-key", model="gemini-1.5-flash")
    with pytest.raises(AIRateLimitError):
        await provider.generate_structured_response("system", "user", FinancialSummaryInsight)


# ---------------------------------------------------------------------------
# Test OpenAI Provider
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_openai_provider_success(mock_post: AsyncMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"healthScore": 95, "healthSummary": "Excellent", "budgetStatus": "on_track", "overspendingAlerts": [], "savingsOpportunities": []}'
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
    result = await provider.generate_structured_response("system", "user", FinancialSummaryInsight)
    
    assert isinstance(result, FinancialSummaryInsight)
    assert result.health_score == 95


# ---------------------------------------------------------------------------
# Test Claude Provider
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_claude_provider_success(mock_post: AsyncMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [
            {
                "type": "tool_use",
                "name": "format_output",
                "input": {
                    "healthScore": 88,
                    "healthSummary": "Nice",
                    "budgetStatus": "on_track",
                    "overspendingAlerts": [],
                    "savingsOpportunities": []
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    provider = ClaudeProvider(api_key="test-key", model="claude-3-5-haiku-20241022")
    result = await provider.generate_structured_response("system", "user", FinancialSummaryInsight)
    
    assert isinstance(result, FinancialSummaryInsight)
    assert result.health_score == 88


# ---------------------------------------------------------------------------
# Test Provider Factory Configuration
# ---------------------------------------------------------------------------

def test_factory_returns_mock_by_default() -> None:
    with patch.object(settings, "AI_PROVIDER", "mock"):
        provider = AIProviderFactory.get_provider()
        assert isinstance(provider, MockProvider)


def test_factory_raises_config_error_on_missing_key() -> None:
    with patch.object(settings, "AI_PROVIDER", "gemini"):
        with patch.object(settings, "GEMINI_API_KEY", None):
            with pytest.raises(AIConfigurationError):
                AIProviderFactory.get_provider()
