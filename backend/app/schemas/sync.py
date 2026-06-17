from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.expense import ExpensePublic
from app.schemas.budget import BudgetPublic
from app.schemas.category import CategoryPublic
from app.schemas.goal import GoalPublic

class SyncDatabaseChanges(BaseModel):
    expenses: Optional[Dict[str, List[Any]]] = Field(
        None, 
        description="Dictionary representing expenses changes: {'created': [], 'updated': [], 'deleted': []}"
    )
    budgets: Optional[Dict[str, List[Any]]] = Field(
        None,
        description="Dictionary representing monthly budgets changes"
    )
    categories: Optional[Dict[str, List[Any]]] = Field(
        None,
        description="Dictionary representing categories changes"
    )
    goals: Optional[Dict[str, List[Any]]] = Field(
        None,
        description="Dictionary representing savings goals changes"
    )

class SyncPullResponse(BaseModel):
    changes: Dict[str, Dict[str, List[Any]]] = Field(
        ...,
        description="All changes (created, updated, deleted) since the requested timestamp, grouped by table"
    )
    timestamp: datetime = Field(
        ...,
        description="Current server timestamp to use as last_pulled_at for the next pull request"
    )

class SyncPushRequest(BaseModel):
    changes: Dict[str, Dict[str, List[Any]]] = Field(
        ...,
        description="Changes made on the mobile client (created, updated, deleted) grouped by table"
    )
    last_pulled_at: Optional[datetime] = Field(
        None,
        alias="lastPulledAt",
        description="Timestamp of the last client pull to identify conflict windows"
    )
