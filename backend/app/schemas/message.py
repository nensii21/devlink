from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, model_validator

from app.models.message import MessageType


class MessageBase(BaseModel):
    content: str
    type: MessageType = MessageType.TEXT
    parent_message_id: Optional[uuid.UUID] = None
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_size: Optional[int] = None
    mime_type: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def map_message_to_content(cls, data: any) -> any:
        if isinstance(data, dict):
            if "message" in data and "content" not in data:
                data["content"] = data["message"]
        return data


class MessageCreate(MessageBase):
    conversation_id: uuid.UUID


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    is_edited: Optional[bool] = None
    is_deleted: Optional[bool] = None


class ReactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    emoji: str
    created_at: datetime


class ReactionCreate(BaseModel):
    emoji: str


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
    read_at: Optional[datetime] = None
    reactions: list[ReactionResponse] = []


class BulkReadRequest(BaseModel):
    message_ids: Optional[list[uuid.UUID]] = None
    conversation_id: Optional[uuid.UUID] = None


class BulkReadResponse(BaseModel):
    updated_count: int
    read_at: datetime

