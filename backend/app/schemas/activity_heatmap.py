from __future__ import annotations

"""
Schemas for the contribution heatmap and streak summary (#1040).
"""

import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# A calendar day's intensity bucket. 0 means "nothing happened"; 1-4 are
# quartiles of the *user's own* activity in the requested window, so a quiet
# account still produces a readable gradient instead of a flat wall of level 1.
HeatmapLevel = int


class HeatmapDay(BaseModel):
    """One cell of the heatmap grid."""

    day: date = Field(description="UTC calendar day")
    count: int = Field(ge=0, description="Number of activities recorded on this day")
    level: HeatmapLevel = Field(ge=0, le=4, description="Intensity bucket, 0-4")

    model_config = ConfigDict(from_attributes=True)


class StreakSummary(BaseModel):
    """Aggregate streak statistics over the requested window."""

    current_streak: int = Field(
        ge=0,
        description=(
            "Consecutive active days ending today or yesterday. Yesterday counts "
            "so that an early-morning request does not report a broken streak."
        ),
    )
    longest_streak: int = Field(
        ge=0, description="Longest run of consecutive active days in the window"
    )
    longest_streak_start: Optional[date] = Field(
        default=None, description="First day of the longest run"
    )
    longest_streak_end: Optional[date] = Field(
        default=None, description="Last day of the longest run"
    )

    total_activities: int = Field(ge=0, description="Total activities in the window")
    active_days: int = Field(
        ge=0, description="Number of days with at least one activity"
    )
    total_days: int = Field(ge=1, description="Size of the window in days")

    busiest_day: Optional[date] = Field(
        default=None, description="Day with the most activity"
    )
    busiest_day_count: int = Field(
        default=0, ge=0, description="Activity count on the busiest day"
    )

    daily_average: float = Field(
        ge=0,
        description="Total activities divided by the window size, rounded to two decimals",
    )
    active_day_average: float = Field(
        ge=0,
        description="Total activities divided by active days only, rounded to two decimals",
    )


class ActivityTypeCount(BaseModel):
    """How the window's activity breaks down by type."""

    activity_type: str
    count: int = Field(ge=0)


class ActivityHeatmapResponse(BaseModel):
    """Full heatmap payload for one user."""

    user_id: uuid.UUID
    username: str

    start_date: date
    end_date: date

    days: list[HeatmapDay] = Field(
        description=(
            "One entry per day in the window, inclusive of both ends and in "
            "ascending order. Days with no activity are present with count 0 so "
            "the client can render the grid without filling gaps itself."
        )
    )
    streak: StreakSummary
    breakdown: list[ActivityTypeCount] = Field(
        default_factory=list,
        description="Activity counts grouped by type, descending",
    )

    model_config = ConfigDict(from_attributes=True)
