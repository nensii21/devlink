from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.issue import IssuePriority, IssueStatus

# ------------------------------------------------------------------
# Issue Schemas
# ------------------------------------------------------------------


class IssueBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    priority: IssuePriority = IssuePriority.MEDIUM
    labels: Optional[str] = None


class IssueCreate(IssueBase):
    pass


class IssueUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    labels: Optional[str] = None


class IssueAuthorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    full_name: Optional[str] = None
    avatar: Optional[str] = None


class IssueResponse(IssueBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    author_id: uuid.UUID
    status: IssueStatus
    is_duplicate_checked: bool
    created_at: datetime
    updated_at: datetime


class IssueDetailResponse(IssueResponse):
    author: Optional[IssueAuthorResponse] = None
    duplicate_suggestions: list[DuplicateSuggestionResponse] = []


# ------------------------------------------------------------------
# Duplicate Detection Schemas
# ------------------------------------------------------------------


class DuplicateCheckRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    threshold: float = Field(
        0.75,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score to consider as duplicate",
    )


class DuplicateSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_issue_id: uuid.UUID
    duplicate_issue_id: uuid.UUID
    similarity_score: float
    created_at: datetime
    issue: Optional[IssueResponse] = None


class DuplicateCheckResponse(BaseModel):
    has_duplicates: bool
    suggestions: list[DuplicateSuggestionResponse]
    checked_count: int
    threshold: float


# Fix forward reference
IssueDetailResponse.model_rebuild()
