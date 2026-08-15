from __future__ import annotations

"""
Schemas for project release notes (#1043).
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.project_release import (
    MAX_HIGHLIGHT_LENGTH,
    MAX_HIGHLIGHTS,
    ReleaseStatus,
    ReleaseType,
)


def _clean_highlights(values: Optional[list[str]]) -> list[str]:
    """Drop blanks, strip whitespace, and enforce the per-item length cap."""
    if not values:
        return []

    cleaned: list[str] = []
    for raw in values:
        item = (raw or "").strip()
        if not item:
            continue
        if len(item) > MAX_HIGHLIGHT_LENGTH:
            raise ValueError(
                f"Each highlight must be {MAX_HIGHLIGHT_LENGTH} characters or fewer."
            )
        cleaned.append(item)

    if len(cleaned) > MAX_HIGHLIGHTS:
        raise ValueError(f"At most {MAX_HIGHLIGHTS} highlights are allowed.")
    return cleaned


class ReleaseCreate(BaseModel):
    version: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Free-form version label: v1.2.0, 2026.08, beta-3. Unique per project.",
    )
    title: str = Field(..., min_length=1, max_length=200)
    body: Optional[str] = Field(default=None, description="Markdown release notes")
    highlights: list[str] = Field(
        default_factory=list, description="Short bullet points"
    )
    release_type: ReleaseType = Field(default=ReleaseType.MINOR)
    # Defaults to draft: writing a changelog entry and announcing it are two
    # different decisions, and conflating them means every typo is broadcast.
    status: ReleaseStatus = Field(default=ReleaseStatus.DRAFT)

    @field_validator("version", "title")
    @classmethod
    def _strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be blank.")
        return cleaned

    @field_validator("highlights")
    @classmethod
    def _validate_highlights(cls, value: list[str]) -> list[str]:
        return _clean_highlights(value)


class ReleaseUpdate(BaseModel):
    version: Optional[str] = Field(default=None, min_length=1, max_length=50)
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    body: Optional[str] = None
    highlights: Optional[list[str]] = None
    release_type: Optional[ReleaseType] = None

    @field_validator("version", "title")
    @classmethod
    def _strip_optional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be blank.")
        return cleaned

    @field_validator("highlights")
    @classmethod
    def _validate_highlights(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        return _clean_highlights(value)


class ReleaseAuthor(BaseModel):
    id: uuid.UUID
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReleaseResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    author_id: Optional[uuid.UUID] = None

    version: str
    title: str
    body: Optional[str] = None
    highlights: list[str] = Field(default_factory=list)

    release_type: ReleaseType
    status: ReleaseStatus
    published_at: Optional[datetime] = None
    is_pinned: bool = False

    author: Optional[ReleaseAuthor] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReleaseList(BaseModel):
    items: list[ReleaseResponse]
    total: int
    limit: int
    offset: int
