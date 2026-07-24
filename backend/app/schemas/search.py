from __future__ import annotations

import uuid
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


# ---------------------------------------------------------------------------
# Autocomplete (lightweight suggestion response for the Topbar typeahead)
# ---------------------------------------------------------------------------


class SearchSuggestionUser(BaseModel):
    """Lightweight user shape for autocomplete suggestions."""

    id: uuid.UUID
    name: str
    username: str
    role: Optional[str] = None
    profile_image: Optional[str] = None


class SearchSuggestionProject(BaseModel):
    """Lightweight project shape for autocomplete suggestions."""

    id: uuid.UUID
    title: str
    icon: Optional[str] = None


class SearchSuggestionSkill(BaseModel):
    """Lightweight skill shape for autocomplete suggestions."""

    id: uuid.UUID
    name: str


class SearchAutocompleteResponse(BaseModel):
    """Grouped autocomplete response returned by ``GET /api/search/autocomplete``."""

    users: list[SearchSuggestionUser] = Field(default_factory=list)
    projects: list[SearchSuggestionProject] = Field(default_factory=list)
    skills: list[SearchSuggestionSkill] = Field(default_factory=list)
