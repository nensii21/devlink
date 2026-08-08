from __future__ import annotations

import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.user_skill import SkillLevel


class SkillMatrixEntry(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(default="Languages", description="Skill category: Languages, Frameworks, Databases, Cloud, DevOps, AI/ML, Design")
    level: SkillLevel = Field(default=SkillLevel.BEGINNER)
    years_of_experience: int = Field(default=0, ge=0, le=50)


class SkillMatrixResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skills_by_category: dict[str, list[dict]]
    total_skills: int


class SkillMatrixUpdateRequest(BaseModel):
    skills: list[SkillMatrixEntry]
