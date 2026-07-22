from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict
from app.models.project import ProjectStage, ProjectVisibility


class ProjectBase(BaseModel):
    title: str
    slug: str
    tagline: Optional[str] = None
    description: str
    stage: ProjectStage = ProjectStage.IDEA
    visibility: ProjectVisibility = ProjectVisibility.PUBLIC
    tech_stack: Optional[str] = None
    tags: Optional[list[str]] = None
    repository_url: Optional[str] = None
    website_url: Optional[str] = None
    demo_url: Optional[str] = None
    team_size: int = 1
    max_team_size: int = 5
    hiring: bool = True
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    stage: Optional[ProjectStage] = None
    visibility: Optional[ProjectVisibility] = None
    tech_stack: Optional[str] = None
    tags: Optional[list[str]] = None
    repository_url: Optional[str] = None
    website_url: Optional[str] = None
    demo_url: Optional[str] = None
    team_size: Optional[int] = None
    max_team_size: Optional[int] = None
    hiring: Optional[bool] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None


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
    stars: int
    views: int
    applications_count: int
    is_featured: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
