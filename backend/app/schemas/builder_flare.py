from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict
from app.models.builder_flare import FlareStatus


class BuilderFlareBase(BaseModel):
    title: str
    description: str
    role: str
    location: Optional[str] = None
    commitment: Optional[str] = None
    experience_level: Optional[str] = None
    openings: int = 1
    status: FlareStatus = FlareStatus.OPEN
    remote: bool = True


class BuilderFlareCreate(BuilderFlareBase):
    project_id: uuid.UUID


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


class BuilderFlareResponse(BuilderFlareBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    created_by: uuid.UUID
    applicants_count: int
    featured: bool
    created_at: datetime
    updated_at: datetime
