from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict

from app.models.conversation import ConversationType


class ConversationBase(BaseModel):
    type: ConversationType = ConversationType.DIRECT
    title: Optional[str] = None
    project_id: Optional[uuid.UUID] = None


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None
    archived: Optional[bool] = None


class ConversationResponse(ConversationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_by: uuid.UUID
    is_active: bool
    archived: bool
    created_at: datetime
    updated_at: datetime
