"""AI provider abstraction layer.

Defines the provider interface, concrete implementations for Gemini / OpenAI /
Claude / Mock, a factory, and shared helpers (JSON extraction, burst limiter).
"""

from __future__ import annotations

import abc
import json
import logging
import re
import time
from typing import Any, Type, TypeVar

import httpx
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger("spend_sense.ai_providers")

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class AIError(Exception):
    """Base exception for all AI-related errors."""
    pass


class AIConfigurationError(AIError):
    """Raised when an AI provider is configured but missing credentials."""
    pass


class AIProviderError(AIError):
    """Raised when the LLM provider API returns an error or fails to respond."""
    pass


class AIRateLimitError(AIError):
    """Raised when the LLM provider responds with rate limit status."""
    pass


# ---------------------------------------------------------------------------
# JSON Extractor helper
# ---------------------------------------------------------------------------

def extract_json(text: str) -> str:
    """Extract first JSON object from text, handling markdown fences and filler."""
    text = text.strip()

    # Try markdown json block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Try markdown json block with array
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Find outer curly braces
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1].strip()

    return text


def _validate_response_size(text: str, max_chars: int = 50_000) -> None:
    """Guard against excessively large LLM responses to prevent memory issues."""
    if len(text) > max_chars:
        raise AIProviderError(
            f"LLM response exceeds {max_chars} characters ({len(text)}). "
            "This may indicate a malformed or runaway generation."
        )


# ---------------------------------------------------------------------------
# Burst Rate Limiter (per-user, in-memory)
# ---------------------------------------------------------------------------

_burst_tracker: dict[str, list[float]] = {}


def check_burst_rate_limit(user_key: str) -> None:
    """Enforce per-minute burst limit across all providers.

    Raises AIRateLimitError if the user has exceeded AI_BURST_RATE_LIMIT
    requests in the last 60 seconds.
    """
    now = time.time()
    window = 60.0  # 1 minute
    history = _burst_tracker.get(user_key, [])
    history = [t for t in history if t > now - window]
    _burst_tracker[user_key] = history

    if len(history) >= settings.AI_BURST_RATE_LIMIT:
        raise AIRateLimitError(
            f"Burst rate limit exceeded ({settings.AI_BURST_RATE_LIMIT} requests/minute). "
            "Please wait before requesting another insight."
        )


def record_burst_usage(user_key: str) -> None:
    """Record a successful API call in the burst tracker."""
    history = _burst_tracker.get(user_key, [])
    history.append(time.time())
    _burst_tracker[user_key] = history


# ---------------------------------------------------------------------------
# Provider Interface
# ---------------------------------------------------------------------------

class AIProvider(abc.ABC):
    """Abstract interface for all AI intelligence providers."""

    @abc.abstractmethod
    async def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        """Send prompts to provider and parse the response into the designated model."""
        ...


# ---------------------------------------------------------------------------
# Mock Provider (Local Offline Fallback / Dev Mode)
# ---------------------------------------------------------------------------

