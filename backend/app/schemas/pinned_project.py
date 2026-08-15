from __future__ import annotations

"""
Schemas for pinned profile projects (#1042).
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.pinned_project import MAX_PINNED_PROJECTS


class PinnedProjectCreate(BaseModel):
    project_id: uuid.UUID = Field(
        ..., description="Project to pin; appended after any existing pins"
    )


class PinnedProjectReorder(BaseModel):
    project_ids: list[uuid.UUID] = Field(
        ...,
        max_length=MAX_PINNED_PROJECTS,
        description=(
            "The complete pinned set, in display order. Replaces whatever was "
            "pinned before. An empty list clears all pins."
        ),
    )


class PinnedProjectSummary(BaseModel):
    """The slice of a project a profile card needs. Not the full project."""

    id: uuid.UUID
    title: str
    slug: str
    tagline: Optional[str] = None
    stage: Optional[str] = None
    tech_stack: Optional[str] = None
    tags: Optional[list] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    stars: int = 0
    views: int = 0

    model_config = ConfigDict(from_attributes=True)


class PinnedProjectResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    position: int
    project: Optional[PinnedProjectSummary] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PinnedProjectList(BaseModel):
    items: list[PinnedProjectResponse]
    total: int
    max_pins: int = Field(
        default=MAX_PINNED_PROJECTS, description="Server-enforced cap"
    )
