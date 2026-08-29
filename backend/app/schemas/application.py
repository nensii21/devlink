from __future__ import annotations

# pyrefly: ignore [missing-import]
import uuid

# pyrefly: ignore [missing-import]
from datetime import datetime

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict

from app.models.application import ApplicationStatus


class ApplicationBase(BaseModel):
    message: str | None = None
    portfolio_url: str | None = None
    github_url: str | None = None
    resume_url: str | None = None


class ApplicationCreate(ApplicationBase):
    project_id: uuid.UUID
    flare_id: uuid.UUID


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    message: str | None = None
    portfolio_url: str | None = None
    github_url: str | None = None
    resume_url: str | None = None
    review_notes: str | None = None
    shortlisted: bool | None = None
    interview_scheduled_at: datetime | None = None
    interview_link: str | None = None


class ApplicationResponse(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    applicant_id: uuid.UUID
    project_id: uuid.UUID
    flare_id: uuid.UUID
    status: ApplicationStatus
    review_notes: str | None = None
    shortlisted: bool
    interview_scheduled_at: datetime | None = None
    interview_link: str | None = None
    created_at: datetime
    updated_at: datetime
