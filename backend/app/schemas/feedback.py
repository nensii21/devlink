from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    category: str = Field(
        ..., description="Bug Report, Feature Request, UI Feedback, Performance, Other"
    )
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)


class FeedbackStatusUpdate(BaseModel):
    status: str = Field(..., description="open, in_review, planned, resolved, closed")
    admin_response: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: str
    title: str
    description: str
    status: str
    admin_response: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
