"""
Pydantic schemas for the AI Tech Stack Recommendation feature.
"""

from __future__ import annotations

from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class TechStackRequest(BaseModel):
    """Request body for AI tech stack recommendation."""

    project_idea: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="A brief description of the project idea.",
        examples=["Food Delivery Platform"],
    )


class TechStackRecommendation(BaseModel):
    """A single recommended technology with justification."""

    name: str = Field(
        ...,
        description="Name of the recommended technology.",
    )
    category: str = Field(
        ...,
        description="Category: frontend, backend, database, cache, devops, etc.",
    )
    reason: str = Field(
        ...,
        description="Why this technology is recommended for the given project idea.",
    )


class TechStackResponse(BaseModel):
    """AI-generated tech stack recommendation response."""

    project_idea: str
    recommendations: list[TechStackRecommendation] = Field(
        ...,
        description="Ranked list of recommended technologies.",
    )
    summary: Optional[str] = Field(
        None,
        description="Brief explanation of the overall stack strategy.",
    )
