from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType


class NotificationCreate(BaseModel):
    recipient_id: uuid.UUID
    sender_id: Optional[uuid.UUID] = None
    type: NotificationType
    title: str
    message: str
    action_url: Optional[str] = None
    image_url: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    message_id: Optional[uuid.UUID] = None
    application_id: Optional[uuid.UUID] = None


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recipient_id: uuid.UUID
    sender_id: Optional[uuid.UUID] = None
    type: NotificationType
    title: str
    message: str
    action_url: Optional[str] = None
    image_url: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    message_id: Optional[uuid.UUID] = None
    application_id: Optional[uuid.UUID] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
