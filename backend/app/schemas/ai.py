from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectDescriptionGenerateRequest(BaseModel):
    """Request body for AI project description generation."""

    prompt: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="A short prompt or idea to generate the project description from.",
        examples=["A real-time chat application for developers"],
    )


class ProjectDescriptionGenerateResponse(BaseModel):
    """Response containing the AI-generated project description."""

    description: str = Field(
        ...,
        description="The AI-generated project description.",
    )
