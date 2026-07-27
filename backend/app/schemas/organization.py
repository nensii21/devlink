from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.organization import OrganizationType

# ==========================================================
# Base Organization Schema
# ==========================================================


class OrganizationBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )
    slug: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Unique URL slug. Generated automatically from name if omitted.",
    )
    description: Optional[str] = None
    organization_type: OrganizationType = OrganizationType.STARTUP
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    location: Optional[str] = Field(default=None, max_length=200)
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    hiring: bool = False


# ==========================================================
# Create Organization
# ==========================================================


class OrganizationCreate(OrganizationBase):
    pass


# ==========================================================
# Update Organization
# ==========================================================


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    organization_type: Optional[OrganizationType] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    location: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    hiring: Optional[bool] = None
    active: Optional[bool] = None


# ==========================================================
# Slug Check Response Schema
# ==========================================================


class SlugCheckResponse(BaseModel):
    slug: str
    available: bool


# ==========================================================
# Organization Response
# ==========================================================


class OrganizationResponse(OrganizationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    slug: str
    members_count: int
    projects_count: int
    followers_count: int
    verified: bool
    active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[uuid.UUID] = None
