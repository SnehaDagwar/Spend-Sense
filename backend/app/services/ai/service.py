from __future__ import annotations

import datetime
import hashlib
import logging
import time
import uuid
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
from app.services.ai.providers import AIProviderFactory, AIRateLimitError, AIError
from app.services.ai import prompts

logger = logging.getLogger("spend_sense.ai_service")

T = TypeVar("T", bound=Any)

# ---------------------------------------------------------------------------
# Global In-Memory Cache and Rate Limiter Storage
# ---------------------------------------------------------------------------
_insights_cache: dict[tuple[uuid.UUID, str, str, str], tuple[Any, float]] = {}
_rate_limit_tracker: dict[uuid.UUID, list[float]] = {}


def _get_month_range(month_str: str) -> tuple[datetime.date, datetime.date]:
    """Helper to return (first_day, last_day) for a YYYY-MM string."""
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
    """Service layer coordinating financial intelligence & AI insights."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.provider = AIProviderFactory.get_provider()

    # ---------------------------------------------------------------------------
    # Rate Limiting & Caching Helpers
    # ---------------------------------------------------------------------------

    def _check_rate_limit(self, user_id: uuid.UUID) -> None:
        """Enforce strict daily limits on AI generation requests."""
        now = time.time()
        day_ago = now - 86400
        
        # Filter request history to past 24h
        history = _rate_limit_tracker.get(user_id, [])
        history = [t for t in history if t > day_ago]
        _rate_limit_tracker[user_id] = history
        
        if len(history) >= settings.AI_DAILY_RATE_LIMIT:
            raise AIRateLimitError("Daily AI request limit reached. Please try again tomorrow.")

    def _record_rate_limit_usage(self, user_id: uuid.UUID) -> None:
        """Log a successful API call in the rate limiter history."""
        now = time.time()
        history = _rate_limit_tracker.get(user_id, [])
        history.append(now)
        _rate_limit_tracker[user_id] = history

    def _compute_state_hash(self, user_id: uuid.UUID, start_date: datetime.date, end_date: datetime.date) -> str:
        """Compute SHA256 checksum of user's financial state to bypass LLM on unchanged data."""
        # 1. Gather actual expense summary
        res_exp = self.db.execute(
            select(
                func.count(Expense.id).label("count"),
                func.sum(Expense.amount).label("sum"),
                func.max(Expense.updated_at).label("max_updated")
            ).where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
        ).first()
        exp_count = res_exp.count or 0
        exp_sum = res_exp.sum or Decimal("0.00")
        exp_max_updated = res_exp.max_updated.isoformat() if res_exp.max_updated else "none"

        # 2. Gather budget details
        budget = self.db.execute(
            select(MonthlyBudget)
            .where(
                MonthlyBudget.user_id == user_id,
                MonthlyBudget.month == start_date
            )
        ).scalar()
        budget_income = budget.income if budget else Decimal("0.00")
        budget_max_updated = budget.updated_at.isoformat() if budget else "none"

        # 3. Create state key
        hash_str = f"{exp_count}:{exp_sum}:{exp_max_updated}:{budget_income}:{budget_max_updated}"
        return hashlib.sha256(hash_str.encode()).hexdigest()

    def _get_cached_insight(self, user_id: uuid.UUID, insight_type: str, month: str, state_hash: str) -> Optional[Any]:
        """Fetch cached response model if cache hit and within 1h TTL."""
        key = (user_id, insight_type, month, state_hash)
        if key in _insights_cache:
            value, timestamp = _insights_cache[key]
            if time.time() - timestamp < 3600:
                logger.info(f"Cache hit for {insight_type} ({month})")
                return value
            else:
                del _insights_cache[key]
        return None

    def _set_cached_insight(self, user_id: uuid.UUID, insight_type: str, month: str, state_hash: str, value: Any) -> None:
        """Cache response model and remove obsolete cached entries for same user/type."""
        obsolete_keys = [k for k in _insights_cache.keys() if k[0] == user_id and k[1] == insight_type]
        for k in obsolete_keys:
            del _insights_cache[k]
        _insights_cache[(user_id, insight_type, month, state_hash)] = (value, time.time())

    # ---------------------------------------------------------------------------
    # Data Compilers
    # ---------------------------------------------------------------------------

    def _compile_goals_summary(self, user_id: uuid.UUID) -> str:
        """Format a summary of active goals."""
        goals = self.db.scalars(
            select(SavingsGoal)
            .where(SavingsGoal.user_id == user_id, SavingsGoal.status == SavingsGoalStatus.ACTIVE)
        ).all()
        if not goals:
            return "No active savings goals."
        
        goal_strs = []
        for g in goals:
            goal_strs.append(
                f"- Name: {g.name}, Target: {g.target_amount}, Saved: {g.current_amount}, "
                f"Monthly Contribution: {g.monthly_contribution}"
            )
        return "\n".join(goal_strs)

    # ---------------------------------------------------------------------------
    # Core Service Methods
    # ---------------------------------------------------------------------------

    async def get_summary_insight(self, user: User, month: str) -> FinancialSummaryInsight:
        """Fetch general financial summary diagnostics."""
        start_date, end_date = _get_month_range(month)
        state_hash = self._compute_state_hash(user.id, start_date, end_date)
        
        cached = self._get_cached_insight(user.id, "summary", month, state_hash)
        if cached:
            return cached

        self._check_rate_limit(user.id)

        # 1. Fetch values
        budget = self.db.execute(
            select(MonthlyBudget)
            .where(MonthlyBudget.user_id == user.id, MonthlyBudget.month == start_date)
        ).scalar()

        total_spent = self.db.scalar(
            select(func.sum(Expense.amount))
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
        ) or Decimal("0.00")

        # 2. Format category allocations
        alloc_strs = []
        if budget and budget.category_allocations:
            for alloc in budget.category_allocations:
                spent = self.db.scalar(
                    select(func.sum(Expense.amount))
                    .where(
                        Expense.user_id == user.id,
                        Expense.category_id == alloc.category_id,
                        Expense.expense_date >= start_date,
                        Expense.expense_date <= end_date
                    )
                ) or Decimal("0.00")
                alloc_strs.append(f"- {alloc.category.name}: Planned={alloc.planned_amount}, Spent={spent}")
        else:
            alloc_strs.append("No category allocations planned.")

        # 3. Format top categories
        cat_spends = self.db.execute(
            select(SpendingCategory.name, func.sum(Expense.amount).label("spent"))
            .join(Expense, Expense.category_id == SpendingCategory.id)
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
            .group_by(SpendingCategory.name)
            .order_by(func.sum(Expense.amount).desc())
        ).all()
        top_cat_strs = []
        for name, spent in cat_spends:
            pct = (spent / total_spent * 100) if total_spent > 0 else Decimal("0.0")
            top_cat_strs.append(f"- {name}: {spent} ({pct:.1f}%)")

        # Compile prompts
        user_prompt = prompts.SUMMARY_USER_PROMPT.format(
            month=month,
            user_type=user.user_type.value if hasattr(user.user_type, "value") else str(user.user_type),
            currency=user.preferences.currency.value if user.preferences and hasattr(user.preferences.currency, "value") else "INR",
            income=budget.income if budget else (user.preferences.default_monthly_income if user.preferences else 0),
            total_planned=sum(a.planned_amount for a in budget.category_allocations) if budget else 0,
            total_spent=total_spent,
            category_allocations="\n".join(alloc_strs),
            top_categories="\n".join(top_cat_strs) if top_cat_strs else "No expenses recorded.",
            goals_summary=self._compile_goals_summary(user.id)
        )

        response = await self.provider.generate_structured_response(
            system_prompt=prompts.SUMMARY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=FinancialSummaryInsight
        )

        self._record_rate_limit_usage(user.id)
        self._set_cached_insight(user.id, "summary", month, state_hash, response)
        return response

    async def get_spending_patterns_insight(self, user: User, month: str) -> SpendingPatternInsight:
        """Fetch deep-dive behavioral spending analyses and subscription audits."""
        start_date, end_date = _get_month_range(month)
        state_hash = self._compute_state_hash(user.id, start_date, end_date)
        
        cached = self._get_cached_insight(user.id, "patterns", month, state_hash)
        if cached:
            return cached

        self._check_rate_limit(user.id)

        # 1. Fetch values
        total_spent = self.db.scalar(
            select(func.sum(Expense.amount))
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
        ) or Decimal("0.00")

        # 2. Category breakdown
        cat_spends = self.db.execute(
            select(SpendingCategory.name, func.sum(Expense.amount).label("spent"))
            .join(Expense, Expense.category_id == SpendingCategory.id)
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
            .group_by(SpendingCategory.name)
            .order_by(func.sum(Expense.amount).desc())
        ).all()
        cat_strs = [f"- {name}: {spent}" for name, spent in cat_spends]

        # 3. Daily trend
        trends = self.db.execute(
            select(Expense.expense_date, func.sum(Expense.amount).label("spent"))
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
            .group_by(Expense.expense_date)
            .order_by(Expense.expense_date.asc())
        ).all()
        trend_strs = [f"{d}: {spent}" for d, spent in trends]

        # 4. Payment methods
        methods = self.db.execute(
            select(Expense.payment_method, func.count(Expense.id))
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
            .group_by(Expense.payment_method)
        ).all()
        method_strs = [f"{m.value if hasattr(m, 'value') else m or 'other'}: {cnt}" for m, cnt in methods]

        # 5. Transactions (obfuscated & limited)
        txs = self.db.execute(
            select(Expense.amount, Expense.merchant, SpendingCategory.name, Expense.note)
            .join(SpendingCategory, Expense.category_id == SpendingCategory.id)
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
            .order_by(Expense.expense_date.desc())
            .limit(50)
        ).all()
        tx_strs = [f"Amt: {amt}, Merchant: {m or 'Unknown'}, Cat: {cat_name}, Note: {note or 'none'}" for amt, m, cat_name, note in txs]

        user_prompt = prompts.PATTERNS_USER_PROMPT.format(
            month=month,
            total_spent=total_spent,
            category_breakdown="\n".join(cat_strs) if cat_strs else "No category breakdown.",
            daily_trends="\n".join(trend_strs) if trend_strs else "No daily activity.",
            payment_methods=", ".join(method_strs) if method_strs else "None",
            transaction_details="\n".join(tx_strs) if tx_strs else "No transactions recorded."
        )

        response = await self.provider.generate_structured_response(
            system_prompt=prompts.PATTERNS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=SpendingPatternInsight
        )

        self._record_rate_limit_usage(user.id)
        self._set_cached_insight(user.id, "patterns", month, state_hash, response)
        return response

    async def get_recommendations_insight(self, user: User, month: str) -> RecommendationsInsight:
        """Fetch targeted recommendations for budget settings and savings targets."""
        start_date, end_date = _get_month_range(month)
        state_hash = self._compute_state_hash(user.id, start_date, end_date)
        
        cached = self._get_cached_insight(user.id, "recommendations", month, state_hash)
        if cached:
            return cached

        self._check_rate_limit(user.id)

        # 1. Fetch values
        budget = self.db.execute(
            select(MonthlyBudget)
            .where(MonthlyBudget.user_id == user.id, MonthlyBudget.month == start_date)
        ).scalar()

        # 2. Category planned vs actual performance
        perf_strs = []
        if budget and budget.category_allocations:
            for alloc in budget.category_allocations:
                spent = self.db.scalar(
                    select(func.sum(Expense.amount))
                    .where(
                        Expense.user_id == user.id,
                        Expense.category_id == alloc.category_id,
                        Expense.expense_date >= start_date,
                        Expense.expense_date <= end_date
                    )
                ) or Decimal("0.00")
                # Expose Category UUID so the LLM can recommend budget edits directly referencing it
                perf_strs.append(f"Category UUID: {alloc.category_id}, Name: {alloc.category.name}, Planned: {alloc.planned_amount}, Spent: {spent}")
        else:
            perf_strs.append("No budgets configured for this month.")

        user_prompt = prompts.RECOMMENDATIONS_USER_PROMPT.format(
            month=month,
            income=budget.income if budget else (user.preferences.default_monthly_income if user.preferences else 0),
            category_performance="\n".join(perf_strs),
            goals_summary=self._compile_goals_summary(user.id)
        )

        response = await self.provider.generate_structured_response(
            system_prompt=prompts.RECOMMENDATIONS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=RecommendationsInsight
        )

        self._record_rate_limit_usage(user.id)
        self._set_cached_insight(user.id, "recommendations", month, state_hash, response)
        return response

    async def get_anomalies_insight(self, user: User, month: str) -> AnomaliesInsight:
        """Fetch security/risk audit for duplicate transactions or massive spending spikes."""
        start_date, end_date = _get_month_range(month)
        state_hash = self._compute_state_hash(user.id, start_date, end_date)
        
        cached = self._get_cached_insight(user.id, "anomalies", month, state_hash)
        if cached:
            return cached

        self._check_rate_limit(user.id)

        # 1. Fetch values
        budget = self.db.execute(
            select(MonthlyBudget)
            .where(MonthlyBudget.user_id == user.id, MonthlyBudget.month == start_date)
        ).scalar()

        # Category budgets
        bud_strs = []
        if budget and budget.category_allocations:
            for alloc in budget.category_allocations:
                bud_strs.append(f"- Category: {alloc.category.name}, Planned Budget: {alloc.planned_amount}")
        else:
            bud_strs.append("No planned budget allocations.")

        # 2. Get transaction list
        expenses = self.db.execute(
            select(Expense.id, Expense.amount, Expense.merchant, SpendingCategory.name, Expense.expense_date, Expense.note)
            .join(SpendingCategory, Expense.category_id == SpendingCategory.id)
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
            .order_by(Expense.expense_date.desc())
            .limit(50)
        ).all()
        exp_strs = [
            f"ID: {eid}, Amt: {amt}, Merchant: {m or 'Unknown'}, Cat: {cat_name}, Date: {dt.isoformat()}, Note: {note or 'none'}" 
            for eid, amt, m, cat_name, dt, note in expenses
        ]

        user_prompt = prompts.ANOMALIES_USER_PROMPT.format(
            category_budgets="\n".join(bud_strs),
            expense_list="\n".join(exp_strs) if exp_strs else "No recent expenses recorded."
        )

        response = await self.provider.generate_structured_response(
            system_prompt=prompts.ANOMALIES_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=AnomaliesInsight
        )

        self._record_rate_limit_usage(user.id)
        self._set_cached_insight(user.id, "anomalies", month, state_hash, response)
        return response

    async def get_monthly_review_insight(self, user: User, month: str) -> MonthlyReviewInsight:
        """Fetch historical performance, saving targets achievement summaries, and milestones."""
        start_date, end_date = _get_month_range(month)
        state_hash = self._compute_state_hash(user.id, start_date, end_date)
        
        cached = self._get_cached_insight(user.id, "review", month, state_hash)
        if cached:
            return cached

        self._check_rate_limit(user.id)

        # 1. Fetch values
        budget = self.db.execute(
            select(MonthlyBudget)
            .where(MonthlyBudget.user_id == user.id, MonthlyBudget.month == start_date)
        ).scalar()
        income = budget.income if budget else (user.preferences.default_monthly_income if user.preferences else Decimal("0.00"))

        total_spent = self.db.scalar(
            select(func.sum(Expense.amount))
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
        ) or Decimal("0.00")

        net_savings = income - total_spent
        savings_rate = (net_savings / income * 100) if income > 0 else Decimal("0.0")

        # Category allocations actual spent
        cat_spends = self.db.execute(
            select(SpendingCategory.name, func.sum(Expense.amount).label("spent"))
            .join(Expense, Expense.category_id == SpendingCategory.id)
            .where(
                Expense.user_id == user.id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
            .group_by(SpendingCategory.name)
            .order_by(func.sum(Expense.amount).desc())
        ).all()
        cat_strs = [f"- {name}: Spent={spent}" for name, spent in cat_spends]

        # 2. Historical comparison (past 3 months)
        comp_strs = []
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
                select(func.sum(Expense.amount))
                .where(
                    Expense.user_id == user.id,
                    Expense.expense_date >= m_start,
                    Expense.expense_date <= m_end
                )
            ) or Decimal("0.00")
            
            m_budget = self.db.execute(
                select(MonthlyBudget).where(MonthlyBudget.user_id == user.id, MonthlyBudget.month == m_start)
            ).scalar()
            m_income = m_budget.income if m_budget else Decimal("0.00")
            m_savings = m_income - m_spent
            comp_strs.append(f"- Month: {m_str}, Income: {m_income}, Spent: {m_spent}, Savings: {m_savings}")

        # 3. Active goals and streak milestones
        goals_data = self._compile_goals_summary(user.id)
        progress = self.db.execute(
            select(UserProgress).where(UserProgress.user_id == user.id)
        ).scalar()
        streak = progress.savings_streak if progress else 0

        user_prompt = prompts.MONTHLY_REVIEW_USER_PROMPT.format(
            month=month,
            income=income,
            total_spent=total_spent,
            net_savings=net_savings,
            savings_rate=savings_rate,
            category_spending="\n".join(cat_strs) if cat_strs else "No category expenses.",
            comparison_data="\n".join(comp_strs) if comp_strs else "No prior history.",
            goals_and_streaks=f"Savings Streak: {streak} months\nGoals Status:\n{goals_data}"
        )

        response = await self.provider.generate_structured_response(
            system_prompt=prompts.MONTHLY_REVIEW_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=MonthlyReviewInsight
        )

        self._record_rate_limit_usage(user.id)
        self._set_cached_insight(user.id, "review", month, state_hash, response)
        return response
