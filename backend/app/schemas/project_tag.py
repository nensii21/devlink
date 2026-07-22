from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProjectTagRequest(BaseModel):
    """Request to generate project tags."""
    title: str = Field(..., min_length=1, max_length=200, description="Project title")
    description: str = Field(..., min_length=1, description="Project description")
    tech_stack: Optional[str] = Field(None, description="Optional tech stack string")


class TagSuggestion(BaseModel):
    """A single tag suggestion with confidence score."""
    name: str = Field(..., description="Tag name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")


class ProjectTagResponse(BaseModel):
    """Response containing generated project tags."""
    tags: list[TagSuggestion] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="5-10 suggested tags with confidence scores",
    )