class MockProvider(AIProvider):
    """Mock provider for local development, testing, and fallback.

    Generates realistic, structured, mock insights based on the input data shapes.
    """

    async def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        logger.info("Generating mock structured response for: %s", response_model.__name__)

        name = response_model.__name__

        # 1. FinancialSummaryInsight
        if name == "FinancialSummaryInsight":
            data = {
                "healthScore": 76,
                "healthSummary": (
                    "Your finances are in good health, but high discretionary "
                    "shopping this week has slightly increased your budget risk."
                ),
                "budgetStatus": "at_risk",
                "overspendingAlerts": [
                    "You have spent 88% of your planned Shopping budget with 12 days remaining in the month.",
                    "Your dining out expenditures are 15% higher than your daily average for past months.",
                ],
                "savingsOpportunities": [
                    "If you cut back on dining out by 1,500 INR this month, you can hit your Emergency Fund goal 2 weeks early.",
                    "Switching your premium entertainment plans to standard could save you 400 INR monthly.",
                ],
                "source": "mock",
            }
            return response_model.model_validate(data)

        # 2. SpendingPatternInsight
        elif name == "SpendingPatternInsight":
            data = {
                "dominantCategories": ["Rent", "Food", "Shopping"],
                "frequentPaymentMethods": [
                    "UPI (82% of transactions)",
                    "Credit Card (18% of transactions)",
                ],
                "timeOfMonthAnalysis": (
                    "Your spending peaks primarily during the first week of the month "
                    "(due to Rent & Utilities) and on weekends, where leisure spending increases by 35%."
                ),
                "unusualVolumeCategories": ["Food (18 transactions this month, average is 12)"],
                "subscriptionDetections": [
                    {
                        "merchant": "Netflix",
                        "amount": 649.00,
                        "frequency": "monthly",
                        "nextRenewalDate": "2026-06-15",
                        "confidenceScore": 0.95,
                    },
                    {
                        "merchant": "Gym Membership",
                        "amount": 2500.00,
                        "frequency": "monthly",
                        "nextRenewalDate": "2026-06-01",
                        "confidenceScore": 0.90,
                    },
                    {
                        "merchant": "Spotify Premium",
                        "amount": 179.00,
                        "frequency": "monthly",
                        "nextRenewalDate": "2026-06-22",
                        "confidenceScore": 0.98,
                    },
                ],
                "source": "mock",
            }
            return response_model.model_validate(data)

        # 3. RecommendationsInsight
        elif name == "RecommendationsInsight":
            match = re.search(r"category_id=['\"]?([a-fA-F0-9-]{36})['\"]?", user_prompt)
            cat_id = match.group(1) if match else "12345678-1234-1234-1234-1234567890ab"

            data = {
                "recommendedBudgets": [
                    {
                        "categoryId": cat_id,
                        "categoryName": "Food",
                        "currentPlanned": 10000.00,
                        "suggestedPlanned": 8500.00,
                        "reason": (
                            "Based on actual spending trends over the past 3 months, you "
                            "consistently spend around 7,800 INR on food. Reducing your "
                            "planned allocation by 1,500 INR frees up cash for savings."
                        ),
                    }
                ],
                "savingsActions": [
                    "Opt out of secondary subscription services to reclaim 300 INR per month.",
                    "Consolidate shopping deliveries to avoid incremental shipping charges.",
                ],
                "goalMilestoneSuggestions": [
                    "Increase your Emergency Fund contribution by 500 INR this month to maintain your target streak bonus."
                ],
                "source": "mock",
            }
            return response_model.model_validate(data)

        # 4. AnomaliesInsight
        elif name == "AnomaliesInsight":
            match = re.search(r"id=['\"]?([a-fA-F0-9-]{36})['\"]?", user_prompt)
            exp_id = match.group(1) if match else "87654321-4321-4321-4321-210987654321"

            data = {
                "anomalies": [
                    {
                        "expenseId": exp_id,
                        "amount": 4200.00,
                        "merchant": "Amazon",
                        "category": "Shopping",
                        "reason": (
                            "This single purchase of 4,200 INR is 250% higher "
                            "than your median shopping transaction of 1,200 INR."
                        ),
                    },
                    {
                        "expenseId": "99999999-9999-9999-9999-999999999999",
                        "amount": 250.00,
                        "merchant": "Uber",
                        "category": "Transport",
                        "reason": (
                            "Duplicate transaction alert: Two Uber rides of 250 INR "
                            "were recorded within 4 minutes on the same date."
                        ),
                    },
                ],
                "source": "mock",
            }
            return response_model.model_validate(data)

        # 5. MonthlyReviewInsight
        elif name == "MonthlyReviewInsight":
            data = {
                "month": "2026-05",
                "netSavings": 12500.00,
                "savingsRate": 25.0,
                "topSpendDrivers": [
                    "Rent (paid on 1st of month)",
                    "Electronics purchase at Amazon (4,200 INR)",
                ],
                "achievements": [
                    "You achieved a savings rate of 25%, beating your target of 20%!",
                    "Maintained your weekly shopping cap for 4 weeks straight.",
                ],
                "opportunitiesForNextMonth": [
                    "Plan major purchases around salary credit cycles to optimize cash flow.",
                    "Divert 2,000 INR of your food budget surplus directly to your SIP savings goals.",
                ],
                "source": "mock",
            }
            return response_model.model_validate(data)

        # Fallback empty model validation
        return response_model.model_validate({})


# ---------------------------------------------------------------------------
# Gemini Provider
# ---------------------------------------------------------------------------

