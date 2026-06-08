"""Rule-based fallback intelligence engine.

Generates deterministic financial insights from raw data using statistical
analysis and financial heuristics — no LLM call required.  This module is used:

1. As a **graceful fallback** when the configured AI provider is unavailable.
2. As the **default** when ``AI_PROVIDER=mock`` and the user has real data.
3. As a **baseline** for testing and development.

All public functions accept pre-compiled financial context dicts and return
Pydantic schema instances directly.
"""

from __future__ import annotations

import datetime
import logging
import statistics
import uuid
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.schemas.insights import (
    AnomaliesInsight,
    AnomalyItem,
    CategoryRecommendation,
    FinancialSummaryInsight,
    MonthlyReviewInsight,
    RecommendationsInsight,
    SpendingPatternInsight,
    SubscriptionDetection,
)

logger = logging.getLogger("spend_sense.ai_fallback")

_ZERO = Decimal("0.00")
_HUNDRED = Decimal("100.00")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Return ``numerator / denominator * 100`` rounded to 2dp, or 0 if div-by-zero."""
    if denominator <= 0:
        return _ZERO
    return (numerator / denominator * _HUNDRED).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _round2(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# 1. Financial Summary
# ---------------------------------------------------------------------------

def compute_summary_insight(
    *,
    month: str,
    income: Decimal,
    total_spent: Decimal,
    allocations: list[dict[str, Any]],
    warning_threshold: float = 0.80,
) -> FinancialSummaryInsight:
    """Generate a rule-based financial health summary.

    Parameters
    ----------
    allocations : list of dicts
        Each dict has keys: ``name``, ``planned`` (Decimal), ``spent`` (Decimal).
    """
    # --- health score ---
    # Weighted: 40% budget utilization, 30% savings rate, 30% overspending penalty
    utilization = float(total_spent / income) if income > 0 else 1.0
    savings_rate = max(0.0, 1.0 - utilization)

    overspend_count = sum(
        1 for a in allocations
        if a["planned"] > 0 and a["spent"] > a["planned"]
    )
    overspend_penalty = min(overspend_count * 10, 40)  # max 40pt penalty

    raw_score = (
        max(0, 40 - int(max(0, utilization - 0.5) * 80))  # budget util component
        + int(savings_rate * 30)                            # savings component
        + (30 - overspend_penalty)                          # discipline component
    )
    health_score = max(0, min(100, raw_score))

    # --- budget status ---
    if total_spent > income * Decimal("0.95"):
        budget_status = "critical"
    elif total_spent > income * Decimal(str(warning_threshold)):
        budget_status = "at_risk"
    else:
        budget_status = "on_track"

    # --- overspending alerts ---
    alerts: list[str] = []
    for a in allocations:
        if a["planned"] > 0:
            pct_used = _pct(a["spent"], a["planned"])
            if a["spent"] > a["planned"]:
                alerts.append(
                    f"You have exceeded your {a['name']} budget by "
                    f"{_round2(a['spent'] - a['planned'])} "
                    f"({pct_used}% of planned)."
                )
            elif pct_used >= Decimal(str(warning_threshold * 100)):
                alerts.append(
                    f"You have used {pct_used}% of your {a['name']} budget."
                )

    # --- savings opportunities ---
    opportunities: list[str] = []
    for a in allocations:
        if a["planned"] > 0 and a["spent"] < a["planned"] * Decimal("0.5"):
            surplus = _round2(a["planned"] - a["spent"])
            opportunities.append(
                f"You have {surplus} surplus in {a['name']}. "
                f"Consider reallocating to savings."
            )

    if savings_rate < 0.1 and income > 0:
        opportunities.append(
            f"Your savings rate is only {_round2(Decimal(str(savings_rate * 100)))}%. "
            "Aim for at least 20% by reducing discretionary spending."
        )

    summary_parts = []
    if budget_status == "on_track":
        summary_parts.append(f"Your finances look healthy for {month}.")
    elif budget_status == "at_risk":
        summary_parts.append(f"Your spending is approaching your income limit for {month}.")
    else:
        summary_parts.append(f"Your spending for {month} has nearly consumed your income.")
    if overspend_count:
        summary_parts.append(
            f"{overspend_count} categor{'y is' if overspend_count == 1 else 'ies are'} over budget."
        )

    return FinancialSummaryInsight(
        health_score=health_score,
        health_summary=" ".join(summary_parts),
        budget_status=budget_status,
        overspending_alerts=alerts[:5],
        savings_opportunities=opportunities[:5],
        source="rule_engine",
    )


# ---------------------------------------------------------------------------
# 2. Spending Patterns
# ---------------------------------------------------------------------------

def compute_patterns_insight(
    *,
    month: str,
    total_spent: Decimal,
    category_breakdown: list[dict[str, Any]],
    daily_trends: list[dict[str, Any]],
    payment_methods: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
) -> SpendingPatternInsight:
    """Generate rule-based spending pattern analysis.

    Parameters
    ----------
    category_breakdown : list of dicts with ``name``, ``spent``
    daily_trends : list of dicts with ``date`` (date), ``spent`` (Decimal)
    payment_methods : list of dicts with ``method`` (str), ``count`` (int)
    transactions : list of dicts with ``amount``, ``merchant``, ``category``, ``note``
    """
    # Dominant categories (top 3)
    sorted_cats = sorted(category_breakdown, key=lambda c: c["spent"], reverse=True)
    dominant = [c["name"] for c in sorted_cats[:3]]

    # Frequent payment methods
    total_txn = sum(p["count"] for p in payment_methods) or 1
    freq_methods = [
        f"{p['method']} ({int(p['count'] / total_txn * 100)}% of transactions)"
        for p in sorted(payment_methods, key=lambda p: p["count"], reverse=True)[:3]
    ]

    # Time-of-month analysis
    week_spending: dict[str, Decimal] = defaultdict(lambda: _ZERO)
    for t in daily_trends:
        day = t["date"].day if hasattr(t["date"], "day") else int(str(t["date"]).split("-")[-1])
        if day <= 7:
            week_spending["first week"] += t["spent"]
        elif day <= 14:
            week_spending["second week"] += t["spent"]
        elif day <= 21:
            week_spending["third week"] += t["spent"]
        else:
            week_spending["last week"] += t["spent"]

    if week_spending:
        peak_week = max(week_spending, key=week_spending.get)  # type: ignore[arg-type]
        analysis = f"Your spending peaks during the {peak_week} of the month."
    else:
        analysis = "Not enough daily data to determine spending patterns."

    # Unusual volume categories (>15 transactions in a category)
    cat_counts: Counter[str] = Counter()
    for tx in transactions:
        cat_counts[tx["category"]] += 1
    unusual = [
        f"{cat} ({cnt} transactions)" for cat, cnt in cat_counts.most_common(3) if cnt > 12
    ]

    # Subscription detection (same merchant + similar amount appearing >= 2 times)
    merchant_amounts: dict[str, list[Decimal]] = defaultdict(list)
    for tx in transactions:
        m = (tx.get("merchant") or "").strip()
        if m:
            merchant_amounts[m].append(tx["amount"])

    subs: list[SubscriptionDetection] = []
    for merchant, amounts in merchant_amounts.items():
        if len(amounts) >= 2:
            avg = sum(amounts) / len(amounts)
            # Check if amounts are consistent (within 10% of average)
            if all(abs(a - avg) <= avg * Decimal("0.1") for a in amounts):
                subs.append(
                    SubscriptionDetection(
                        merchant=merchant,
                        amount=_round2(avg),
                        frequency="monthly" if len(amounts) <= 2 else "frequent",
                        next_renewal_date=None,
                        confidence_score=round(min(0.95, 0.5 + len(amounts) * 0.15), 2),
                    )
                )

    return SpendingPatternInsight(
        dominant_categories=dominant,
        frequent_payment_methods=freq_methods,
        time_of_month_analysis=analysis,
        unusual_volume_categories=unusual,
        subscription_detections=subs[:5],
        source="rule_engine",
    )


# ---------------------------------------------------------------------------
# 3. Recommendations
# ---------------------------------------------------------------------------

def compute_recommendations_insight(
    *,
    month: str,
    income: Decimal,
    allocations: list[dict[str, Any]],
    goals: list[dict[str, Any]],
) -> RecommendationsInsight:
    """Generate rule-based budget and savings recommendations.

    Parameters
    ----------
    allocations : list of dicts with ``category_id``, ``name``, ``planned``, ``spent``
    goals : list of dicts with ``name``, ``target``, ``current``, ``monthly_contribution``
    """
    recs: list[CategoryRecommendation] = []
    for a in allocations:
        if a["planned"] > 0:
            utilization = a["spent"] / a["planned"]
            if utilization < Decimal("0.6"):
                # Under-utilized — suggest reducing
                suggested = _round2(a["spent"] * Decimal("1.15"))  # 15% buffer above actual
                suggested = max(suggested, Decimal("100.00"))  # floor
                if suggested < a["planned"]:
                    recs.append(
                        CategoryRecommendation(
                            category_id=a["category_id"],
                            category_name=a["name"],
                            current_planned=a["planned"],
                            suggested_planned=suggested,
                            reason=(
                                f"You typically spend {_round2(a['spent'])} on {a['name']}. "
                                f"Reducing the planned allocation frees up budget for savings."
                            ),
                        )
                    )
            elif utilization > Decimal("1.1"):
                # Over-utilized — suggest increasing
                suggested = _round2(a["spent"] * Decimal("1.10"))
                recs.append(
                    CategoryRecommendation(
                        category_id=a["category_id"],
                        category_name=a["name"],
                        current_planned=a["planned"],
                        suggested_planned=suggested,
                        reason=(
                            f"Your actual spend of {_round2(a['spent'])} exceeds the "
                            f"planned {a['planned']}. Adjusting prevents repeated overruns."
                        ),
                    )
                )

    # Savings actions
    savings_actions: list[str] = []
    total_surplus = sum(
        (a["planned"] - a["spent"])
        for a in allocations
        if a["planned"] > 0 and a["spent"] < a["planned"]
    )
    if total_surplus > 0:
        savings_actions.append(
            f"Redirect your {_round2(total_surplus)} budget surplus to savings goals."
        )

    # Goal milestone suggestions
    goal_suggestions: list[str] = []
    for g in goals:
        remaining = g["target"] - g["current"]
        if remaining > 0 and g["monthly_contribution"] > 0:
            months_left = int(remaining / g["monthly_contribution"]) + 1
            goal_suggestions.append(
                f"At your current contribution rate, you'll reach {g['name']} in "
                f"~{months_left} months. Increasing by 10% could shave off a month."
            )

    return RecommendationsInsight(
        recommended_budgets=recs[:5],
        savings_actions=savings_actions[:3],
        goal_milestone_suggestions=goal_suggestions[:3],
        source="rule_engine",
    )


# ---------------------------------------------------------------------------
# 4. Anomalies
# ---------------------------------------------------------------------------

def compute_anomalies_insight(
    *,
    expenses: list[dict[str, Any]],
    category_budgets: dict[str, Decimal],
) -> AnomaliesInsight:
    """Detect statistical anomalies in expense data.

    Parameters
    ----------
    expenses : list of dicts with ``id``, ``amount``, ``merchant``, ``category``, ``date``, ``note``
    category_budgets : mapping of category name -> planned amount
    """
    anomalies: list[AnomalyItem] = []

    # Group by category for statistical analysis
    cat_amounts: dict[str, list[Decimal]] = defaultdict(list)
    for e in expenses:
        cat_amounts[e["category"]].append(e["amount"])

    # 1. Statistical outliers (> 2 standard deviations from category mean)
    for e in expenses:
        cat = e["category"]
        amounts = cat_amounts.get(cat, [])
        if len(amounts) >= 3:
            float_amounts = [float(a) for a in amounts]
            mean = statistics.mean(float_amounts)
            stdev = statistics.stdev(float_amounts)
            if stdev > 0 and float(e["amount"]) > mean + 2 * stdev:
                anomalies.append(
                    AnomalyItem(
                        expense_id=e["id"],
                        amount=e["amount"],
                        merchant=e.get("merchant") or "Unknown",
                        category=cat,
                        reason=(
                            f"This transaction of {e['amount']} is significantly above "
                            f"the category average of {_round2(Decimal(str(mean)))}."
                        ),
                    )
                )

        # 2. Single expense consuming >50% of category budget
        budget = category_budgets.get(cat, _ZERO)
        if budget > 0 and e["amount"] > budget * Decimal("0.5"):
            # Avoid duplicate with outlier check
            if not any(a.expense_id == e["id"] for a in anomalies):
                anomalies.append(
                    AnomalyItem(
                        expense_id=e["id"],
                        amount=e["amount"],
                        merchant=e.get("merchant") or "Unknown",
                        category=cat,
                        reason=(
                            f"This single expense consumes {_pct(e['amount'], budget)}% "
                            f"of the {cat} monthly budget."
                        ),
                    )
                )

    # 3. Duplicate detection (same amount + merchant + date)
    seen: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for e in expenses:
        key = (str(e["amount"]), e.get("merchant") or "", str(e.get("date", "")))
        seen[key].append(e)

    for key, group in seen.items():
        if len(group) >= 2:
            for dup in group[1:]:
                if not any(a.expense_id == dup["id"] for a in anomalies):
                    anomalies.append(
                        AnomalyItem(
                            expense_id=dup["id"],
                            amount=dup["amount"],
                            merchant=dup.get("merchant") or "Unknown",
                            category=dup["category"],
                            reason=(
                                f"Possible duplicate: same amount ({dup['amount']}), "
                                f"merchant, and date as another transaction."
                            ),
                        )
                    )

    return AnomaliesInsight(
        anomalies=anomalies[:10],
        source="rule_engine",
    )


# ---------------------------------------------------------------------------
# 5. Monthly Review
# ---------------------------------------------------------------------------

def compute_monthly_review_insight(
    *,
    month: str,
    income: Decimal,
    total_spent: Decimal,
    category_spending: list[dict[str, Any]],
    historical: list[dict[str, Any]],
    savings_streak: int,
    goals: list[dict[str, Any]],
) -> MonthlyReviewInsight:
    """Generate a rule-based monthly financial review.

    Parameters
    ----------
    category_spending : list of dicts with ``name``, ``spent``
    historical : list of dicts with ``month``, ``income``, ``spent``, ``savings``
    goals : list of dicts with ``name``, ``target``, ``current``
    """
    net_savings = income - total_spent
    savings_rate = _pct(net_savings, income) if income > 0 else _ZERO

    # Top spend drivers (top 3 categories)
    sorted_cats = sorted(category_spending, key=lambda c: c["spent"], reverse=True)
    top_drivers = [f"{c['name']} ({_round2(c['spent'])})" for c in sorted_cats[:3]]

    # Achievements
    achievements: list[str] = []
    if savings_rate >= 20:
        achievements.append(f"You achieved a savings rate of {savings_rate}%!")
    if savings_streak >= 2:
        achievements.append(f"You maintained a savings streak of {savings_streak} months!")
    for g in goals:
        if g["current"] >= g["target"]:
            achievements.append(f"You completed your '{g['name']}' savings goal!")

    # Opportunities
    opportunities: list[str] = []
    if historical:
        prev_spent = [h["spent"] for h in historical if h["spent"] > 0]
        if prev_spent:
            avg_prev = sum(prev_spent) / len(prev_spent)
            if total_spent > avg_prev:
                delta = _round2(total_spent - avg_prev)
                opportunities.append(
                    f"Your spending increased by {delta} compared to your 3-month average. "
                    f"Review discretionary categories for savings."
                )
    if savings_rate < 20 and income > 0:
        target_savings = _round2(income * Decimal("0.20") - net_savings)
        if target_savings > 0:
            opportunities.append(
                f"Reduce spending by {target_savings} next month to reach a 20% savings rate."
            )

    return MonthlyReviewInsight(
        month=month,
        net_savings=_round2(net_savings),
        savings_rate=_round2(savings_rate),
        top_spend_drivers=top_drivers,
        achievements=achievements[:5],
        opportunities_for_next_month=opportunities[:3],
        source="rule_engine",
    )
