"""
Reputation System Schemas (#597)

``ReputationAwardRequest`` used to accept an optional target, an arbitrary
free-text action, and an unbounded integer. The router applied all three
verbatim, with no authorization, which made the endpoint a write primitive for
any user's score. The constraints live here now, so an invalid request is a 422
before any of it reaches the service.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReputationAction(str, Enum):
    """The activities that earn reputation.

    ``action`` was a bare ``str`` with an ``examples=[...]`` list, which is
    documentation, not validation -- anything at all was accepted, and
    ``ACTION_POINTS.get(action.lower(), 10)`` then silently awarded ten points
    for a typo or an invented name. An enum makes an unknown action a 422 and
    keeps the wire values identical to the keys the service already uses.
    """

    MERGED_PULL_REQUEST = "merged_pull_request"
    COMPLETED_PROJECT = "completed_project"
    COMMUNITY_CONTRIBUTION = "community_contribution"
    HELPFUL_DISCUSSION = "helpful_discussion"
    PROFILE_COMPLETION = "profile_completion"
    MENTOR_RECOGNITION = "mentor_recognition"
    SUCCESSFUL_COLLABORATION = "successful_collaboration"
    COMMUNITY_FEEDBACK = "community_feedback"
    ENDORSEMENT = "endorsement"
    ACCOUNT_VERIFICATION = "account_verification"
    MANUAL_ADJUSTMENT = "manual_adjustment"


#: Largest magnitude a single award may carry, in either direction.
#:
#: The action table's own values top out at 100. The ceiling exists so that a
#: mis-typed override is a validation error rather than a leaderboard rewrite,
#: and so a negative award cannot zero somebody out in one request -- the
#: service floors the score at 0, which made deduction the cheaper attack.
MAX_POINTS_PER_AWARD = 500


class ReputationAwardRequest(BaseModel):
    """An administrator granting or deducting points.

    ``user_id`` is required. It was optional, defaulting to the caller, and
    "award points to myself" is not an operation this system should offer over
    HTTP at all -- reputation is meant to be derived from activity.
    """

    user_id: uuid.UUID = Field(
        ...,
        description="The user receiving the adjustment.",
    )
    action: ReputationAction = Field(
        ...,
        description="The activity being recognised.",
    )
    points: Optional[int] = Field(
        default=None,
        ge=-MAX_POINTS_PER_AWARD,
        le=MAX_POINTS_PER_AWARD,
        description=(
            "Override the points for this action. Omit to use the standard "
            "value from the action table. Negative values deduct."
        ),
    )
    description: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional note stored on the log entry.",
    )


class ReputationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    points: int
    description: Optional[str] = None
    granted_by_id: Optional[uuid.UUID] = Field(
        default=None,
        description=(
            "The administrator who applied this adjustment, when it came from "
            "the award endpoint. Null for entries the platform awarded itself."
        ),
    )
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
    total: int = Field(
        description=(
            "Total number of ranked users. Counts the same set the entries are "
            "drawn from -- active, non-deleted accounts -- so a client can page "
            "correctly."
        ),
    )


class TrustScoreBreakdown(BaseModel):
    collaborations_points: int = 0
    pull_requests_points: int = 0
    completed_projects_points: int = 0
    feedback_points: int = 0
    endorsements_points: int = 0
    verification_points: int = 0


class TrustScoreResponse(BaseModel):
    user_id: uuid.UUID
    reputation_score: int
    trust_score: int  # 0-100 normalized trust rating
    trust_level: str  # e.g., "Highly Trusted", "Verified Contributor", "Rising Member"
    rank_tier: str
    is_verified: bool
    breakdown: TrustScoreBreakdown


class EndorseUserRequest(BaseModel):
    target_user_id: uuid.UUID = Field(..., description="The user receiving endorsement")
    skill_or_reason: str = Field(..., max_length=100, description="Skill or reason for endorsement")
    note: Optional[str] = Field(default=None, max_length=255, description="Optional endorsement note")
