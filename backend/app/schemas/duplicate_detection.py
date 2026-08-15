from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DuplicateProjectCheckRequest(BaseModel):
    title: str = Field(
        ..., min_length=2, max_length=200, description="Project title to check"
    )
    description: Optional[str] = Field(
        default="", description="Project description or tagline"
    )
    tags: Optional[list[str]] = Field(
        default_factory=list, description="Associated skills, tech stack, or tags"
    )
    category: Optional[str] = Field(
        default=None, description="Optional project category"
    )
    similarity_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Similarity score threshold (0.0 - 1.0)",
    )
    limit: int = Field(
        default=5, ge=1, le=20, description="Maximum candidate matches to return"
    )


class SuggestedProjectMatch(BaseModel):
    project_id: uuid.UUID
    title: str
    slug: str
    description: str
    similarity_score: float = Field(
        ..., description="Calculated similarity score (0.0 to 1.0)"
    )
    confidence_score: float = Field(
        ..., description="Duplicate confidence score percentage (0.0 to 100.0)"
    )
    is_duplicate: bool = Field(
        ..., description="True if similarity_score >= similarity_threshold"
    )
    match_reasons: list[str] = Field(
        default_factory=list, description="Human-readable breakdown of match factors"
    )

    model_config = ConfigDict(from_attributes=True)


class DuplicateProjectCheckResponse(BaseModel):
    has_duplicates: bool = Field(
        ..., description="True if any suggested match exceeds the similarity threshold"
    )
    max_similarity_score: float = Field(
        ..., description="Highest similarity score among matches"
    )
    suggested_projects: list[SuggestedProjectMatch] = Field(
        default_factory=list, description="List of matching candidate projects"
    )
    threshold_used: float = Field(
        ..., description="Similarity threshold configured for check"
    )
    manual_override_allowed: bool = Field(
        default=True,
        description="Indicates user can bypass warning via allow_duplicate=True",
    )
