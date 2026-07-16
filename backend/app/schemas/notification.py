from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType

# ==========================================================
# Base
# ==========================================================


class NotificationBase(BaseModel):
    recipient_id: uuid.UUID
    type: NotificationType
    title: str
    message: str

    action_url: Optional[str] = None
    image_url: Optional[str] = None

    project_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    message_id: Optional[uuid.UUID] = None
    application_id: Optional[uuid.UUID] = None


# ==========================================================
# Create
# ==========================================================


class NotificationCreate(NotificationBase):
    pass


# ==========================================================
# Update
# ==========================================================


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    title: Optional[str] = None
    message: Optional[str] = None
    action_url: Optional[str] = None
    image_url: Optional[str] = None


# ==========================================================
# Response
# ==========================================================


class NotificationResponse(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender_id: Optional[uuid.UUID] = None

    is_read: bool
    read_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime
