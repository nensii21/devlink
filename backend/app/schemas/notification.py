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
    delivered_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime


# ==========================================================
# Notification Preferences Schemas (#586)
# ==========================================================


class NotificationPreferenceResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID

    # Global Channel Toggles
    email_enabled: bool = True
    websocket_enabled: bool = True
    database_enabled: bool = True

    # Core Event Categories
    messages: bool = True
    team_invitations: bool = True
    project_updates: bool = True
    mentions: bool = True
    system_announcements: bool = True

    # Per-Category Email Delivery Preferences
    email_messages: bool = True
    email_team_invitations: bool = True
    email_project_updates: bool = True
    email_mentions: bool = True
    email_system_announcements: bool = True

    # Legacy & Auxiliary Toggles
    invitations: bool = True
    role_changes: bool = True
    marketing_emails: bool = False
    system_alerts: bool = True

    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceUpdate(BaseModel):
    # Global Channel Toggles
    email_enabled: Optional[bool] = None
    websocket_enabled: Optional[bool] = None
    database_enabled: Optional[bool] = None

    # Core Event Categories
    messages: Optional[bool] = None
    team_invitations: Optional[bool] = None
    project_updates: Optional[bool] = None
    mentions: Optional[bool] = None
    system_announcements: Optional[bool] = None

    # Per-Category Email Delivery Preferences
    email_messages: Optional[bool] = None
    email_team_invitations: Optional[bool] = None
    email_project_updates: Optional[bool] = None
    email_mentions: Optional[bool] = None
    email_system_announcements: Optional[bool] = None

    # Legacy & Auxiliary Toggles
    invitations: Optional[bool] = None
    role_changes: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    system_alerts: Optional[bool] = None
