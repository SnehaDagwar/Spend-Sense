from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.budget import MonthlyBudget, BudgetCategoryAllocation
from app.models.category import SpendingCategory
from app.models.goal import SavingsGoal, GoalContribution
from app.schemas.sync import SyncPullResponse, SyncPushRequest
from app.schemas.expense import ExpensePublic
from app.schemas.budget import BudgetPublic
from app.schemas.category import CategoryPublic
from app.schemas.goal import GoalPublic

class SyncService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def pull_changes(self, user_id: uuid.UUID, last_pulled_at: datetime | None) -> Dict[str, Any]:
        """Fetch all database items modified since last_pulled_at, for the given user."""
        now = datetime.now(timezone.utc)
        
        # Base filter clauses
        expense_clause = Expense.user_id == user_id
        budget_clause = MonthlyBudget.user_id == user_id
        category_clause = SpendingCategory.user_id == user_id
        goal_clause = SavingsGoal.user_id == user_id

        if last_pulled_at:
            expense_clause = and_(expense_clause, Expense.updated_at > last_pulled_at)
            budget_clause = and_(budget_clause, MonthlyBudget.updated_at > last_pulled_at)
            category_clause = and_(category_clause, SpendingCategory.updated_at > last_pulled_at)
            goal_clause = and_(goal_clause, SavingsGoal.updated_at > last_pulled_at)

        # Pull modified entities
        expenses = self.db.scalars(select(Expense).where(expense_clause)).all()
        budgets = self.db.scalars(select(MonthlyBudget).where(budget_clause)).all()
        categories = self.db.scalars(select(SpendingCategory).where(category_clause)).all()
        goals = self.db.scalars(select(SavingsGoal).where(goal_clause)).all()

        # Format responses
        # For simplicity in Phase 17, we return created/updated together in changes pull. Deleted are not tracked by tables currently.
        # A robust solution tracking deletion would use an audit log. We'll default to return full entities.
        return {
            "changes": {
                "expenses": {
                    "created": [ExpensePublic.model_validate(e).model_dump(mode="json") for e in expenses],
                    "updated": [],
                    "deleted": []
                },
                "budgets": {
                    "created": [BudgetPublic.model_validate(b).model_dump(mode="json") for b in budgets],
                    "updated": [],
                    "deleted": []
                },
                "categories": {
                    "created": [CategoryPublic.model_validate(c).model_dump(mode="json") for c in categories],
                    "updated": [],
                    "deleted": []
                },
                "goals": {
                    "created": [GoalPublic.model_validate(g).model_dump(mode="json") for g in goals],
                    "updated": [],
                    "deleted": []
                }
            },
            "timestamp": now.isoformat()
        }

    def push_changes(self, user_id: uuid.UUID, request: SyncPushRequest) -> Dict[str, str]:
        """Apply batch inserts, updates, and deletes pushed by the client."""
        changes = request.changes
        
        # 1. Sync Categories
        if "categories" in changes:
            cat_changes = changes["categories"]
            for cat_data in cat_changes.get("created", []):
                cat_id = uuid.UUID(cat_data["id"])
                # Check if it already exists
                existing = self.db.scalar(select(SpendingCategory).where(SpendingCategory.id == cat_id))
                if not existing:
                    new_cat = SpendingCategory(
                        id=cat_id,
                        user_id=user_id,
                        slug=cat_data["slug"],
                        name=cat_data["name"],
                        icon=cat_data["icon"],
                        color=cat_data["color"],
                        display_order=cat_data.get("displayOrder", 10),
                        is_system=False
                    )
                    self.db.add(new_cat)
            
            for cat_data in cat_changes.get("updated", []):
                cat_id = uuid.UUID(cat_data["id"])
                existing = self.db.scalar(select(SpendingCategory).where(SpendingCategory.id == cat_id, SpendingCategory.user_id == user_id))
                if existing:
                    existing.name = cat_data.get("name", existing.name)
                    existing.icon = cat_data.get("icon", existing.icon)
                    existing.color = cat_data.get("color", existing.color)

            for cat_id_str in cat_changes.get("deleted", []):
                cat_id = uuid.UUID(cat_id_str)
                existing = self.db.scalar(select(SpendingCategory).where(SpendingCategory.id == cat_id, SpendingCategory.user_id == user_id))
                if existing:
                    self.db.delete(existing)

        # 2. Sync Budgets
        if "budgets" in changes:
            b_changes = changes["budgets"]
            for b_data in b_changes.get("created", []):
                b_id = uuid.UUID(b_data["id"])
                existing = self.db.scalar(select(MonthlyBudget).where(MonthlyBudget.id == b_id))
                if not existing:
                    new_b = MonthlyBudget(
                        id=b_id,
                        user_id=user_id,
                        month=datetime.strptime(b_data["month"] + "-01", "%Y-%m-%d").date(),
                        income=b_data["income"]
                    )
                    self.db.add(new_b)
                    
                    # Add allocations
                    for alloc in b_data.get("categories", []):
                        new_alloc = BudgetCategoryAllocation(
                            budget_id=b_id,
                            category_id=uuid.UUID(alloc["id"]),
                            planned_amount=alloc["planned"]
                        )
                        self.db.add(new_alloc)

            for b_data in b_changes.get("updated", []):
                b_id = uuid.UUID(b_data["id"])
                existing = self.db.scalar(select(MonthlyBudget).where(MonthlyBudget.id == b_id, MonthlyBudget.user_id == user_id))
                if existing:
                    existing.income = b_data.get("income", existing.income)
                    # Sync allocations
                    if "categories" in b_data:
                        # Clear old allocations and insert new
                        self.db.execute(BudgetCategoryAllocation.__table__.delete().where(BudgetCategoryAllocation.budget_id == b_id))
                        for alloc in b_data["categories"]:
                            new_alloc = BudgetCategoryAllocation(
                                budget_id=b_id,
                                category_id=uuid.UUID(alloc["id"]),
                                planned_amount=alloc["planned"]
                            )
                            self.db.add(new_alloc)

            for b_id_str in b_changes.get("deleted", []):
                b_id = uuid.UUID(b_id_str)
                existing = self.db.scalar(select(MonthlyBudget).where(MonthlyBudget.id == b_id, MonthlyBudget.user_id == user_id))
                if existing:
                    self.db.delete(existing)

        # 3. Sync Expenses
        if "expenses" in changes:
            e_changes = changes["expenses"]
            for e_data in e_changes.get("created", []):
                e_id = uuid.UUID(e_data["id"])
                existing = self.db.scalar(select(Expense).where(Expense.id == e_id))
                if not existing:
                    new_e = Expense(
                        id=e_id,
                        user_id=user_id,
                        category_id=uuid.UUID(e_data["categoryId"]),
                        amount=e_data["amount"],
                        expense_date=datetime.strptime(e_data["date"][:10], "%Y-%m-%d").date(),
                        note=e_data.get("note", ""),
                        payment_method=e_data.get("paymentMethod"),
                        merchant=e_data.get("merchant"),
                        tags=e_data.get("tags", []),
                        currency=e_data.get("currency", "INR"),
                        is_recurring=e_data.get("isRecurring", False)
                    )
                    self.db.add(new_e)

            for e_data in e_changes.get("updated", []):
                e_id = uuid.UUID(e_data["id"])
                existing = self.db.scalar(select(Expense).where(Expense.id == e_id, Expense.user_id == user_id))
                if existing:
                    existing.amount = e_data.get("amount", existing.amount)
                    existing.note = e_data.get("note", existing.note)
                    if "categoryId" in e_data:
                        existing.category_id = uuid.UUID(e_data["categoryId"])
                    if "date" in e_data:
                        existing.expense_date = datetime.strptime(e_data["date"][:10], "%Y-%m-%d").date()

            for e_id_str in e_changes.get("deleted", []):
                e_id = uuid.UUID(e_id_str)
                existing = self.db.scalar(select(Expense).where(Expense.id == e_id, Expense.user_id == user_id))
                if existing:
                    self.db.delete(existing)

        # 4. Sync Goals
        if "goals" in changes:
            g_changes = changes["goals"]
            for g_data in g_changes.get("created", []):
                g_id = uuid.UUID(g_data["id"])
                existing = self.db.scalar(select(SavingsGoal).where(SavingsGoal.id == g_id))
                if not existing:
                    new_g = SavingsGoal(
                        id=g_id,
                        user_id=user_id,
                        name=g_data["name"],
                        icon=g_data["icon"],
                        target_amount=g_data["targetAmount"],
                        current_amount=g_data["currentAmount"],
                        monthly_contribution=g_data["monthlyContribution"],
                        target_date=datetime.strptime(g_data["targetDate"], "%Y-%m-%d").date() if g_data.get("targetDate") else None,
                        color=g_data.get("color")
                    )
                    self.db.add(new_g)
                    
                    # Add contributions
                    for contrib in g_data.get("history", []):
                        new_contrib = GoalContribution(
                            goal_id=g_id,
                            amount=contrib["amount"],
                            contributed_at=datetime.fromisoformat(contrib["date"].replace("Z", "+00:00"))
                        )
                        self.db.add(new_contrib)

            for g_data in g_changes.get("updated", []):
                g_id = uuid.UUID(g_data["id"])
                existing = self.db.scalar(select(SavingsGoal).where(SavingsGoal.id == g_id, SavingsGoal.user_id == user_id))
                if existing:
                    existing.name = g_data.get("name", existing.name)
                    existing.current_amount = g_data.get("currentAmount", existing.current_amount)
                    # Add contributions updates
                    if "history" in g_data:
                        # Re-sync contributions
                        self.db.execute(GoalContribution.__table__.delete().where(GoalContribution.goal_id == g_id))
                        for contrib in g_data["history"]:
                            new_contrib = GoalContribution(
                                goal_id=g_id,
                                amount=contrib["amount"],
                                contributed_at=datetime.fromisoformat(contrib["date"].replace("Z", "+00:00"))
                            )
                            self.db.add(new_contrib)

            for g_id_str in g_changes.get("deleted", []):
                g_id = uuid.UUID(g_id_str)
                existing = self.db.scalar(select(SavingsGoal).where(SavingsGoal.id == g_id, SavingsGoal.user_id == user_id))
                if existing:
                    self.db.delete(existing)

        self.db.commit()
        return {"status": "success"}
