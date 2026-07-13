from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.builder_flare import FlareStatus


class BuilderFlareCreate(BaseModel):
    project_id: uuid.UUID
    title: str
    description: str
    role: str
    location: Optional[str] = None
    commitment: Optional[str] = None
    experience_level: Optional[str] = None
    openings: int = 1
    remote: bool = True


class BuilderFlareUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    commitment: Optional[str] = None
    experience_level: Optional[str] = None
    openings: Optional[int] = None
    status: Optional[FlareStatus] = None
    remote: Optional[bool] = None


class BuilderFlareResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    created_by: uuid.UUID
    title: str
    description: str
    role: str
    location: Optional[str] = None
    commitment: Optional[str] = None
    experience_level: Optional[str] = None
    openings: int
    applicants_count: int
    status: FlareStatus
    featured: bool
    remote: bool
    created_at: datetime
    updated_at: datetime
