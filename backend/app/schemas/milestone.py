from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MilestoneCreate(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=200, description="Title of the milestone"
    )
    description: Optional[str] = Field(default=None, description="Detailed description")
    due_date: Optional[datetime] = Field(
        default=None, description="When the milestone is due"
    )
    owner_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of the user assigned to the milestone"
    )


class MilestoneOwner(BaseModel):
    id: uuid.UUID
    username: str
    first_name: str
    last_name: str
    profile_image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MilestoneUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None)
    due_date: Optional[datetime] = Field(default=None)
    is_completed: Optional[bool] = Field(default=None)
    is_archived: Optional[bool] = Field(default=None)
    owner_id: Optional[uuid.UUID] = Field(default=None)


class MilestoneResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    owner_id: Optional[uuid.UUID] = None
    owner: Optional[MilestoneOwner] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MilestoneProgressResponse(BaseModel):
    total_milestones: int
    completed_milestones: int
    active_milestones: int
    archived_milestones: int
    overdue_milestones: int
    completion_percentage: float = Field(
        description="Percentage of completed vs total active milestones (0-100%)"
    )


class MilestoneTimelineItem(BaseModel):
    milestone: MilestoneResponse
    status: str = Field(
        description="Status label: 'overdue', 'upcoming', 'completed', 'archived'"
    )
    days_remaining: Optional[int] = Field(
        default=None, description="Days remaining until due date (negative if overdue)"
    )


class MilestoneTimelineResponse(BaseModel):
    project_id: uuid.UUID
    project_title: str
    progress: MilestoneProgressResponse
    timeline: list[MilestoneTimelineItem]
