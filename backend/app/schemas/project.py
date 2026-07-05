from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from app.models.project import ProjectStage, ProjectVisibility

class ProjectBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    slug: str = Field(..., min_length=3, max_length=200)
    tagline: Optional[str] = Field(default=None, max_length=255)
    description: str
    stage: ProjectStage = ProjectStage.IDEA
    visibility: ProjectVisibility = ProjectVisibility.PUBLIC
    tech_stack: Optional[str] = None
    repository_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None
    demo_url: Optional[HttpUrl] = None
    max_team_size: int = 5
    hiring: bool = True

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    tagline: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    stage: Optional[ProjectStage] = None
    visibility: Optional[ProjectVisibility] = None
    tech_stack: Optional[str] = None
    repository_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None
    demo_url: Optional[HttpUrl] = None
    max_team_size: Optional[int] = None
    hiring: Optional[bool] = None

class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    owner_id: uuid.UUID
    team_size: int
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    stars: int
    views: int
    applications_count: int
    is_featured: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
