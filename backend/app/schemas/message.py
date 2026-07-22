from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict

from app.models.message import MessageType


class MessageBase(BaseModel):
    content: str
    type: MessageType = MessageType.TEXT
    parent_message_id: Optional[uuid.UUID] = None
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_size: Optional[int] = None
    mime_type: Optional[str] = None


class MessageCreate(MessageBase):
    conversation_id: uuid.UUID


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    is_edited: Optional[bool] = None
    is_deleted: Optional[bool] = None


class MessageResponse(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
