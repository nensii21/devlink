from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectSearchFilters(BaseModel):
    """Represents the filterable fields on a project search."""

    q: Optional[str] = None
    stage: Optional[str] = None
    language: Optional[str] = None
    experience: Optional[str] = None
    is_remote: Optional[bool] = None
    is_paid: Optional[bool] = None
    is_open_source: Optional[bool] = None
    tags: Optional[List[str]] = None
    hiring: Optional[bool] = None


class SavedSearchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    filters: ProjectSearchFilters


class SavedSearchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    filters: Optional[ProjectSearchFilters] = None


class SavedSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    filters: dict
    created_at: datetime
    updated_at: datetime
