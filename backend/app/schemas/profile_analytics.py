from __future__ import annotations

import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProfileAnalyticSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int = Field(..., description="Total count of events/interactions")
    growth_pct: float = Field(..., description="Week-over-week growth percentage")


class ProfileAnalyticsSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_views: ProfileAnalyticSummaryItem = Field(
        ..., description="Summary for profile views"
    )
    search_appearances: ProfileAnalyticSummaryItem = Field(
        ..., description="Summary for search appearances"
    )
    connection_requests: ProfileAnalyticSummaryItem = Field(
        ..., description="Summary for connection requests (new followers)"
    )
    repository_clicks: ProfileAnalyticSummaryItem = Field(
        ..., description="Summary for repository link clicks"
    )
    project_clicks: ProfileAnalyticSummaryItem = Field(
        ..., description="Summary for project card clicks"
    )


class ProfileAnalyticTrendItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: str = Field(..., description="Date string in YYYY-MM-DD format")
    profile_views: int = Field(..., description="Profile views on this day")
    search_appearances: int = Field(..., description="Search appearances on this day")
    connection_requests: int = Field(
        ..., description="Connection requests (follows) on this day"
    )
    repository_clicks: int = Field(..., description="Repository clicks on this day")
    project_clicks: int = Field(..., description="Project clicks on this day")


class ProfileAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    summary: ProfileAnalyticsSummary = Field(
        ..., description="Overview summaries for each tracked metric"
    )
    trends: List[ProfileAnalyticTrendItem] = Field(
        default_factory=list,
        description="Daily trend breakdown for each tracked metric over the last 7 days",
    )


class TrackClickRequest(BaseModel):
    click_type: str = Field(..., description="Type of click: 'repository' or 'project'")
    target_user_id: uuid.UUID = Field(
        ..., description="ID of the user whose resource was clicked"
    )
    entity_id: Optional[uuid.UUID] = Field(
        None, description="Optional ID of the project or repository entity clicked"
    )
