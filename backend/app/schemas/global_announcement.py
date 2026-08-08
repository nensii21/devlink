from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.global_announcement import AnnouncementSeverity, TargetAudience


class GlobalAnnouncementBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    severity: AnnouncementSeverity = Field(default=AnnouncementSeverity.INFO)
    target_audience: TargetAudience = Field(default=TargetAudience.ALL)
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    is_active: bool = Field(default=True)


class GlobalAnnouncementCreate(GlobalAnnouncementBase):
    pass


class GlobalAnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1)
    severity: Optional[AnnouncementSeverity] = None
    target_audience: Optional[TargetAudience] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class GlobalAnnouncementResponse(GlobalAnnouncementBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime
