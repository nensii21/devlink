from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.message import MessageType


class MessageCreate(BaseModel):
    conversation_id: uuid.UUID
    content: str
    type: MessageType = MessageType.TEXT
    parent_message_id: Optional[uuid.UUID] = None
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_size: Optional[int] = None
    mime_type: Optional[str] = None


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    is_edited: Optional[bool] = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    parent_message_id: Optional[uuid.UUID] = None
    type: MessageType
    content: str
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_size: Optional[int] = None
    mime_type: Optional[str] = None
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
