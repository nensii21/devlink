from __future__ import annotations
# pyrefly: ignore [missing-import]
import uuid
# pyrefly: ignore [missing-import]
from datetime import datetime
from typing import Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict
from app.models.application import ApplicationStatus

class ApplicationBase(BaseModel):
    message: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    resume_url: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    message: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    resume_url: Optional[str] = None
    review_notes: Optional[str] = None
    shortlisted: Optional[bool] = None

class ApplicationResponse(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    applicant_id: uuid.UUID
    project_id: uuid.UUID
    flare_id: uuid.UUID
    status: ApplicationStatus
    review_notes: Optional[str] = None
    shortlisted: bool
    created_at: datetime
    updated_at: datetime
