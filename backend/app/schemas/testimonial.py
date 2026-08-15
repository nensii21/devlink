from __future__ import annotations

"""
Schemas for peer testimonials (#1044).
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.testimonial import (
    MAX_BODY_LENGTH,
    MAX_FEATURED,
    MIN_BODY_LENGTH,
    TestimonialRelationship,
    TestimonialStatus,
)


class TestimonialCreate(BaseModel):
    subject_id: uuid.UUID = Field(..., description="The user this testimonial is about")
    relationship: TestimonialRelationship = Field(
        ..., description="How you worked together"
    )
    body: str = Field(
        ...,
        min_length=MIN_BODY_LENGTH,
        max_length=MAX_BODY_LENGTH,
        description=(
            f"{MIN_BODY_LENGTH}-{MAX_BODY_LENGTH} characters. The floor is deliberate: "
            "a two-word testimonial carries no information and dilutes the ones that do."
        ),
    )
    project_id: Optional[uuid.UUID] = Field(
        default=None, description="The collaboration this came out of"
    )

    @field_validator("body")
    @classmethod
    def _strip_body(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < MIN_BODY_LENGTH:
            raise ValueError(
                f"A testimonial must be at least {MIN_BODY_LENGTH} characters."
            )
        return cleaned


class TestimonialUpdate(BaseModel):
    relationship: Optional[TestimonialRelationship] = None
    body: Optional[str] = Field(
        default=None, min_length=MIN_BODY_LENGTH, max_length=MAX_BODY_LENGTH
    )
    project_id: Optional[uuid.UUID] = None

    @field_validator("body")
    @classmethod
    def _strip_body(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if len(cleaned) < MIN_BODY_LENGTH:
            raise ValueError(
                f"A testimonial must be at least {MIN_BODY_LENGTH} characters."
            )
        return cleaned


class TestimonialParty(BaseModel):
    id: uuid.UUID
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_image: Optional[str] = None
    headline: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TestimonialResponse(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    author_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None

    relationship: TestimonialRelationship
    body: str

    status: TestimonialStatus
    is_featured: bool = False
    responded_at: Optional[datetime] = None

    author: Optional[TestimonialParty] = None
    subject: Optional[TestimonialParty] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestimonialList(BaseModel):
    items: list[TestimonialResponse]
    total: int
    limit: int
    offset: int


class RelationshipCount(BaseModel):
    relationship: TestimonialRelationship
    count: int


class TestimonialSummary(BaseModel):
    user_id: uuid.UUID
    username: str

    total_approved: int = Field(
        description="Approved testimonials, the only ones shown publicly"
    )
    featured: list[TestimonialResponse] = Field(default_factory=list)
    by_relationship: list[RelationshipCount] = Field(default_factory=list)
    max_featured: int = Field(default=MAX_FEATURED)
