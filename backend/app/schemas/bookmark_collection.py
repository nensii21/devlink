from __future__ import annotations

import uuid
from datetime import datetime

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.bookmark import BookmarkResponse


class BookmarkCollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class BookmarkCollectionUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class BookmarkCollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    is_default: bool
    bookmark_count: int = 0
    created_at: datetime
    updated_at: datetime


class BookmarkCollectionWithBookmarks(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    is_default: bool
    bookmarks: list[BookmarkResponse] = []
    created_at: datetime
    updated_at: datetime
