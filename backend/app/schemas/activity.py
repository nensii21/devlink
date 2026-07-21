from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.activity import ActivityType


class ActivityActor(BaseModel):
    """Lightweight user representation embedded in activity responses."""

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

    project_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    repository_id: Optional[uuid.UUID] = None
    application_id: Optional[uuid.UUID] = None
    builder_flare_id: Optional[uuid.UUID] = None

    icon: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    color: Optional[str] = Field(
        default=None,
        max_length=30,
    )


class ActivityCreate(ActivityBase):
    """Schema for creating a new activity record.

    ``actor_id`` is intentionally NOT included here — it is always
    derived from the authenticated user (or passed explicitly to
    ``ActivityService.create_activity`` / ``record_activity``) so a
    client cannot forge activity under another user's identity.
    """

    pass


class ActivityUpdate(BaseModel):
    activity_type: Optional[ActivityType] = None

    title: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    description: Optional[str] = None

    project_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    repository_id: Optional[uuid.UUID] = None
    application_id: Optional[uuid.UUID] = None
    builder_flare_id: Optional[uuid.UUID] = None

    icon: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    color: Optional[str] = Field(
        default=None,
        max_length=30,
    )


class ActivityResponse(ActivityBase):
    """Full activity record returned to API clients.

    Includes the ``actor`` sub-object (when available) so the frontend
    can render the user who performed the action without a second
    round-trip to ``/api/users/{id}``.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID
    actor: ActivityActor | None = None
    created_at: datetime
