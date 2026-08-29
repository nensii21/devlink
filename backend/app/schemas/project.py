from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.project import ProjectStage, ProjectStatus, ProjectVisibility

# ==========================================================
# Base Project Schema
# ==========================================================


class ProjectBase(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    slug: Optional[str] = Field(
        default=None,
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
    status: ProjectStatus = ProjectStatus.RECRUITING

    @field_validator("status", mode="before")
    @classmethod
    def validate_and_normalize_status(cls, v: Any) -> Any:
        if v is None:
            return v
        from app.services.project_status_service import _parse_status_enum

        try:
            return _parse_status_enum(v)
        except ValueError:
            return v

    tech_stack: Optional[str] = None
    requirements: Optional[str] = None

    repository_url: Optional[str] = None
    website_url: Optional[str] = None
    demo_url: Optional[str] = None

    team_size: int = 1
    max_team_size: int = 5
    hiring: bool = True

    logo_url: Optional[str] = None
    banner_url: Optional[str] = None

    language: Optional[str] = None
    experience_level: Optional[str] = None
    is_remote: bool = False
    is_paid: bool = False
    is_opensource: bool = False

    scheduled_publish_at: Optional[datetime] = None
    is_published: bool = True


# ==========================================================
# Create Project
# ==========================================================


class ProjectCreate(ProjectBase):
    allow_duplicate: bool = Field(
        default=False,
        description="Manual override flag to allow project creation even if a potential duplicate is detected",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "DevLink",
                "tagline": "The ultimate developer collaboration platform.",
                "description": "DevLink connects developers to open source projects, hackathons, and networking opportunities.",
                "stage": "MVP",
                "visibility": "PUBLIC",
                "hiring": True,
                "is_opensource": True,
                "repository_url": "https://github.com/nensii21/devlink",
                "tech_stack": "React, FastAPI, PostgreSQL",
            }
        }
    )


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
    status: Optional[ProjectStatus] = None

    @field_validator("status", mode="before")
    @classmethod
    def validate_and_normalize_status(cls, v: Any) -> Any:
        if v is None:
            return v
        from app.services.project_status_service import _parse_status_enum

        try:
            return _parse_status_enum(v)
        except ValueError:
            return v

    tech_stack: Optional[str] = None
    requirements: Optional[str] = None
    repository_url: Optional[str] = None
    website_url: Optional[str] = None
    demo_url: Optional[str] = None
    team_size: Optional[int] = None
    max_team_size: Optional[int] = None
    hiring: Optional[bool] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None

    language: Optional[str] = None
    experience_level: Optional[str] = None
    is_remote: Optional[bool] = None
    is_paid: Optional[bool] = None
    is_opensource: Optional[bool] = None

    scheduled_publish_at: Optional[datetime] = None
    is_published: Optional[bool] = None
    version: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "DevLink Beta",
                "hiring": False,
                "stage": "BETA",
                "team_size": 3,
            }
        }
    )


# ==========================================================
# Project Response
# ==========================================================


class SimilarProjectWarning(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    title_similarity: float
    description_similarity: float


class ProjectStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: uuid.UUID
    views: int
    applicants: int
    accepted_members: int
    bookmark_count: int


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID

    stars: int = 0
    views: int = 0
    applications_count: int = 0

    is_featured: bool = False
    is_archived: bool = False

    created_at: datetime
    updated_at: datetime
    version: int = 1

    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[uuid.UUID] = None
    scheduled_publish_at: Optional[datetime] = None
    is_published: bool = True


class ProjectDraftCreate(ProjectBase):
    pass


class ProjectDraftUpdate(ProjectUpdate):
    pass


class ProjectCloneRequest(BaseModel):
    title: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[ProjectVisibility] = None
    include_milestones: bool = False
    include_tags: bool = True
