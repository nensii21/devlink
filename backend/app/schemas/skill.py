from __future__ import annotations

# pyrefly: ignore [missing-import]
import uuid
from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.skill_names import clean_skill_name


class SkillBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str
    category: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = clean_skill_name(value)
        if not cleaned:
            raise ValueError("Skill name cannot be empty or whitespace-only.")
        return cleaned


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    slug: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = clean_skill_name(value)
        if not cleaned:
            raise ValueError("Skill name cannot be empty or whitespace-only.")
        return cleaned


class SkillResponse(SkillBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
