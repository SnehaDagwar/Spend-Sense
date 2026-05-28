"""Pydantic schemas for spending categories.

System categories are read-only from the API perspective.  Custom categories
are created and mutated by authenticated users.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import Field, field_validator

from app.schemas.base import APIModel

# Slug must be lowercase alphanumeric with optional hyphens, 1–50 chars
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{0,48}[a-z0-9]$|^[a-z0-9]$")

# Accepts #RRGGBB, #RGB, hsl(...), rgb(...), or CSS named colors (loose check)
_COLOR_RE = re.compile(
    r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$"
    r"|^hsl\(.+\)$"
    r"|^rgb\(.+\)$"
    r"|^[a-z]+$",
)


# ---------------------------------------------------------------------------
# Shared validators
# ---------------------------------------------------------------------------

def _validate_slug(value: str) -> str:
    value = value.strip().lower()
    if not _SLUG_RE.match(value):
        raise ValueError(
            "Slug must be 1–50 lowercase alphanumeric characters, "
            "optionally separated by hyphens."
        )
    return value


def _validate_color(value: str) -> str:
    value = value.strip()
    if not _COLOR_RE.match(value):
        raise ValueError(
            "Color must be a valid CSS color: #RRGGBB, hsl(...), rgb(...), or a named color."
        )
    return value


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CategoryCreate(APIModel):
    """Payload for POST /categories."""

    slug: Annotated[str, Field(min_length=1, max_length=50)]
    name: Annotated[str, Field(min_length=1, max_length=100)]
    icon: Annotated[str, Field(min_length=1, max_length=100)]
    color: Annotated[str, Field(min_length=1, max_length=100)]
    display_order: Annotated[int, Field(ge=0, le=32767)] = 0

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return _validate_slug(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be blank.")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        return _validate_color(v)

    @field_validator("icon")
    @classmethod
    def validate_icon(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Icon cannot be blank.")
        return v


class CategoryUpdate(APIModel):
    """Payload for PATCH /categories/{category_id}.

    All fields are optional — only provided fields are updated.
    """

    name: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    icon: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    color: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    display_order: Annotated[int | None, Field(ge=0, le=32767)] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Name cannot be blank.")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is not None:
            return _validate_color(v)
        return v

    @field_validator("icon")
    @classmethod
    def validate_icon(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Icon cannot be blank.")
        return v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CategoryPublic(APIModel):
    """Single category representation returned by the API."""

    id: uuid.UUID
    slug: str
    name: str
    icon: str
    color: str
    is_system: bool
    is_archived: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class CategoryListResponse(APIModel):
    """Response envelope for GET /categories."""

    items: list[CategoryPublic]
