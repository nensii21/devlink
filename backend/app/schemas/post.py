from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PostAuthorResponse(BaseModel):
    id: uuid.UUID
    name: str
    handle: str
    avatar: Optional[str] = None
    verified: bool = False
    premium: bool = False


class PostCreate(BaseModel):
    content: str
    status: str = "published"  # "draft", "published", "scheduled"
    publish_at: Optional[datetime] = None
    tags: list[str] = []


class PostUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None
    publish_at: Optional[datetime] = None
    tags: Optional[list[str]] = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    author: PostAuthorResponse
    content: str
    tags: list[str] = []
    likes: int = 0
    comments: int = 0
    ago: str = "just now"
    status: str = "published"
    publish_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
