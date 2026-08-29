from __future__ import annotations

from typing import List
from pydantic import BaseModel, ConfigDict, Field


class DAUMetric(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: str = Field(..., description="Date string in YYYY-MM-DD format")
    active_users: int = Field(
        ..., description="Count of distinct active users on this day"
    )


class ActiveUsersOverview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dau: int = Field(..., description="Daily Active Users (last 24 hours)")
    wau: int = Field(..., description="Weekly Active Users (last 7 days)")
    mau: int = Field(..., description="Monthly Active Users (last 30 days)")
    daily_trend: List[DAUMetric] = Field(
        default_factory=list,
        description="Daily active users time series breakdown",
    )


class RetentionMetric(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    retention_7d_pct: float = Field(
        ...,
        description="Percentage of users registered >7 days ago who were active in last 7 days",
    )
    retention_30d_pct: float = Field(
        ...,
        description="Percentage of users registered >30 days ago who were active in last 30 days",
    )
    retained_7d_users: int = Field(
        ..., description="Count of retained users over 7 days"
    )
    eligible_7d_users: int = Field(
        ..., description="Count of users eligible for 7-day retention"
    )
    retained_30d_users: int = Field(
        ..., description="Count of retained users over 30 days"
    )
    eligible_30d_users: int = Field(
        ..., description="Count of users eligible for 30-day retention"
    )


class ConversionMetric(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_completion_pct: float = Field(
        ..., description="Percentage of registered users with complete profile details"
    )
    project_creator_pct: float = Field(
        ..., description="Percentage of registered users who created at least 1 project"
    )
    application_acceptance_pct: float = Field(
        ..., description="Percentage of builder flare applications that were accepted"
    )
    user_application_pct: float = Field(
        ...,
        description="Percentage of registered users who submitted at least 1 application",
    )
    completed_profiles_count: int = Field(
        ..., description="Total completed user profiles"
    )
    project_creators_count: int = Field(
        ..., description="Total users with at least 1 project"
    )
    total_applications_count: int = Field(
        ..., description="Total builder flare applications"
    )
    accepted_applications_count: int = Field(
        ..., description="Total accepted applications"
    )


class DailyProjectMetric(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: str = Field(..., description="Date string in YYYY-MM-DD format")
    new_projects: int = Field(..., description="New projects created on this date")
    cumulative_projects: int = Field(
        ..., description="Cumulative project count up to this date"
    )


class ProjectGrowthMetric(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_projects: int = Field(..., description="Total projects count in database")
    new_projects_period: int = Field(
        ..., description="New projects created in the specified period"
    )
    growth_rate_pct: float = Field(
        ..., description="Percentage growth in projects over the period"
    )
    daily_growth: List[DailyProjectMetric] = Field(
        default_factory=list,
        description="Daily breakdown of project creation over time",
    )


class PlatformAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timeframe_days: int = Field(..., description="Analysis window length in days")
    active_users: ActiveUsersOverview = Field(
        ..., description="DAU, WAU, and MAU metrics"
    )
    retention: RetentionMetric = Field(..., description="User retention statistics")
    conversion: ConversionMetric = Field(..., description="Conversion funnel rates")
    project_growth: ProjectGrowthMetric = Field(
        ..., description="Project growth metrics and trend"
    )


class PlatformSocialProofResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    developers: int = Field(..., description="Total registered active developers")
    projects: int = Field(..., description="Total published projects")
    teams: int = Field(..., description="Total teams formed")
    organizations: int = Field(..., description="Total partner organizations")
    hackathons: int = Field(..., description="Total hosted hackathons")
    last_updated: str = Field(..., description="ISO timestamp of stats calculation")
