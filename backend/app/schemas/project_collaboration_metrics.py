from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class DailyActivityPoint(BaseModel):
    date: str
    activity_count: int
    messages: int
    tasks_completed: int


class ProjectCollaborationMetricsResponse(BaseModel):
    project_id: int
    active_members: int = Field(
        ..., description="Number of active members in last 30 days"
    )
    total_team_size: int = Field(
        ..., description="Total team members assigned to project"
    )
    avg_response_time_hours: float = Field(
        ..., description="Average team response time in hours"
    )
    messages_exchanged: int = Field(
        ..., description="Total messages exchanged in team chat"
    )
    tasks_completed: int = Field(..., description="Total milestones & tasks completed")
    applications_received: int = Field(
        ..., description="Total developer applications received"
    )
    collaboration_score: float = Field(
        ..., description="Team collaboration health score (0-100)"
    )
    daily_activity: List[DailyActivityPoint]
