from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.application import ApplicationStatus


class ApplicationBase(BaseModel):
    message: str | None = None
    portfolio_url: str | None = None
    github_url: str | None = None
    resume_url: str | None = None
    selected_role: str | None = None
    cover_letter: str | None = None


class ApplicationCreate(ApplicationBase):
    project_id: uuid.UUID
    flare_id: uuid.UUID | None = None


class OneClickApplicationCreate(BaseModel):
    project_id: uuid.UUID
    flare_id: uuid.UUID | None = None
    selected_role: str | None = Field(default=None, description="Selected role/position on project")
    cover_letter: str | None = Field(default=None, description="Short intro or custom cover letter")
    resume_url: str | None = Field(default=None, description="Resume link")
    portfolio_url: str | None = Field(default=None, description="Portfolio website link")
    github_url: str | None = Field(default=None, description="GitHub profile URL")
    auto_use_profile: bool = Field(default=True, description="Auto-fill missing fields from DevLink profile")


class ApplicationPrefillResponse(BaseModel):
    user_id: uuid.UUID
    full_name: str
    username: str
    headline: str | None = None
    skills: list[str] = Field(default_factory=list)
    github_url: str | None = None
    portfolio_url: str | None = None
    resume_url: str | None = None
    role: str | None = None
    suggested_cover_letter: str | None = None


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    message: str | None = None
    portfolio_url: str | None = None
    github_url: str | None = None
    resume_url: str | None = None
    selected_role: str | None = None
    cover_letter: str | None = None
    review_notes: str | None = None
    shortlisted: bool | None = None
    interview_scheduled_at: datetime | None = None
    interview_link: str | None = None


class ApplicationResponse(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    applicant_id: uuid.UUID
    project_id: uuid.UUID
    flare_id: uuid.UUID | None = None
    status: ApplicationStatus
    review_notes: str | None = None
    shortlisted: bool = False
    interview_scheduled_at: datetime | None = None
    interview_link: str | None = None
    created_at: datetime
    updated_at: datetime
