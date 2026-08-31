"""Pydantic schemas for the project onboarding checklist feature."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.onboarding_checklist import ChecklistItemType


# ── Checklist ────────────────────────────────────────────────────────


class ChecklistCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_default: bool = False


class ChecklistUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_archived: Optional[bool] = None


class ChecklistResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    created_by_id: uuid.UUID
    title: str
    description: Optional[str] = None
    is_default: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChecklistWithItems(ChecklistResponse):
    items: List[OnboardingItemResponse] = Field(default_factory=list)
    item_count: int = 0
    required_count: int = 0


class ChecklistListResponse(BaseModel):
    items: List[ChecklistResponse]
    total: int


# ── Checklist Items ──────────────────────────────────────────────────


class OnboardingItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    item_type: ChecklistItemType = ChecklistItemType.TASK
    order: int = 0
    is_required: bool = True
    resource_url: Optional[str] = None


class OnboardingItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    item_type: Optional[ChecklistItemType] = None
    order: Optional[int] = None
    is_required: Optional[bool] = None
    resource_url: Optional[str] = None


class OnboardingItemResponse(BaseModel):
    id: uuid.UUID
    checklist_id: uuid.UUID
    title: str
    description: Optional[str] = None
    item_type: ChecklistItemType
    order: int
    is_required: bool
    resource_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Assignments ──────────────────────────────────────────────────────


class AssignmentCreate(BaseModel):
    user_id: uuid.UUID


class AssignmentBatchCreate(BaseModel):
    user_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=50)


class AssignmentResponse(BaseModel):
    id: uuid.UUID
    checklist_id: uuid.UUID
    user_id: uuid.UUID
    assigned_by_id: uuid.UUID
    is_completed: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentWithProgress(AssignmentResponse):
    total_items: int = 0
    completed_items: int = 0
    progress_percent: float = 0.0
    required_remaining: int = 0


class AssignmentListResponse(BaseModel):
    items: List[AssignmentResponse]
    total: int


# ── Item Completion ──────────────────────────────────────────────────


class ItemCompletionCreate(BaseModel):
    notes: Optional[str] = None


class ItemCompletionResponse(BaseModel):
    id: uuid.UUID
    assignment_id: uuid.UUID
    item_id: uuid.UUID
    completed_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ── Statistics ───────────────────────────────────────────────────────


class ChecklistStats(BaseModel):
    checklist_id: uuid.UUID
    total_assigned: int
    completed_count: int
    in_progress_count: int
    not_started_count: int
    average_completion_percent: float


class ProjectOnboardingStats(BaseModel):
    project_id: uuid.UUID
    total_checklists: int
    total_assignments: int
    completed_assignments: int
    average_progress: float
    most_popular_checklist: Optional[str] = None
