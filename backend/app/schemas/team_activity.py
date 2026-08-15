from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TeamActivityType(str, Enum):
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    ROLE_UPDATED = "role_updated"
    PROJECT_UPDATED = "project_updated"
    MILESTONE_COMPLETED = "milestone_completed"
    NEW_DISCUSSION = "new_discussion"
    FILE_UPLOADED = "file_uploaded"


class TeamActivityCreate(BaseModel):
    activity_type: TeamActivityType
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    actor_name: Optional[str] = None
    actor_avatar: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TeamActivityItem(BaseModel):
    id: str
    project_id: int
    activity_type: TeamActivityType
    title: str
    description: Optional[str] = None
    actor_name: str
    actor_avatar: Optional[str] = None
    metadata_info: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class TeamActivityTimelineResponse(BaseModel):
    project_id: int
    items: List[TeamActivityItem]
    total: int
    page: int
    limit: int
    has_more: bool
