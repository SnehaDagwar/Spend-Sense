"""Pydantic response schemas for AI Insights & Financial Intelligence endpoints."""

from __future__ import annotations

import datetime
import uuid
from typing import Optional, Literal
from decimal import Decimal
from pydantic import Field

from app.schemas.base import APIModel


class SubscriptionDetection(APIModel):
    merchant: str
    amount: Decimal
    frequency: str = Field(description="Detected frequency, e.g. 'monthly', 'yearly'")
    next_renewal_date: Optional[datetime.date] = None
    confidence_score: float = Field(description="Confidence from 0.0 to 1.0")


class FinancialSummaryInsight(APIModel):
    health_score: int = Field(description="Financial health score from 0 to 100")
    health_summary: str = Field(description="Human-readable brief summary of financial status")
    budget_status: str = Field(description="One of 'on_track', 'at_risk', or 'critical'")
    overspending_alerts: list[str] = Field(default_factory=list)
    savings_opportunities: list[str] = Field(default_factory=list)
    source: str = Field(
        default="ai",
        description="Origin of the insight: 'ai', 'rule_engine', or 'mock'",
    )


class SpendingPatternInsight(APIModel):
    dominant_categories: list[str] = Field(
        default_factory=list, description="Categories where most of the money is going"
    )
    frequent_payment_methods: list[str] = Field(
        default_factory=list, description="Most commonly used payment methods"
    )
    time_of_month_analysis: str = Field(description="Analysis of when spending spikes occur during the month")
    unusual_volume_categories: list[str] = Field(
        default_factory=list, description="Categories with unusually high volume of transactions"
    )
    subscription_detections: list[SubscriptionDetection] = Field(default_factory=list)
    source: str = Field(
        default="ai",
        description="Origin of the insight: 'ai', 'rule_engine', or 'mock'",
    )


class CategoryRecommendation(APIModel):
    category_id: uuid.UUID
    category_name: str
    current_planned: Decimal
    suggested_planned: Decimal
    reason: str


class RecommendationsInsight(APIModel):
    recommended_budgets: list[CategoryRecommendation] = Field(default_factory=list)
    savings_actions: list[str] = Field(default_factory=list)
    goal_milestone_suggestions: list[str] = Field(default_factory=list)
    source: str = Field(
        default="ai",
        description="Origin of the insight: 'ai', 'rule_engine', or 'mock'",
    )


class AnomalyItem(APIModel):
    expense_id: uuid.UUID
    amount: Decimal
    merchant: str
    category: str
    reason: str


class AnomaliesInsight(APIModel):
    anomalies: list[AnomalyItem] = Field(default_factory=list)
    source: str = Field(
        default="ai",
        description="Origin of the insight: 'ai', 'rule_engine', or 'mock'",
    )


class MonthlyReviewInsight(APIModel):
    month: str = Field(description="Target month in YYYY-MM format")
    net_savings: Decimal
    savings_rate: Decimal = Field(description="Savings rate as a percentage")
    top_spend_drivers: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    opportunities_for_next_month: list[str] = Field(default_factory=list)
    source: str = Field(
        default="ai",
        description="Origin of the insight: 'ai', 'rule_engine', or 'mock'",
    )
