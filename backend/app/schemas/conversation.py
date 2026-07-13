from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.conversation import ConversationType


class ConversationCreate(BaseModel):
    type: ConversationType = ConversationType.DIRECT
    title: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    created_by: uuid.UUID


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None
    archived: Optional[bool] = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: ConversationType
    title: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    created_by: uuid.UUID
    is_active: bool
    archived: bool
    created_at: datetime
    updated_at: datetime
