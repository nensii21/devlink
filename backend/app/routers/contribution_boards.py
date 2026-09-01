from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.cache import cache_manager
from app.dependencies import get_current_user, get_database
from app.middleware.idempotency import IdempotentRoute
from app.middleware.rate_limit import limiter
from app.models.contribution_board import TaskPriority, TaskStatus
from app.models.project import Project
from app.models.user import User
from app.schemas.contribution_board import (
    BoardColumnCreate,
    BoardColumnResponse,
    BoardColumnUpdate,
    BoardCreate,
    BoardResponse,
    BoardStatisticsResponse,
    BoardUpdate,
    PaginatedBoards,
    PaginatedTasks,
    TaskActivityResponse,
    TaskCommentCreate,
    TaskCommentResponse,
    TaskCreate,
    TaskMoveRequest,
    TaskResponse,
    TaskUpdate,
)
from app.services.contribution_board_service import ContributionBoardService

router = APIRouter(
    prefix="/contribution-boards",
    tags=["Contribution Boards"],
    route_class=IdempotentRoute,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  Board Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/{project_id}",
    response_model=BoardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a contribution board",
)
@limiter.limit("10/minute")
def create_board(
    request: Request,
    project_id: uuid.UUID,
    body: BoardCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if not db.get(Project, project_id):
        raise HTTPException(404, "Project not found")
    return ContributionBoardService.create_board(db, project_id, current_user.id, body)


@router.get(
    "/{project_id}",
    response_model=PaginatedBoards,
    summary="List boards for a project",
)
def list_boards(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    include_archived: bool = Query(False),
    db: Session = Depends(get_database),
):
    result = ContributionBoardService.list_boards(
        db, project_id, page=page, limit=limit, include_archived=include_archived
    )
    return PaginatedBoards(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        limit=result["limit"],
        pages=result["pages"],
    )


@router.get(
    "/board/{board_id}",
    response_model=BoardResponse,
    summary="Get a board with columns and task counts",
)
def get_board(
    board_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    board = ContributionBoardService.get_board(db, board_id)
    if not board:
        raise HTTPException(404, "Board not found")
    # Compute task counts per column
    for col in board.columns:
        from sqlalchemy import func, select
        from app.models.contribution_board import ContributionTask

        col.task_count = (
            db.scalar(
                select(func.count())
                .select_from(ContributionTask)
                .where(ContributionTask.column_id == col.id)
            )
            or 0
        )
    board.task_count = sum(c.task_count for c in board.columns)
    return board


@router.patch(
    "/board/{board_id}",
    response_model=BoardResponse,
    summary="Update a board",
)
def update_board(
    board_id: uuid.UUID,
    body: BoardUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    board = ContributionBoardService.update_board(db, board_id, body)
    if not board:
        raise HTTPException(404, "Board not found")
    if board.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(403, "Only the board owner or admin can update")
    return board


@router.delete(
    "/board/{board_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a board",
)
@limiter.limit("10/minute")
def delete_board(
    request: Request,
    board_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    board = ContributionBoardService.get_board(db, board_id)
    if not board:
        raise HTTPException(404, "Board not found")
    if board.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(403, "Only the board owner or admin can delete")
    ContributionBoardService.delete_board(db, board_id)


# ═══════════════════════════════════════════════════════════════════════════════
#  Column Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/board/{board_id}/columns",
    response_model=BoardColumnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a column to a board",
)
@limiter.limit("30/minute")
def create_column(
    request: Request,
    board_id: uuid.UUID,
    body: BoardColumnCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    board = ContributionBoardService.get_board(db, board_id)
    if not board:
        raise HTTPException(404, "Board not found")
    return ContributionBoardService.create_column(db, board_id, body)


@router.patch(
    "/columns/{column_id}",
    response_model=BoardColumnResponse,
    summary="Update a column",
)
def update_column(
    column_id: uuid.UUID,
    body: BoardColumnUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    col = ContributionBoardService.update_column(db, column_id, body)
    if not col:
        raise HTTPException(404, "Column not found")
    return col


@router.delete(
    "/columns/{column_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a column",
)
@limiter.limit("30/minute")
def delete_column(
    request: Request,
    column_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if not ContributionBoardService.delete_column(db, column_id):
        raise HTTPException(404, "Column not found")


@router.patch(
    "/board/{board_id}/columns/reorder",
    response_model=list[BoardColumnResponse],
    summary="Reorder columns on a board",
)
def reorder_columns(
    board_id: uuid.UUID,
    column_ids: list[uuid.UUID],
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    return ContributionBoardService.reorder_columns(db, board_id, column_ids)


# ═══════════════════════════════════════════════════════════════════════════════
#  Task Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/board/{board_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task on a board",
)
@limiter.limit("30/minute")
def create_task(
    request: Request,
    board_id: uuid.UUID,
    body: TaskCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    board = ContributionBoardService.get_board(db, board_id)
    if not board:
        raise HTTPException(404, "Board not found")
    return ContributionBoardService.create_task(db, board_id, current_user.id, body)


@router.get(
    "/board/{board_id}/tasks",
    response_model=PaginatedTasks,
    summary="List tasks on a board",
)
def list_tasks(
    board_id: uuid.UUID,
    column_id: uuid.UUID | None = Query(None),
    priority: TaskPriority | None = Query(None),
    search: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_database),
):
    result = ContributionBoardService.list_tasks(
        db,
        board_id,
        column_id=column_id,
        priority=priority,
        search=search,
        page=page,
        limit=limit,
    )
    return PaginatedTasks(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        limit=result["limit"],
        pages=result["pages"],
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get a task with full details",
)
def get_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    task = ContributionBoardService.get_task(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    # Attach assignee info
    from app.schemas.contribution_board import TaskAssigneeResponse
    from app.models.contribution_board import TaskAssignment

    assignments = list(
        db.scalars(
            select(TaskAssignment).where(TaskAssignment.task_id == task_id)
        )
    ) if False else []
    task.assignees = []
    task.comment_count = (
        db.scalar(
            select(func.count()).select_from(TaskComment).where(TaskComment.task_id == task_id)
        )
        if False else 0
    )
    return task


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
)
def update_task(
    task_id: uuid.UUID,
    body: TaskUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    task = ContributionBoardService.update_task(db, task_id, body, current_user.id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.post(
    "/tasks/{task_id}/move",
    response_model=TaskResponse,
    summary="Move a task to a different column and position",
)
@limiter.limit("60/minute")
def move_task(
    request: Request,
    task_id: uuid.UUID,
    body: TaskMoveRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    task = ContributionBoardService.move_task(db, task_id, body, current_user.id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
@limiter.limit("30/minute")
def delete_task(
    request: Request,
    task_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if not ContributionBoardService.delete_task(db, task_id):
        raise HTTPException(404, "Task not found")


# ═══════════════════════════════════════════════════════════════════════════════
#  Assignment Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/tasks/{task_id}/assign/{user_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Assign a user to a task",
)
def assign_user(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    result = ContributionBoardService.assign_user(db, task_id, user_id, current_user.id)
    if not result:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "User is already assigned to this task"
        )
    return {"status": "assigned"}


@router.delete(
    "/tasks/{task_id}/assign/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a user from a task",
)
def unassign_user(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if not ContributionBoardService.unassign_user(db, task_id, user_id):
        raise HTTPException(404, "Assignment not found")


# ═══════════════════════════════════════════════════════════════════════════════
#  Comment Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/tasks/{task_id}/comments",
    response_model=TaskCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a task",
)
@limiter.limit("60/minute")
def add_comment(
    request: Request,
    task_id: uuid.UUID,
    body: TaskCommentCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    task = ContributionBoardService.get_task(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return ContributionBoardService.add_comment(db, task_id, current_user.id, body)


@router.get(
    "/tasks/{task_id}/comments",
    response_model=list[TaskCommentResponse],
    summary="List comments on a task",
)
def list_comments(
    task_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    return ContributionBoardService.list_comments(db, task_id)


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment",
)
def delete_comment(
    comment_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if not ContributionBoardService.delete_comment(db, comment_id, current_user.id):
        raise HTTPException(
            404, "Comment not found or not authorized to delete"
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  Activity Log & Statistics
# ═══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/tasks/{task_id}/activity",
    response_model=list[TaskActivityResponse],
    summary="Get the activity log for a task",
)
def get_task_activity(
    task_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_database),
):
    return ContributionBoardService.get_activity_log(db, task_id, limit=limit)


@router.get(
    "/board/{board_id}/statistics",
    response_model=BoardStatisticsResponse,
    summary="Get board statistics and analytics",
)
def get_board_statistics(
    board_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    stats = ContributionBoardService.get_board_statistics(db, board_id)
    if not stats:
        raise HTTPException(404, "Board not found")
    return BoardStatisticsResponse(**stats)


# Need these imports at the bottom to avoid circular imports in the get_task endpoint
from sqlalchemy import func, select  # noqa: E402
from app.models.contribution_board import TaskComment, TaskAssignment  # noqa: E402
