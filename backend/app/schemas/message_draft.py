from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class MessageDraftSaveRequest(BaseModel):
    conversation_id: uuid.UUID
    content: str = Field(..., max_length=10000)


class MessageDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    conversation_id: uuid.UUID
    content: str
    updated_at: datetime
