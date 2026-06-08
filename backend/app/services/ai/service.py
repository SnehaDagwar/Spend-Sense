"""AI Insights service — orchestrates data compilation, provider calls,
caching, rate limiting, and graceful fallback to rule-based intelligence.
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import logging
import time
import uuid
from collections import OrderedDict
from decimal import Decimal
from typing import Any, Optional, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.budget import MonthlyBudget
from app.models.category import SpendingCategory
from app.models.expense import Expense
from app.models.goal import SavingsGoal
from app.models.enums import SavingsGoalStatus
from app.models.progress import UserProgress
from app.models.user import User
from app.schemas.insights import (
    FinancialSummaryInsight,
    SpendingPatternInsight,
    RecommendationsInsight,
    AnomaliesInsight,
    MonthlyReviewInsight,
)
from app.services.ai.providers import (
    AIProviderFactory,
    AIRateLimitError,
    AIProviderError,
    AIError,
    check_burst_rate_limit,
    record_burst_usage,
)
from app.services.ai import prompts
from app.services.ai import fallback as fb

logger = logging.getLogger("spend_sense.ai_service")

T = TypeVar("T", bound=Any)

# ---------------------------------------------------------------------------
# Bounded LRU Cache (thread-safe enough for single-worker async)
# ---------------------------------------------------------------------------

_CacheKey = tuple[uuid.UUID, str, str, str]  # (user_id, insight_type, month, state_hash)


class _LRUCache:
    """Simple bounded LRU cache backed by an OrderedDict."""

    def __init__(self, max_size: int, ttl_seconds: int = 3600) -> None:
        self._store: OrderedDict[_CacheKey, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds

    def get(self, key: _CacheKey) -> Optional[Any]:
        if key in self._store:
            value, ts = self._store[key]
            if time.time() - ts < self._ttl:
                self._store.move_to_end(key)
                return value
            del self._store[key]
        return None

    def put(self, key: _CacheKey, value: Any) -> None:
        # Evict old entries for same user+type to prevent stale data
        obsolete = [k for k in self._store if k[0] == key[0] and k[1] == key[1]]
        for k in obsolete:
            del self._store[k]
        self._store[key] = (value, time.time())
        self._store.move_to_end(key)
        # Evict oldest if over capacity
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)


_insights_cache = _LRUCache(
    max_size=settings.AI_CACHE_MAX_SIZE,
    ttl_seconds=3600,
)

# ---------------------------------------------------------------------------
# Daily Rate Limiter (in-memory)
# ---------------------------------------------------------------------------

_rate_limit_tracker: dict[uuid.UUID, list[float]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_month_range(month_str: str) -> tuple[datetime.date, datetime.date]:
    """Return (first_day, last_day) for a YYYY-MM string."""
    year = int(month_str[:4])
    mon = int(month_str[5:7])
    first = datetime.date(year, mon, 1)
    if mon == 12:
        last = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last = datetime.date(year, mon + 1, 1) - datetime.timedelta(days=1)
    return first, last


def _month_last_day(month_start: datetime.date) -> datetime.date:
    """Return the last day of the month given its first day."""
    year, mon = month_start.year, month_start.month
    if mon == 12:
        return datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    return datetime.date(year, mon + 1, 1) - datetime.timedelta(days=1)


# ---------------------------------------------------------------------------
# AI Service Implementation
# ---------------------------------------------------------------------------

class AIService:
    """Service layer coordinating financial intelligence & AI insights.

    Responsibilities:
    - Compile financial data from ORM models
    - Enforce rate limits (daily + burst)
    - Check cache for identical financial states
    - Call the configured AI provider
    - On provider failure, fall back to rule-based intelligence
    - Log timing metrics for observability
    """

    # Maximum retries on transient provider failures
    _MAX_RETRIES = 1
    _RETRY_DELAY = 2.0  # seconds

    def __init__(self, db: Session) -> None:
        self.db = db
        self.provider = AIProviderFactory.get_provider()

    # ------------------------------------------------------------------
    # Rate Limiting
    # ------------------------------------------------------------------

    def _check_rate_limit(self, user_id: uuid.UUID) -> None:
        """Enforce strict daily limits on AI generation requests."""
        now = time.time()
        day_ago = now - 86400

        history = _rate_limit_tracker.get(user_id, [])
        history = [t for t in history if t > day_ago]
        _rate_limit_tracker[user_id] = history

        if len(history) >= settings.AI_DAILY_RATE_LIMIT:
            raise AIRateLimitError(
                "Daily AI request limit reached. Please try again tomorrow."
            )

        # Also enforce burst limit
        check_burst_rate_limit(str(user_id))

    def _record_rate_limit_usage(self, user_id: uuid.UUID) -> None:
        """Log a successful API call in both daily and burst trackers."""
        now = time.time()
        history = _rate_limit_tracker.get(user_id, [])
        history.append(now)
        _rate_limit_tracker[user_id] = history
        record_burst_usage(str(user_id))

    # ------------------------------------------------------------------
    # State Hashing & Cache
    # ------------------------------------------------------------------

    def _compute_state_hash(
        self, user_id: uuid.UUID, start_date: datetime.date, end_date: datetime.date
    ) -> str:
        """SHA256 checksum of user's financial state to skip LLM on unchanged data."""
        res_exp = self.db.execute(
            select(
                func.count(Expense.id).label("count"),
                func.sum(Expense.amount).label("sum"),
                func.max(Expense.updated_at).label("max_updated"),
            ).where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
        ).first()
        exp_count = res_exp.count or 0
        exp_sum = res_exp.sum or Decimal("0.00")
        exp_max_updated = res_exp.max_updated.isoformat() if res_exp.max_updated else "none"

        budget = self.db.execute(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == user_id,
                MonthlyBudget.month == start_date,
            )
        ).scalar()
        budget_income = budget.income if budget else Decimal("0.00")
        budget_max_updated = budget.updated_at.isoformat() if budget else "none"

        hash_str = f"{exp_count}:{exp_sum}:{exp_max_updated}:{budget_income}:{budget_max_updated}"
        return hashlib.sha256(hash_str.encode()).hexdigest()

    def _get_cached(self, user_id: uuid.UUID, insight_type: str, month: str, state_hash: str) -> Optional[Any]:
        key: _CacheKey = (user_id, insight_type, month, state_hash)
        hit = _insights_cache.get(key)
        if hit is not None:
            logger.info("Cache HIT for %s (%s)", insight_type, month)
        return hit

    def _set_cached(self, user_id: uuid.UUID, insight_type: str, month: str, state_hash: str, value: Any) -> None:
        _insights_cache.put((user_id, insight_type, month, state_hash), value)

    # ------------------------------------------------------------------
    # Data Compilers
    # ------------------------------------------------------------------

    def _compile_goals_summary(self, user_id: uuid.UUID) -> str:
        """Format a summary of active goals."""
        goals = self.db.scalars(
            select(SavingsGoal).where(
                SavingsGoal.user_id == user_id,
                SavingsGoal.status == SavingsGoalStatus.ACTIVE,
            )
        ).all()
        if not goals:
            return "No active savings goals."

        lines = [
            f"- Name: {g.name}, Target: {g.target_amount}, Saved: {g.current_amount}, "
            f"Monthly Contribution: {g.monthly_contribution}"
            for g in goals
        ]
        return "\n".join(lines)

    def _compile_goals_list(self, user_id: uuid.UUID) -> list[dict[str, Any]]:
        """Return active goals as dicts for the fallback engine."""
        goals = self.db.scalars(
            select(SavingsGoal).where(
                SavingsGoal.user_id == user_id,
                SavingsGoal.status == SavingsGoalStatus.ACTIVE,
            )
        ).all()
        return [
            {
                "name": g.name,
                "target": g.target_amount,
                "current": g.current_amount,
                "monthly_contribution": g.monthly_contribution,
            }
            for g in goals
        ]

    def _compile_allocations(
        self,
        user_id: uuid.UUID,
        budget: Optional[MonthlyBudget],
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[dict[str, Any]]:
        """Compile category allocation dicts with actual spend for both AI and fallback."""
        if not budget or not budget.category_allocations:
            return []
        result = []
        for alloc in budget.category_allocations:
            spent = self.db.scalar(
                select(func.sum(Expense.amount)).where(
                    Expense.user_id == user_id,
                    Expense.category_id == alloc.category_id,
                    Expense.expense_date >= start_date,
                    Expense.expense_date <= end_date,
                )
            ) or Decimal("0.00")
            result.append({
                "category_id": alloc.category_id,
                "name": alloc.category.name,
                "planned": alloc.planned_amount,
                "spent": spent,
            })
        return result

    # ------------------------------------------------------------------
    # Retry wrapper
    # ------------------------------------------------------------------

    async def _call_provider_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        """Call provider with a single retry on transient failures."""
        last_exc: Exception | None = None
        for attempt in range(1 + self._MAX_RETRIES):
            try:
                return await self.provider.generate_structured_response(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=response_model,
                )
            except AIRateLimitError:
                raise  # Don't retry rate limits
            except (AIProviderError, AIError) as exc:
                last_exc = exc
                if attempt < self._MAX_RETRIES:
                    logger.warning(
                        "Provider attempt %d failed (%s), retrying in %.1fs…",
                        attempt + 1, exc, self._RETRY_DELAY,
                    )
                    await asyncio.sleep(self._RETRY_DELAY)
        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Core Service Methods
    # ------------------------------------------------------------------

    async def get_summary_insight(self, user: User, month: str) -> FinancialSummaryInsight:
        """Fetch general financial summary diagnostics."""
        t0 = time.monotonic()
        start_date, end_date = _get_month_range(month)
        state_hash = self._compute_state_hash(user.id, start_date, end_date)

        cached = self._get_cached(user.id, "summary", month, state_hash)
        if cached:
            return cached

        self._check_rate_limit(user.id)

        # Compile data
        budget = self.db.execute(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == user.id, MonthlyBudget.month == start_date
            )
        ).scalar()

        total_spent = self.db.scalar(
            select(func.sum(Expense.amount)).where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
        ) or Decimal("0.00")

        income = budget.income if budget else (
            user.preferences.default_monthly_income if user.preferences else Decimal("0.00")
        )
        allocations = self._compile_allocations(user.id, budget, start_date, end_date)

        # Top categories
        cat_spends = self.db.execute(
            select(SpendingCategory.name, func.sum(Expense.amount).label("spent"))
            .join(Expense, Expense.category_id == SpendingCategory.id)
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
            .group_by(SpendingCategory.name)
            .order_by(func.sum(Expense.amount).desc())
        ).all()
        top_cat_strs = []
        for name, spent in cat_spends:
            pct = (spent / total_spent * 100) if total_spent > 0 else Decimal("0.0")
            top_cat_strs.append(f"- {name}: {spent} ({pct:.1f}%)")

        # Attempt AI provider call
        try:
            alloc_strs = [
                f"- {a['name']}: Planned={a['planned']}, Spent={a['spent']}" for a in allocations
            ] or ["No category allocations planned."]

            currency = "INR"
            if user.preferences and hasattr(user.preferences.currency, "value"):
                currency = user.preferences.currency.value

            user_prompt = prompts.SUMMARY_USER_PROMPT.format(
                month=month,
                user_type=user.user_type.value if hasattr(user.user_type, "value") else str(user.user_type),
                currency=currency,
                income=income,
                total_planned=sum(a["planned"] for a in allocations) if allocations else 0,
                total_spent=total_spent,
                category_allocations="\n".join(alloc_strs),
                top_categories="\n".join(top_cat_strs) if top_cat_strs else "No expenses recorded.",
                goals_summary=self._compile_goals_summary(user.id),
            )

            response = await self._call_provider_with_retry(
                system_prompt=prompts.SUMMARY_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=FinancialSummaryInsight,
            )

            self._record_rate_limit_usage(user.id)
            self._set_cached(user.id, "summary", month, state_hash, response)
            logger.info("Summary insight generated via AI in %.2fs", time.monotonic() - t0)
            return response

        except AIRateLimitError:
            raise  # Propagate rate limits to the route layer
        except Exception as exc:
            if not settings.AI_FALLBACK_ENABLED:
                raise
            logger.warning("AI provider failed for summary, falling back to rule engine: %s", exc)

        # Fallback
        warning_threshold = 0.80
        if budget and hasattr(budget, "warning_threshold") and budget.warning_threshold:
            warning_threshold = float(budget.warning_threshold)

        response = fb.compute_summary_insight(
            month=month,
            income=income,
            total_spent=total_spent,
            allocations=allocations,
            warning_threshold=warning_threshold,
        )
        self._set_cached(user.id, "summary", month, state_hash, response)
        logger.info("Summary insight generated via FALLBACK in %.2fs", time.monotonic() - t0)
        return response

    async def get_spending_patterns_insight(self, user: User, month: str) -> SpendingPatternInsight:
        """Fetch deep-dive behavioral spending analyses and subscription audits."""
        t0 = time.monotonic()
        start_date, end_date = _get_month_range(month)
        state_hash = self._compute_state_hash(user.id, start_date, end_date)

        cached = self._get_cached(user.id, "patterns", month, state_hash)
        if cached:
            return cached

        self._check_rate_limit(user.id)

        # Compile data
        total_spent = self.db.scalar(
            select(func.sum(Expense.amount)).where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
        ) or Decimal("0.00")

        cat_spends = self.db.execute(
            select(SpendingCategory.name, func.sum(Expense.amount).label("spent"))
            .join(Expense, Expense.category_id == SpendingCategory.id)
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
            .group_by(SpendingCategory.name)
            .order_by(func.sum(Expense.amount).desc())
        ).all()

        trends = self.db.execute(
            select(Expense.expense_date, func.sum(Expense.amount).label("spent"))
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
            .group_by(Expense.expense_date)
            .order_by(Expense.expense_date.asc())
        ).all()

        methods = self.db.execute(
            select(Expense.payment_method, func.count(Expense.id))
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
            .group_by(Expense.payment_method)
        ).all()

        txs = self.db.execute(
            select(Expense.amount, Expense.merchant, SpendingCategory.name, Expense.note)
            .join(SpendingCategory, Expense.category_id == SpendingCategory.id)
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
            .order_by(Expense.expense_date.desc())
            .limit(50)
        ).all()

        try:
            cat_strs = [f"- {name}: {spent}" for name, spent in cat_spends]
            trend_strs = [f"{d}: {spent}" for d, spent in trends]
            method_strs = [
                f"{m.value if hasattr(m, 'value') else m or 'other'}: {cnt}"
                for m, cnt in methods
            ]
            tx_strs = [
                f"Amt: {amt}, Merchant: {m or 'Unknown'}, Cat: {cat_name}, Note: {note or 'none'}"
                for amt, m, cat_name, note in txs
            ]

            user_prompt = prompts.PATTERNS_USER_PROMPT.format(
                month=month,
                total_spent=total_spent,
                category_breakdown="\n".join(cat_strs) if cat_strs else "No category breakdown.",
                daily_trends="\n".join(trend_strs) if trend_strs else "No daily activity.",
                payment_methods=", ".join(method_strs) if method_strs else "None",
                transaction_details="\n".join(tx_strs) if tx_strs else "No transactions recorded.",
            )

            response = await self._call_provider_with_retry(
                system_prompt=prompts.PATTERNS_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=SpendingPatternInsight,
            )

            self._record_rate_limit_usage(user.id)
            self._set_cached(user.id, "patterns", month, state_hash, response)
            logger.info("Patterns insight generated via AI in %.2fs", time.monotonic() - t0)
            return response

        except AIRateLimitError:
            raise
        except Exception as exc:
            if not settings.AI_FALLBACK_ENABLED:
                raise
            logger.warning("AI provider failed for patterns, falling back: %s", exc)

        # Fallback
        response = fb.compute_patterns_insight(
            month=month,
            total_spent=total_spent,
            category_breakdown=[{"name": n, "spent": s} for n, s in cat_spends],
            daily_trends=[{"date": d, "spent": s} for d, s in trends],
            payment_methods=[
                {"method": m.value if hasattr(m, "value") else m or "other", "count": cnt}
                for m, cnt in methods
            ],
            transactions=[
                {"amount": amt, "merchant": m or "Unknown", "category": cat, "note": note or ""}
                for amt, m, cat, note in txs
            ],
        )
        self._set_cached(user.id, "patterns", month, state_hash, response)
        logger.info("Patterns insight generated via FALLBACK in %.2fs", time.monotonic() - t0)
        return response

    async def get_recommendations_insight(self, user: User, month: str) -> RecommendationsInsight:
        """Fetch targeted recommendations for budget settings and savings targets."""
        t0 = time.monotonic()
        start_date, end_date = _get_month_range(month)
        state_hash = self._compute_state_hash(user.id, start_date, end_date)

        cached = self._get_cached(user.id, "recommendations", month, state_hash)
        if cached:
            return cached

        self._check_rate_limit(user.id)

        budget = self.db.execute(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == user.id, MonthlyBudget.month == start_date
            )
        ).scalar()
        income = budget.income if budget else (
            user.preferences.default_monthly_income if user.preferences else Decimal("0.00")
        )
        allocations = self._compile_allocations(user.id, budget, start_date, end_date)

        try:
            perf_strs = [
                f"Category UUID: {a['category_id']}, Name: {a['name']}, "
                f"Planned: {a['planned']}, Spent: {a['spent']}"
                for a in allocations
            ] or ["No budgets configured for this month."]

            user_prompt = prompts.RECOMMENDATIONS_USER_PROMPT.format(
                month=month,
                income=income,
                category_performance="\n".join(perf_strs),
                goals_summary=self._compile_goals_summary(user.id),
            )

            response = await self._call_provider_with_retry(
                system_prompt=prompts.RECOMMENDATIONS_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=RecommendationsInsight,
            )

            self._record_rate_limit_usage(user.id)
            self._set_cached(user.id, "recommendations", month, state_hash, response)
            logger.info("Recommendations insight generated via AI in %.2fs", time.monotonic() - t0)
            return response

        except AIRateLimitError:
            raise
        except Exception as exc:
            if not settings.AI_FALLBACK_ENABLED:
                raise
            logger.warning("AI provider failed for recommendations, falling back: %s", exc)

        response = fb.compute_recommendations_insight(
            month=month,
            income=income,
            allocations=allocations,
            goals=self._compile_goals_list(user.id),
        )
        self._set_cached(user.id, "recommendations", month, state_hash, response)
        logger.info("Recommendations insight generated via FALLBACK in %.2fs", time.monotonic() - t0)
        return response

    async def get_anomalies_insight(self, user: User, month: str) -> AnomaliesInsight:
        """Fetch security/risk audit for duplicate transactions or massive spikes."""
        t0 = time.monotonic()
        start_date, end_date = _get_month_range(month)
        state_hash = self._compute_state_hash(user.id, start_date, end_date)

        cached = self._get_cached(user.id, "anomalies", month, state_hash)
        if cached:
            return cached

        self._check_rate_limit(user.id)

        budget = self.db.execute(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == user.id, MonthlyBudget.month == start_date
            )
        ).scalar()

        bud_map: dict[str, Decimal] = {}
        if budget and budget.category_allocations:
            for alloc in budget.category_allocations:
                bud_map[alloc.category.name] = alloc.planned_amount

        bud_strs = [
            f"- Category: {name}, Planned Budget: {amt}" for name, amt in bud_map.items()
        ] or ["No planned budget allocations."]

        expenses_raw = self.db.execute(
            select(
                Expense.id, Expense.amount, Expense.merchant,
                SpendingCategory.name, Expense.expense_date, Expense.note,
            )
            .join(SpendingCategory, Expense.category_id == SpendingCategory.id)
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
            .order_by(Expense.expense_date.desc())
            .limit(50)
        ).all()

        expenses_dicts = [
            {
                "id": eid,
                "amount": amt,
                "merchant": m or "Unknown",
                "category": cat_name,
                "date": dt,
                "note": note or "",
            }
            for eid, amt, m, cat_name, dt, note in expenses_raw
        ]

        try:
            exp_strs = [
                f"ID: {e['id']}, Amt: {e['amount']}, Merchant: {e['merchant']}, "
                f"Cat: {e['category']}, Date: {e['date'].isoformat() if hasattr(e['date'], 'isoformat') else e['date']}, "
                f"Note: {e['note']}"
                for e in expenses_dicts
            ]

            user_prompt = prompts.ANOMALIES_USER_PROMPT.format(
                category_budgets="\n".join(bud_strs),
                expense_list="\n".join(exp_strs) if exp_strs else "No recent expenses recorded.",
            )

            response = await self._call_provider_with_retry(
                system_prompt=prompts.ANOMALIES_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=AnomaliesInsight,
            )

            self._record_rate_limit_usage(user.id)
            self._set_cached(user.id, "anomalies", month, state_hash, response)
            logger.info("Anomalies insight generated via AI in %.2fs", time.monotonic() - t0)
            return response

        except AIRateLimitError:
            raise
        except Exception as exc:
            if not settings.AI_FALLBACK_ENABLED:
                raise
            logger.warning("AI provider failed for anomalies, falling back: %s", exc)

        response = fb.compute_anomalies_insight(
            expenses=expenses_dicts,
            category_budgets=bud_map,
        )
        self._set_cached(user.id, "anomalies", month, state_hash, response)
        logger.info("Anomalies insight generated via FALLBACK in %.2fs", time.monotonic() - t0)
        return response

    async def get_monthly_review_insight(self, user: User, month: str) -> MonthlyReviewInsight:
        """Fetch historical performance, saving targets, and milestones."""
        t0 = time.monotonic()
        start_date, end_date = _get_month_range(month)
        state_hash = self._compute_state_hash(user.id, start_date, end_date)

        cached = self._get_cached(user.id, "review", month, state_hash)
        if cached:
            return cached

        self._check_rate_limit(user.id)

        budget = self.db.execute(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == user.id, MonthlyBudget.month == start_date
            )
        ).scalar()
        income = budget.income if budget else (
            user.preferences.default_monthly_income if user.preferences else Decimal("0.00")
        )

        total_spent = self.db.scalar(
            select(func.sum(Expense.amount)).where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
        ) or Decimal("0.00")

        net_savings = income - total_spent
        savings_rate = (net_savings / income * 100) if income > 0 else Decimal("0.0")

        cat_spends = self.db.execute(
            select(SpendingCategory.name, func.sum(Expense.amount).label("spent"))
            .join(Expense, Expense.category_id == SpendingCategory.id)
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date,
            )
            .group_by(SpendingCategory.name)
            .order_by(func.sum(Expense.amount).desc())
        ).all()

        # Historical comparison (past 3 months)
        historical: list[dict[str, Any]] = []
        for i in range(1, 4):
            y = start_date.year
            m = start_date.month - i
            while m <= 0:
                m += 12
                y -= 1
            m_start = datetime.date(y, m, 1)
            m_end = _month_last_day(m_start)
            m_str = m_start.strftime("%Y-%m")

            m_spent = self.db.scalar(
                select(func.sum(Expense.amount)).where(
                    Expense.user_id == user.id,
                    Expense.expense_date >= m_start,
                    Expense.expense_date <= m_end,
                )
            ) or Decimal("0.00")

            m_budget = self.db.execute(
                select(MonthlyBudget).where(
                    MonthlyBudget.user_id == user.id, MonthlyBudget.month == m_start
                )
            ).scalar()
            m_income = m_budget.income if m_budget else Decimal("0.00")
            m_savings = m_income - m_spent
            historical.append({
                "month": m_str, "income": m_income, "spent": m_spent, "savings": m_savings,
            })

        progress = self.db.execute(
            select(UserProgress).where(UserProgress.user_id == user.id)
        ).scalar()
        streak = progress.savings_streak if progress else 0

        try:
            cat_strs = [f"- {name}: Spent={spent}" for name, spent in cat_spends]
            comp_strs = [
                f"- Month: {h['month']}, Income: {h['income']}, Spent: {h['spent']}, Savings: {h['savings']}"
                for h in historical
            ]
            goals_data = self._compile_goals_summary(user.id)

            user_prompt = prompts.MONTHLY_REVIEW_USER_PROMPT.format(
                month=month,
                income=income,
                total_spent=total_spent,
                net_savings=net_savings,
                savings_rate=savings_rate,
                category_spending="\n".join(cat_strs) if cat_strs else "No category expenses.",
                comparison_data="\n".join(comp_strs) if comp_strs else "No prior history.",
                goals_and_streaks=f"Savings Streak: {streak} months\nGoals Status:\n{goals_data}",
            )

            response = await self._call_provider_with_retry(
                system_prompt=prompts.MONTHLY_REVIEW_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=MonthlyReviewInsight,
            )

            self._record_rate_limit_usage(user.id)
            self._set_cached(user.id, "review", month, state_hash, response)
            logger.info("Review insight generated via AI in %.2fs", time.monotonic() - t0)
            return response

        except AIRateLimitError:
            raise
        except Exception as exc:
            if not settings.AI_FALLBACK_ENABLED:
                raise
            logger.warning("AI provider failed for monthly review, falling back: %s", exc)

        response = fb.compute_monthly_review_insight(
            month=month,
            income=income,
            total_spent=total_spent,
            category_spending=[{"name": n, "spent": s} for n, s in cat_spends],
            historical=historical,
            savings_streak=streak,
            goals=self._compile_goals_list(user.id),
        )
        self._set_cached(user.id, "review", month, state_hash, response)
        logger.info("Review insight generated via FALLBACK in %.2fs", time.monotonic() - t0)
        return response
