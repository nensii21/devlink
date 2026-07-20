"""
Pydantic schemas for the AI-Powered Builder Recommendation System.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Score Breakdown
# ==========================================================


class ScoreBreakdown(BaseModel):
    """Per-factor contribution to the final recommendation score."""

    skills: float = Field(
        ..., description="Skill overlap between builder and project/seed profile."
    )
    interests: float = Field(
        ..., description="Interest overlap (bio/headline keywords)."
    )
    experience: float = Field(
        ..., description="Experience level match vs. project requirement."
    )
    technologies: float = Field(
        ..., description="Preferred-technology overlap with project tech stack."
    )
    availability: float = Field(
        ..., description="Builder availability (open_to_work) signal."
    )
    contributions: float = Field(
        ..., description="Previous-contribution track-record signal."
    )
    network: float = Field(
        ..., description="Social-graph boost (mutual followers)."
    )


# ==========================================================
# Recommended Builder
# ==========================================================


class RecommendedBuilder(BaseModel):
    """A single builder recommendation entry."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    username: str
    first_name: str
    last_name: str
    headline: Optional[str] = None
    profile_image: Optional[str] = None
    role: Optional[str] = None
    experience_level: Optional[str] = None
    open_to_work: bool = True
    location: Optional[str] = None

    matched_skills: list[str] = Field(
        default_factory=list,
        description="Normalized names of skills that matched the requirement.",
    )
    matched_technologies: list[str] = Field(
        default_factory=list,
        description="Project tech-stack items matched by the builder.",
    )
    contribution_count: int = Field(
        0, description="Total prior contributions (accepted applications + projects)."
    )
    score: float = Field(..., description="Final weighted score (0.0 - 1.0).")
    score_breakdown: ScoreBreakdown


# ==========================================================
# Recommendation Response
# ==========================================================


class RecommendationResponse(BaseModel):
    """Ranked recommendation list returned by the API."""

    query_context: str = Field(
        ..., description="What the recommendations were generated for."
    )
    total: int
    limit: int
    results: list[RecommendedBuilder]


# ==========================================================
# Weights (extensibility hook for future AI models)
# ==========================================================


class RecommendationWeights(BaseModel):
    """
    Publicly documented scoring weights.

    These weights are intentionally exposed so that they can be overridden
    via configuration in the future (e.g. learned by an ML model or
    tuned per-tenant). All weights must sum to 1.0.
    """

    skills: float = 0.30
    interests: float = 0.10
    experience: float = 0.15
    technologies: float = 0.20
    availability: float = 0.10
    contributions: float = 0.10
    network: float = 0.05


# ==========================================================
# Project Context (when recommending builders for a project)
# ==========================================================


class ProjectContext(BaseModel):
    """Denormalized project fields used by the matching engine."""

    project_id: uuid.UUID
    title: str
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    required_skill_ids: list[uuid.UUID] = Field(default_factory=list)
    minimum_experience: int = 0
    owner_id: uuid.UUID
