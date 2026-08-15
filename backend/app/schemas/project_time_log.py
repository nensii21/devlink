from __future__ import annotations

"""
Schemas for project time tracking (#1041).
"""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# A single entry may not exceed one day's work. Anything longer is a data-entry
# slip (or a timer someone forgot to stop), not a real claim.
MAX_MINUTES_PER_ENTRY = 24 * 60
MIN_MINUTES_PER_ENTRY = 1

# How far back a member may backfill. Beyond this the number stops being a
# recollection and starts being a guess.
MAX_BACKFILL_DAYS = 90


class TimeLogCreate(BaseModel):
    minutes: int = Field(
        ...,
        ge=MIN_MINUTES_PER_ENTRY,
        le=MAX_MINUTES_PER_ENTRY,
        description="Duration in whole minutes, 1 to 1440",
    )
    work_date: date = Field(
        ..., description="The day the work happened (UTC), not the day it was logged"
    )
    description: Optional[str] = Field(default=None, max_length=500)
    milestone_id: Optional[uuid.UUID] = Field(
        default=None, description="Milestone this work counts towards"
    )
    is_billable: bool = Field(default=False)

    @field_validator("description")
    @classmethod
    def _strip_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class TimeLogUpdate(BaseModel):
    minutes: Optional[int] = Field(
        default=None, ge=MIN_MINUTES_PER_ENTRY, le=MAX_MINUTES_PER_ENTRY
    )
    work_date: Optional[date] = None
    description: Optional[str] = Field(default=None, max_length=500)
    milestone_id: Optional[uuid.UUID] = None
    is_billable: Optional[bool] = None

    @field_validator("description")
    @classmethod
    def _strip_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class TimeLogAuthor(BaseModel):
    id: uuid.UUID
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TimeLogResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    milestone_id: Optional[uuid.UUID] = None

    minutes: int
    hours: float = Field(
        description="Minutes as hours, rounded to two decimals, for display"
    )
    work_date: date
    description: Optional[str] = None
    is_billable: bool

    user: Optional[TimeLogAuthor] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimeLogList(BaseModel):
    items: list[TimeLogResponse]
    total: int
    limit: int
    offset: int
    total_minutes: int = Field(
        description="Sum of minutes across the whole filtered set, not just this page"
    )


class ContributorTotal(BaseModel):
    user_id: uuid.UUID
    username: Optional[str] = None
    minutes: int
    hours: float
    entries: int


class MilestoneTotal(BaseModel):
    milestone_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Null groups together work not attached to any milestone",
    )
    milestone_title: Optional[str] = None
    minutes: int
    hours: float
    entries: int


class TimeLogSummary(BaseModel):
    project_id: uuid.UUID

    total_minutes: int
    total_hours: float
    total_entries: int

    billable_minutes: int
    billable_hours: float
    non_billable_minutes: int
    non_billable_hours: float

    contributor_count: int
    first_logged_date: Optional[date] = None
    last_logged_date: Optional[date] = None

    by_contributor: list[ContributorTotal] = Field(default_factory=list)
    by_milestone: list[MilestoneTotal] = Field(default_factory=list)
