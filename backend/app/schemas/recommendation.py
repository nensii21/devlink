from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

# ==========================================================
# Lightweight Project Response for Recommendations
# ==========================================================


class RecommendationProject(BaseModel):
    """
    Simplified project representation for recommendation results.
    Includes key fields for display without heavy nesting.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    slug: str
    tagline: str | None = None
    description: str
    stage: str
    tech_stack: str | None = None
    repository_url: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    team_size: int
    max_team_size: int
    hiring: bool
    stars: int
    views: int
    created_at: datetime
    updated_at: datetime


# ==========================================================
# Single Recommendation Item
# ==========================================================


class ProjectRecommendation(BaseModel):
    """
    A single project recommendation with score and breakdown.
    """

    project: RecommendationProject
    score: float
    skill_match_count: int
    total_skills: int
    is_previous_contribution: bool
    is_bookmarked: bool
    is_org_related: bool


# ==========================================================
# Recommendation List Response
# ==========================================================


class RecommendationList(BaseModel):
    """
    Paginated list of project recommendations.
    """

    recommendations: list[ProjectRecommendation]
    total: int