class GeminiProvider(AIProvider):
    """Gemini API Provider using structured schema matching."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        self.timeout = float(settings.AI_REQUEST_TIMEOUT)

    async def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        # Convert Pydantic schema to JSON schema compatible with Gemini
        schema = response_model.model_json_schema()

        def _clean_schema(s: dict[str, Any]) -> dict[str, Any]:
            """Strip metadata fields Gemini might reject."""
            if not isinstance(s, dict):
                return s
            cleaned = {}
            for k, v in s.items():
                if k in ("title", "description", "default") and isinstance(v, str):
                    continue
                if isinstance(v, dict):
                    cleaned[k] = _clean_schema(v)
                elif isinstance(v, list):
                    cleaned[k] = [
                        _clean_schema(item) if isinstance(item, dict) else item
                        for item in v
                    ]
                else:
                    cleaned[k] = v
            return cleaned

        cleaned_schema = _clean_schema(schema)

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": cleaned_schema,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.endpoint, json=payload)

                if response.status_code == 429:
                    raise AIRateLimitError("Gemini API rate limit exceeded.")
                if response.status_code != 200:
                    raise AIProviderError(
                        f"Gemini API returned status {response.status_code}: {response.text}"
                    )

                res_data = response.json()
                text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                _validate_response_size(text)
                cleaned_text = extract_json(text)

                result = response_model.model_validate_json(cleaned_text)
                # Inject source marker
                if hasattr(result, "source"):
                    object.__setattr__(result, "source", "ai")
                return result
        except httpx.HTTPError as exc:
            raise AIProviderError(f"Gemini API connection error: {exc}") from exc
        except (KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
            raise AIProviderError(f"Failed to parse Gemini response: {exc}") from exc


# ---------------------------------------------------------------------------
# OpenAI Provider
# ---------------------------------------------------------------------------

class OpenAIProvider(AIProvider):
    """OpenAI API Provider using Structured Outputs JSON Schema."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        self.timeout = float(settings.AI_REQUEST_TIMEOUT)

    async def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": settings.AI_MAX_RESPONSE_TOKENS,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": response_model.model_json_schema(),
                    "strict": True,
                },
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)

                if response.status_code == 429:
                    raise AIRateLimitError("OpenAI API rate limit exceeded.")
                if response.status_code != 200:
                    raise AIProviderError(
                        f"OpenAI API returned status {response.status_code}: {response.text}"
                    )

                res_data = response.json()
                text = res_data["choices"][0]["message"]["content"]
                _validate_response_size(text)

                result = response_model.model_validate_json(text)
                if hasattr(result, "source"):
                    object.__setattr__(result, "source", "ai")
                return result
        except httpx.HTTPError as exc:
            raise AIProviderError(f"OpenAI API connection error: {exc}") from exc
        except (KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
            raise AIProviderError(f"Failed to parse OpenAI response: {exc}") from exc


# ---------------------------------------------------------------------------
# Claude Provider (Anthropic)
# ---------------------------------------------------------------------------

class ClaudeProvider(AIProvider):
    """Anthropic Claude API Provider using Tool Choice forcing."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.anthropic.com/v1/messages"
        # Claude tends to be slower; use timeout + 15s headroom
        self.timeout = float(settings.AI_REQUEST_TIMEOUT) + 15.0

    async def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "tools": [
                {
                    "name": "format_output",
                    "description": f"Format output to match {response_model.__name__} schema",
                    "input_schema": response_model.model_json_schema(),
                }
            ],
            "tool_choice": {"type": "tool", "name": "format_output"},
            "max_tokens": settings.AI_MAX_RESPONSE_TOKENS,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)

                if response.status_code == 429:
                    raise AIRateLimitError("Claude API rate limit exceeded.")
                if response.status_code != 200:
                    raise AIProviderError(
                        f"Claude API returned status {response.status_code}: {response.text}"
                    )

                res_data = response.json()

                # Retrieve from tool execution parameters
                input_data = None
                for content_item in res_data.get("content", []):
                    if (
                        content_item.get("type") == "tool_use"
                        and content_item.get("name") == "format_output"
                    ):
                        input_data = content_item.get("input")
                        break

                if input_data is None:
                    raise AIProviderError(
                        "Claude response did not invoke the expected formatting tool."
                    )

                result = response_model.model_validate(input_data)
                if hasattr(result, "source"):
                    object.__setattr__(result, "source", "ai")
                return result
        except httpx.HTTPError as exc:
            raise AIProviderError(f"Claude API connection error: {exc}") from exc
        except (KeyError, IndexError, ValueError) as exc:
            raise AIProviderError(f"Failed to parse Claude response: {exc}") from exc


# ---------------------------------------------------------------------------
# Provider Factory
# ---------------------------------------------------------------------------

class AIProviderFactory:
    """Factory class to construct configured AIProvider client instance."""

    @staticmethod
    def get_provider() -> AIProvider:
        provider_name = settings.AI_PROVIDER.lower().strip()

        if provider_name == "gemini":
            if not settings.GEMINI_API_KEY:
                raise AIConfigurationError("GEMINI_API_KEY is not configured in settings.")
            return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)

        elif provider_name == "openai":
            if not settings.OPENAI_API_KEY:
                raise AIConfigurationError("OPENAI_API_KEY is not configured in settings.")
            return OpenAIProvider(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)

        elif provider_name == "claude":
            if not settings.CLAUDE_API_KEY:
                raise AIConfigurationError("CLAUDE_API_KEY is not configured in settings.")
            return ClaudeProvider(api_key=settings.CLAUDE_API_KEY, model=settings.CLAUDE_MODEL)

        elif provider_name == "mock":
            return MockProvider()

        else:
            raise AIConfigurationError(f"Unsupported AI provider: {settings.AI_PROVIDER}")
