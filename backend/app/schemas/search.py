from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.builder_flare import BuilderFlareResponse
from app.schemas.organization import OrganizationResponse
from app.schemas.project import ProjectResponse
from app.schemas.skill import SkillResponse
from app.schemas.user import UserResponse


class SearchResultGroups(BaseModel):
    """Container for grouped search hits across entity types."""

    users: list[UserResponse] = Field(default_factory=list)
    projects: list[ProjectResponse] = Field(default_factory=list)
    organizations: list[OrganizationResponse] = Field(default_factory=list)
    skills: list[SkillResponse] = Field(default_factory=list)
    flares: list[BuilderFlareResponse] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Unified response returned by ``GET /api/search``."""

    query: str
    types: list[str]
    total: int
    results: SearchResultGroups
