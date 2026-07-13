from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SkillCreate(BaseModel):
    name: str
    slug: str
    category: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    category: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    created_at: datetime
    updated_at: datetime
