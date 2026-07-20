from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Any, Dict

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field
from app.models.activity import ActivityType


class ActivityBase(BaseModel):
    activity_type: ActivityType
    title: str
    description: Optional[str] = None
    target_id: Optional[uuid.UUID] = None
    target_type: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    icon: Optional[str] = None
    color: Optional[str] = None


class ActivityCreate(ActivityBase):
    actor_id: uuid.UUID


class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")


class ActivityResponse(ActivityBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    actor_id: uuid.UUID
    created_at: datetime
