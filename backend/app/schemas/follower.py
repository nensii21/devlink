from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ==========================================================
# Follower Response
# ==========================================================


class FollowerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    follower_id: uuid.UUID
    following_id: uuid.UUID
    created_at: datetime


# ==========================================================
# Follow Status
# ==========================================================


class FollowStatusResponse(BaseModel):
    is_following: bool
    follower_count: int
    following_count: int


# ==========================================================
# Follow Action Response
# ==========================================================


class FollowActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    follower_id: uuid.UUID
    following_id: uuid.UUID
    created_at: datetime
    follower_count: int
    following_count: int


# ==========================================================
# Unfollow Response
# ==========================================================


class UnfollowResponse(BaseModel):
    message: str
    follower_count: int
    following_count: int
