from __future__ import annotations

from typing import List, Dict
from pydantic import BaseModel, Field


class ActivityPoint(BaseModel):
    date: str
    activity_count: int
    projects: int = 0
    messages: int = 0
    applications: int = 0


class DeveloperInsightsMetrics(BaseModel):
    projects_created: int = Field(0, description="Total projects created in range")
    applications_submitted: int = Field(0, description="Total applications submitted")
    profile_views: int = Field(0, description="Total profile views")
    followers_gained: int = Field(0, description="Followers gained in range")
    messages_sent: int = Field(0, description="Messages sent")
    contribution_streak: int = Field(
        0, description="Current contribution streak in days"
    )
    ai_match_success_rate: float = Field(0.0, description="AI match success percentage")


class MetricTrend(BaseModel):
    current: float
    previous: float
    percentage_change: float


class DeveloperInsightsResponse(BaseModel):
    user_id: int
    date_range: str
    metrics: DeveloperInsightsMetrics
    trends: Dict[str, MetricTrend]
    activity_timeline: List[ActivityPoint]
    top_skills_matched: List[str]
    recent_achievements: List[str]
