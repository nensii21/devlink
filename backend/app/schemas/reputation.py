"""
Reputation System Schemas (#597)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReputationAwardRequest(BaseModel):
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Target user ID to award points to. If null, awards points to authenticated user.",
    )
    action: str = Field(
        ...,
        examples=["merged_pull_request", "completed_project", "community_contribution", "helpful_discussion", "profile_completion", "mentor_recognition"],
        description="Type of activity earning reputation points.",
    )
    points: Optional[int] = Field(
        default=None,
        description="Optional custom point value override.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional description or note.",
    )


class ReputationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    points: int
    description: Optional[str] = None
    created_at: datetime


class ReputationSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    reputation_score: int
    rank_tier: str
    recent_logs: list[ReputationLogResponse] = Field(default_factory=list)


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    reputation_score: int
    rank_tier: str


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry] = Field(default_factory=list)
    total: int
