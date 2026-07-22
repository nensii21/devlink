from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict

from app.models.issue import IssueDifficulty, IssuePriority, IssueStatus


class IssueBase(BaseModel):
    title: str
    description: str
    priority: IssuePriority = IssuePriority.MEDIUM
    labels: Optional[str] = None


class IssueCreate(IssueBase):
    project_id: uuid.UUID


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    labels: Optional[str] = None


class DifficultyOverride(BaseModel):
    difficulty: IssueDifficulty


class DifficultyEstimateResponse(BaseModel):
    difficulty: IssueDifficulty
    confidence: float
    reasoning: str


class IssueResponse(IssueBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    author_id: uuid.UUID
    status: IssueStatus
    difficulty: Optional[IssueDifficulty] = None
    difficulty_confidence: Optional[float] = None
    difficulty_manual_override: bool = False
    created_at: datetime
    updated_at: datetime
