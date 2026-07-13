from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.activity import ActivityType


class ActivityCreate(BaseModel):
    actor_id: uuid.UUID
    activity_type: ActivityType
    title: str
    description: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    repository_id: Optional[uuid.UUID] = None
    application_id: Optional[uuid.UUID] = None
    builder_flare_id: Optional[uuid.UUID] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID
    activity_type: ActivityType
    title: str
    description: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    repository_id: Optional[uuid.UUID] = None
    application_id: Optional[uuid.UUID] = None
    builder_flare_id: Optional[uuid.UUID] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    created_at: datetime
