from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict


class ExportedSkill(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    level: Optional[str] = None
    years_of_experience: int = 0


class ExportedProject(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    tagline: Optional[str] = None
    description: str
    stage: str
    visibility: str
    tech_stack: Optional[str] = None
    repository_url: Optional[str] = None
    website_url: Optional[str] = None
    team_size: int = 1
    hiring: bool = True
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime


class ExportedApplication(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    status: str
    message: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    created_at: datetime


class ExportedConnection(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    username: Optional[str] = None
    full_name: Optional[str] = None
    direction: str
    created_at: datetime


class ExportedMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    content: str
    type: str
    created_at: datetime


class ExportedBookmark(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime


class ExportedOrganization(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    organization_type: str
    description: Optional[str] = None
    created_at: datetime


class UserExportData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exported_at: datetime
    profile: dict[str, Any]
    skills: list[ExportedSkill]
    projects: list[ExportedProject]
    project_memberships: list[dict[str, Any]]
    applications: list[ExportedApplication]
    connections: list[ExportedConnection]
    messages: list[ExportedMessage]
    bookmarks: list[ExportedBookmark]
    organizations: list[ExportedOrganization]
    activities: list[dict[str, Any]]
    notifications: list[dict[str, Any]]
    builder_flares: list[dict[str, Any]]


class ExportResponse(BaseModel):
    success: bool = True
    data: UserExportData
