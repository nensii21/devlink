from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.project import ProjectStage, ProjectVisibility


# ==========================================================
# Base Project Schema
# ==========================================================


class ProjectBase(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    slug: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    tagline: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    description: str = Field(
        ...,
        min_length=1,
    )

    stage: ProjectStage = ProjectStage.IDEA
    visibility: ProjectVisibility = ProjectVisibility.PUBLIC

    tech_stack: Optional[str] = None

    repository_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None
    demo_url: Optional[HttpUrl] = None

    team_size: int = 1
    max_team_size: int = 5
    hiring: bool = True

    logo_url: Optional[HttpUrl] = None
    banner_url: Optional[HttpUrl] = None


# ==========================================================
# Create Project
# ==========================================================


class ProjectCreate(ProjectBase):
    pass


# ==========================================================
# Update Project
# ==========================================================


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    stage: Optional[ProjectStage] = None
    visibility: Optional[ProjectVisibility] = None
    tech_stack: Optional[str] = None
    repository_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None
    demo_url: Optional[HttpUrl] = None
    team_size: Optional[int] = None
    max_team_size: Optional[int] = None
    hiring: Optional[bool] = None
    logo_url: Optional[HttpUrl] = None
    banner_url: Optional[HttpUrl] = None


# ==========================================================
# Project Response
# ==========================================================


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    owner_id: uuid.UUID

    stars: int
    views: int
    applications_count: int

    is_featured: bool
    is_archived: bool

    created_at: datetime
    updated_at: datetime

    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[uuid.UUID] = None
