from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict


class BookmarkTargetType(str, Enum):
    PROJECT = "project"
    FLARE = "flare"


class BookmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    target_type: BookmarkTargetType
    target_id: uuid.UUID
    created_at: datetime
