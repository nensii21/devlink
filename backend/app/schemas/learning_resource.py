import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


VALID_CATEGORIES = ("tutorial", "documentation", "video", "guide", "tool", "article")
VALID_DIFFICULTIES = ("beginner", "intermediate", "advanced")


class LearningResourceCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    url: str = Field(..., min_length=5, max_length=500)
    description: Optional[str] = None
    category: str = Field(default="tutorial", max_length=50)
    language: Optional[str] = None
    difficulty: str = Field(default="intermediate", max_length=20)
    is_external: bool = True


class LearningResourceUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    url: Optional[str] = Field(default=None, min_length=5, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = Field(default=None, max_length=50)
    language: Optional[str] = None
    difficulty: Optional[str] = Field(default=None, max_length=20)
    is_pinned: Optional[bool] = None


class VoteRequest(BaseModel):
    value: int = Field(..., ge=-1, le=1)


class LearningResourceResponse(BaseModel):
    id: str
    project_id: uuid.UUID
    author_id: uuid.UUID
    author_name: Optional[str] = None
    title: str
    url: str
    description: Optional[str] = None
    category: str
    language: Optional[str] = None
    difficulty: str
    is_external: bool
    is_pinned: bool
    view_count: int
    vote_score: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LearningResourceBrief(BaseModel):
    id: str
    title: str
    url: str
    category: str
    difficulty: str
    vote_score: int
    is_pinned: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LearningResourceListResponse(BaseModel):
    items: List[LearningResourceResponse]
    total: int
    page: int
    limit: int
    pages: int


class LearningResourceStatsResponse(BaseModel):
    project_id: uuid.UUID
    total_resources: int
    by_category: dict
    by_difficulty: dict
    total_votes: int
    top_resources: List[LearningResourceBrief]
