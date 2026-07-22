from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.activity import ActivityType


class ActivityActor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    username: str
    profile_image: str | None = None


class ActivityBase(BaseModel):
    activity_type: ActivityType

    title: str = Field(
        ...,
        min_length=2,
        max_length=255,
    )

    description: str | None = None

    project_id: uuid.UUID | None = None
    organization_id: uuid.UUID | None = None
    repository_id: uuid.UUID | None = None
    application_id: uuid.UUID | None = None
    builder_flare_id: uuid.UUID | None = None

    icon: str | None = Field(
        default=None,
        max_length=100,
    )

    color: str | None = Field(
        default=None,
        max_length=30,
    )


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    activity_type: ActivityType | None = None

    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    description: str | None = None

    project_id: uuid.UUID | None = None
    organization_id: uuid.UUID | None = None
    repository_id: uuid.UUID | None = None
    application_id: uuid.UUID | None = None
    builder_flare_id: uuid.UUID | None = None

    icon: str | None = Field(
        default=None,
        max_length=100,
    )

    color: str | None = Field(
        default=None,
        max_length=30,
    )


from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict
from app.models.activity import ActivityType


class ActivityBase(BaseModel):
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


class ActivityCreate(ActivityBase):
    actor_id: uuid.UUID


class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class ActivityResponse(ActivityBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID
    actor: ActivityActor | None = None
    created_at: datetime
