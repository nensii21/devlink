import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserResponse
from app.schemas.project import ProjectResponse

class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str
    category: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None

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
    openings: int = 1
    applicants_count: int = 0
    status: str
    featured: bool
    remote: bool
    created_at: datetime
    updated_at: datetime

class SearchResult(BaseModel):
    users: list[UserResponse] = []
    projects: list[ProjectResponse] = []
    skills: list[SkillResponse] = []
    flares: list[BuilderFlareResponse] = []

