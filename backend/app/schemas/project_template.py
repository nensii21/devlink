from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TemplateAuthorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    avatar: Optional[str] = None


class ProjectTemplateCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, example="Next.js Fullstack SaaS Starter")
    description: str = Field(..., min_length=10, example="A modern production-ready template with Auth, Stripe, and PostgreSQL.")
    category: str = Field(default="web-app", example="web-app")
    tech_stack: list[str] = Field(default_factory=list, example=["Next.js", "TailwindCSS", "PostgreSQL"])
    features: list[str] = Field(default_factory=list, example=["OAuth Authentication", "Dark Mode", "API Routes"])
    repository_url: Optional[str] = Field(default=None, example="https://github.com/example/starter")
    demo_url: Optional[str] = Field(default=None, example="https://starter-demo.example.com")


class ProjectTemplateUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, min_length=10)
    category: Optional[str] = None
    tech_stack: Optional[list[str]] = None
    features: Optional[list[str]] = None
    repository_url: Optional[str] = None
    demo_url: Optional[str] = None
    is_published: Optional[bool] = None


class ProjectTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    description: str
    category: str
    tech_stack: list[str]
    features: list[str]
    repository_url: Optional[str] = None
    demo_url: Optional[str] = None
    author_id: uuid.UUID
    author: Optional[TemplateAuthorResponse] = None
    is_featured: bool
    is_published: bool
    clones_count: int
    stars_count: int
    is_favorited: bool = False
    created_at: datetime
    updated_at: datetime


class ProjectTemplateCloneRequest(BaseModel):
    new_project_title: Optional[str] = Field(default=None, description="Custom title for cloned project")
    description: Optional[str] = Field(default=None, description="Custom description for cloned project")


class ProjectTemplateListResponse(BaseModel):
    templates: list[ProjectTemplateResponse]
    total: int
    categories: list[str] = [
        "web-app",
        "mobile-app",
        "ai-ml",
        "cli-tool",
        "backend-service",
        "library",
        "other",
    ]
