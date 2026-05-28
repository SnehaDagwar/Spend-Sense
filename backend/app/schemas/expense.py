"""Pydantic schemas for expenses.

Includes request/response schemas and the query-parameter model used by the
list endpoint for filtering and cursor-based pagination.
"""

from __future__ import annotations

import base64
import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import Field, field_validator, model_validator

from app.models.enums import CurrencyCode, PaymentMethod
from app.schemas.base import APIModel
from app.schemas.category import CategoryPublic

# ---------------------------------------------------------------------------
# Pagination cursor helpers
# ---------------------------------------------------------------------------

class PaginationCursor:
    """Opaque base64 cursor encoding (expense_date, id)."""

    @staticmethod
    def encode(expense_date: date, expense_id: uuid.UUID) -> str:
        payload = json.dumps(
            {"date": expense_date.isoformat(), "id": str(expense_id)},
            separators=(",", ":"),
        )
        return base64.urlsafe_b64encode(payload.encode()).decode()

    @staticmethod
    def decode(cursor: str) -> tuple[date, uuid.UUID]:
        try:
            raw = base64.urlsafe_b64decode(cursor.encode()).decode()
            data = json.loads(raw)
            return date.fromisoformat(data["date"]), uuid.UUID(data["id"])
        except Exception as exc:
            raise ValueError(f"Invalid pagination cursor: {cursor!r}") from exc


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ExpenseCreate(APIModel):
    """Payload for POST /expenses."""

    category_id: uuid.UUID
    amount: Annotated[Decimal, Field(gt=Decimal("0"), max_digits=14, decimal_places=2)]
    expense_date: date
    note: Annotated[str, Field(max_length=500)] = ""
    payment_method: Optional[PaymentMethod] = None
    merchant: Annotated[Optional[str], Field(max_length=200)] = None
    tags: Annotated[list[str], Field(max_length=10)] = []
    currency: CurrencyCode = CurrencyCode.INR
    is_recurring: bool = False
    receipt_file_id: Optional[uuid.UUID] = None
    paid_by_member_id: Optional[uuid.UUID] = None

    @field_validator("note")
    @classmethod
    def strip_note(cls, v: str) -> str:
        return v.strip()

    @field_validator("merchant")
    @classmethod
    def strip_merchant(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: list) -> list[str]:
        if len(v) > 10:
            raise ValueError("A maximum of 10 tags are allowed per expense.")
        cleaned: list[str] = []
        for tag in v:
            tag = str(tag).strip().lower()
            if not tag:
                continue
            if len(tag) > 50:
                raise ValueError(f"Each tag must be 50 characters or fewer (got: {tag!r}).")
            cleaned.append(tag)
        return cleaned

    @field_validator("expense_date")
    @classmethod
    def validate_date_not_too_far_future(cls, v: date) -> date:
        from datetime import date as d
        today = d.today()
        delta = (v - today).days
        if delta > 30:
            raise ValueError("Expense date cannot be more than 30 days in the future.")
        return v


class ExpenseUpdate(APIModel):
    """Payload for PATCH /expenses/{expense_id}.

    All fields are optional — only provided fields are updated.
    """

    category_id: Optional[uuid.UUID] = None
    amount: Annotated[
        Optional[Decimal],
        Field(default=None, gt=Decimal("0"), max_digits=14, decimal_places=2),
    ] = None
    expense_date: Optional[date] = None
    note: Annotated[Optional[str], Field(max_length=500)] = None
    payment_method: Optional[PaymentMethod] = None
    merchant: Annotated[Optional[str], Field(max_length=200)] = None
    tags: Annotated[Optional[list[str]], Field(max_length=10)] = None
    currency: Optional[CurrencyCode] = None
    is_recurring: Optional[bool] = None
    receipt_file_id: Optional[uuid.UUID] = None
    paid_by_member_id: Optional[uuid.UUID] = None

    @field_validator("note")
    @classmethod
    def strip_note(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip()
        return v

    @field_validator("merchant")
    @classmethod
    def strip_merchant(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: Optional[list]) -> Optional[list[str]]:
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("A maximum of 10 tags are allowed per expense.")
        cleaned: list[str] = []
        for tag in v:
            tag = str(tag).strip().lower()
            if not tag:
                continue
            if len(tag) > 50:
                raise ValueError(f"Each tag must be 50 characters or fewer (got: {tag!r}).")
            cleaned.append(tag)
        return cleaned

    @model_validator(mode="after")
    def at_least_one_field(self) -> "ExpenseUpdate":
        provided = {
            k for k, v in self.model_dump(exclude_none=True).items() if v is not None
        }
        if not provided:
            raise ValueError("At least one field must be provided for an update.")
        return self


# ---------------------------------------------------------------------------
# Query-parameter model
# ---------------------------------------------------------------------------

class ExpenseFilters(APIModel):
    """Query parameters accepted by GET /expenses."""

    month: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    category_id: Optional[uuid.UUID] = None
    payment_method: Optional[PaymentMethod] = None
    amount_min: Annotated[
        Optional[Decimal],
        Field(default=None, gt=Decimal("0"), max_digits=14, decimal_places=2),
    ] = None
    amount_max: Annotated[
        Optional[Decimal],
        Field(default=None, gt=Decimal("0"), max_digits=14, decimal_places=2),
    ] = None
    is_recurring: Optional[bool] = None
    tags: Optional[str] = Field(
        default=None,
        description="Comma-separated list of tags to filter by (AND logic).",
    )
    q: Optional[str] = Field(
        default=None, max_length=200,
        description="Full-text search across note and merchant.",
    )
    sort_by: str = Field(default="date", pattern=r"^(date|amount)$")
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$")
    limit: Annotated[int, Field(ge=1, le=200)] = 50
    cursor: Optional[str] = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "ExpenseFilters":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to.")
        if self.amount_min and self.amount_max and self.amount_min > self.amount_max:
            raise ValueError("amount_min must be less than or equal to amount_max.")
        if self.month and (self.date_from or self.date_to):
            raise ValueError("Provide either 'month' or 'dateFrom'/'dateTo', not both.")
        return self

    def parsed_tags(self) -> list[str]:
        """Return the tags filter as a list."""
        if not self.tags:
            return []
        return [t.strip().lower() for t in self.tags.split(",") if t.strip()]


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ExpensePublic(APIModel):
    """Single expense representation returned by the API."""

    id: uuid.UUID
    category_id: uuid.UUID
    category: CategoryPublic
    amount: Decimal
    expense_date: date
    note: str
    payment_method: Optional[PaymentMethod] = None
    merchant: Optional[str] = None
    tags: list[str] = []
    currency: CurrencyCode
    is_recurring: bool
    paid_by_member_id: Optional[uuid.UUID] = None
    receipt_file_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class ExpenseListResponse(APIModel):
    """Paginated response envelope for GET /expenses."""

    items: list[ExpensePublic]
    next_cursor: Optional[str] = None
    total_returned: int
