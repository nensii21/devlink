from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.notification import NotificationType


class DigestProject(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    created_at: datetime


class DigestNotification(BaseModel):
    type: NotificationType
    title: str
    message: str
    action_url: str | None = None
    created_at: datetime


class DailyDigestResponse(BaseModel):
    generated_at: datetime
    new_projects: list[DigestProject]
    project_invitations: list[DigestNotification]
    messages: list[DigestNotification]
    notifications: list[DigestNotification]
