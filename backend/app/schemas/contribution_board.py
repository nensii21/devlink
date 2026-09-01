from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.contribution_board import TaskPriority, TaskStatus


# ── Board Schemas ──────────────────────────────────────────────────────────────


class BoardColumnCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    position: int = 0
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    wip_limit: Optional[int] = Field(default=None, ge=0, le=1000)


class BoardColumnUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    position: Optional[int] = Field(default=None, ge=0)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    wip_limit: Optional[int] = Field(default=None, ge=0, le=1000)


class BoardColumnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    board_id: uuid.UUID
    title: str
    position: int
    color: Optional[str] = None
    wip_limit: Optional[int] = None
    task_count: int = 0
    created_at: datetime


class BoardCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    columns: list[BoardColumnCreate] = Field(
        default_factory=lambda: [
            BoardColumnCreate(title="Backlog", position=0, color="#6b7280"),
            BoardColumnCreate(title="To Do", position=1, color="#3b82f6"),
            BoardColumnCreate(title="In Progress", position=2, color="#f59e0b"),
            BoardColumnCreate(title="In Review", position=3, color="#8b5cf6"),
            BoardColumnCreate(title="Done", position=4, color="#10b981"),
        ]
    )


class BoardUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = None
    is_archived: Optional[bool] = None


class BoardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: Optional[str] = None
    is_archived: bool
    columns: list[BoardColumnResponse] = []
    task_count: int = 0
    created_at: datetime
    updated_at: datetime


class BoardBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: Optional[str] = None
    is_archived: bool
    task_count: int = 0
    created_at: datetime


class PaginatedBoards(BaseModel):
    items: list[BoardBrief]
    total: int
    page: int
    limit: int
    pages: int


# ── Task Schemas ───────────────────────────────────────────────────────────────


class TaskAssigneeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    assigned_at: datetime


class TaskCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_comment_id: Optional[uuid.UUID] = None


class TaskCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    task_id: uuid.UUID
    author_id: uuid.UUID
    author_name: Optional[str] = None
    content: str
    parent_comment_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class TaskActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    task_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    actor_name: Optional[str] = None
    action: str
    from_value: Optional[str] = None
    to_value: Optional[str] = None
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    column_id: uuid.UUID
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(default=None, ge=0, le=1000)
    labels: Optional[str] = None
    assignee_ids: list[uuid.UUID] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description: Optional[str] = None
    column_id: Optional[uuid.UUID] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    position: Optional[int] = Field(default=None, ge=0)
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(default=None, ge=0, le=1000)
    labels: Optional[str] = None


class TaskMoveRequest(BaseModel):
    column_id: uuid.UUID
    position: int = Field(..., ge=0)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    board_id: uuid.UUID
    column_id: uuid.UUID
    creator_id: uuid.UUID
    title: str
    description: Optional[str] = None
    priority: TaskPriority
    status: TaskStatus
    position: int
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = None
    labels: Optional[str] = None
    assignees: list[TaskAssigneeResponse] = []
    comment_count: int = 0
    created_at: datetime
    updated_at: datetime


class TaskBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    column_id: uuid.UUID
    title: str
    priority: TaskPriority
    status: TaskStatus
    position: int
    labels: Optional[str] = None
    assignee_count: int = 0
    due_date: Optional[datetime] = None
    created_at: datetime


class PaginatedTasks(BaseModel):
    items: list[TaskBrief]
    total: int
    page: int
    limit: int
    pages: int


class BoardStatisticsResponse(BaseModel):
    board_id: uuid.UUID
    total_tasks: int
    open_tasks: int
    in_progress_tasks: int
    in_review_tasks: int
    done_tasks: int
    archived_tasks: int
    overdue_tasks: int
    tasks_by_priority: dict[str, int]
    tasks_by_column: list[dict]
    avg_estimated_hours: Optional[float] = None
    contributor_count: int
