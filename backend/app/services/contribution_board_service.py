from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import Session, joinedload

from app.models.contribution_board import (
    BoardColumn,
    ContributionBoard,
    ContributionTask,
    TaskActivity,
    TaskAssignment,
    TaskComment,
    TaskPriority,
    TaskStatus,
)
from app.schemas.contribution_board import (
    BoardColumnCreate,
    BoardColumnUpdate,
    BoardCreate,
    BoardUpdate,
    TaskCommentCreate,
    TaskCreate,
    TaskMoveRequest,
    TaskUpdate,
)


class ContributionBoardService:
    """Business logic for the contribution board feature."""

    # ── Board CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def create_board(
        db: Session, project_id: uuid.UUID, owner_id: uuid.UUID, payload: BoardCreate
    ) -> ContributionBoard:
        board = ContributionBoard(
            project_id=project_id,
            owner_id=owner_id,
            title=payload.title,
            description=payload.description,
        )
        db.add(board)
        db.flush()

        for i, col in enumerate(payload.columns):
            db.add(
                BoardColumn(
                    board_id=board.id,
                    title=col.title,
                    position=col.position if col.position else i,
                    color=col.color,
                    wip_limit=col.wip_limit,
                )
            )
        db.flush()
        db.refresh(board)
        return board

    @staticmethod
    def get_board(db: Session, board_id: uuid.UUID) -> ContributionBoard | None:
        board = db.get(ContributionBoard, board_id)
        if not board:
            return None
        # Eager-load columns with task counts
        db.refresh(board, ["columns"])
        return board

    @staticmethod
    def list_boards(
        db: Session,
        project_id: uuid.UUID,
        *,
        page: int = 1,
        limit: int = 20,
        include_archived: bool = False,
    ) -> dict:
        filters = [ContributionBoard.project_id == project_id]
        if not include_archived:
            filters.append(ContributionBoard.is_archived == False)

        count_q = (
            select(func.count()).select_from(ContributionBoard).where(*filters)
        )
        total = db.scalar(count_q) or 0

        q = (
            select(ContributionBoard)
            .where(*filters)
            .order_by(ContributionBoard.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        boards = list(db.scalars(q))

        # Attach task counts
        for b in boards:
            b.task_count = (
                db.scalar(
                    select(func.count())
                    .select_from(ContributionTask)
                    .where(ContributionTask.board_id == b.id)
                )
                or 0
            )

        pages = max(1, math.ceil(total / limit))
        return {
            "items": boards,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    @staticmethod
    def update_board(
        db: Session, board_id: uuid.UUID, payload: BoardUpdate
    ) -> ContributionBoard | None:
        board = db.get(ContributionBoard, board_id)
        if not board:
            return None
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(board, k, v)
        db.flush()
        db.refresh(board)
        return board

    @staticmethod
    def delete_board(db: Session, board_id: uuid.UUID) -> bool:
        board = db.get(ContributionBoard, board_id)
        if not board:
            return False
        db.delete(board)
        db.flush()
        return True

    # ── Column CRUD ────────────────────────────────────────────────────────

    @staticmethod
    def create_column(
        db: Session, board_id: uuid.UUID, payload: BoardColumnCreate
    ) -> BoardColumn:
        # Auto-assign position if not provided
        max_pos = (
            db.scalar(
                select(func.max(BoardColumn.position)).where(
                    BoardColumn.board_id == board_id
                )
            )
            or 0
        )
        col = BoardColumn(
            board_id=board_id,
            title=payload.title,
            position=payload.position if payload.position else max_pos + 1,
            color=payload.color,
            wip_limit=payload.wip_limit,
        )
        db.add(col)
        db.flush()
        db.refresh(col)
        return col

    @staticmethod
    def update_column(
        db: Session, column_id: uuid.UUID, payload: BoardColumnUpdate
    ) -> BoardColumn | None:
        col = db.get(BoardColumn, column_id)
        if not col:
            return None
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(col, k, v)
        db.flush()
        db.refresh(col)
        return col

    @staticmethod
    def delete_column(db: Session, column_id: uuid.UUID) -> bool:
        col = db.get(BoardColumn, column_id)
        if not col:
            return False
        db.delete(col)
        db.flush()
        return True

    @staticmethod
    def reorder_columns(
        db: Session, board_id: uuid.UUID, column_ids: list[uuid.UUID]
    ) -> list[BoardColumn]:
        """Reorder columns based on the order of column_ids."""
        for idx, col_id in enumerate(column_ids):
            col = db.get(BoardColumn, col_id)
            if col and col.board_id == board_id:
                col.position = idx
        db.flush()
        return list(
            db.scalars(
                select(BoardColumn)
                .where(BoardColumn.board_id == board_id)
                .order_by(BoardColumn.position)
            )
        )

    # ── Task CRUD ──────────────────────────────────────────────────────────

    @staticmethod
    def create_task(
        db: Session, board_id: uuid.UUID, creator_id: uuid.UUID, payload: TaskCreate
    ) -> ContributionTask:
        # Auto-assign position within column
        max_pos = (
            db.scalar(
                select(func.max(ContributionTask.position)).where(
                    and_(
                        ContributionTask.board_id == board_id,
                        ContributionTask.column_id == payload.column_id,
                    )
                )
            )
            or 0
        )

        task = ContributionTask(
            board_id=board_id,
            column_id=payload.column_id,
            creator_id=creator_id,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            status=TaskStatus.OPEN,
            position=max_pos + 1,
            due_date=payload.due_date,
            estimated_hours=payload.estimated_hours,
            labels=payload.labels,
        )
        db.add(task)
        db.flush()

        # Assign users
        for uid in payload.assignee_ids:
            db.add(
                TaskAssignment(
                    task_id=task.id, user_id=uid, assigned_by_id=creator_id
                )
            )

        # Log creation
        db.add(
            TaskActivity(
                task_id=task.id,
                actor_id=creator_id,
                action="created",
                to_value=task.title,
            )
        )
        db.flush()
        db.refresh(task)
        return task

    @staticmethod
    def get_task(db: Session, task_id: uuid.UUID) -> ContributionTask | None:
        return db.get(ContributionTask, task_id)

    @staticmethod
    def list_tasks(
        db: Session,
        board_id: uuid.UUID,
        *,
        column_id: uuid.UUID | None = None,
        priority: TaskPriority | None = None,
        status: TaskStatus | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> dict:
        filters = [ContributionTask.board_id == board_id]
        if column_id:
            filters.append(ContributionTask.column_id == column_id)
        if priority:
            filters.append(ContributionTask.priority == priority)
        if status:
            filters.append(ContributionTask.status == status)
        if search:
            filters.append(
                ContributionTask.title.ilike(f"%{search}%")
            )

        count_q = (
            select(func.count()).select_from(ContributionTask).where(*filters)
        )
        total = db.scalar(count_q) or 0

        q = (
            select(ContributionTask)
            .where(*filters)
            .order_by(ContributionTask.position)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        tasks = list(db.scalars(q))

        # Attach assignee counts
        for t in tasks:
            t.assignee_count = (
                db.scalar(
                    select(func.count())
                    .select_from(TaskAssignment)
                    .where(TaskAssignment.task_id == t.id)
                )
                or 0
            )

        pages = max(1, math.ceil(total / limit))
        return {
            "items": tasks,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    @staticmethod
    def update_task(
        db: Session, task_id: uuid.UUID, payload: TaskUpdate, actor_id: uuid.UUID
    ) -> ContributionTask | None:
        task = db.get(ContributionTask, task_id)
        if not task:
            return None

        changes = payload.model_dump(exclude_unset=True)
        for k, v in changes.items():
            old_val = getattr(task, k)
            if old_val != v:
                db.add(
                    TaskActivity(
                        task_id=task.id,
                        actor_id=actor_id,
                        action=f"updated_{k}",
                        from_value=str(old_val) if old_val else None,
                        to_value=str(v) if v else None,
                    )
                )
            setattr(task, k, v)

        db.flush()
        db.refresh(task)
        return task

    @staticmethod
    def move_task(
        db: Session,
        task_id: uuid.UUID,
        payload: TaskMoveRequest,
        actor_id: uuid.UUID,
    ) -> ContributionTask | None:
        task = db.get(ContributionTask, task_id)
        if not task:
            return None

        old_column_id = task.column_id
        old_position = task.position

        # Shift tasks in the target column to make room
        db.execute(
            update(ContributionTask)
            .where(
                and_(
                    ContributionTask.board_id == task.board_id,
                    ContributionTask.column_id == payload.column_id,
                    ContributionTask.position >= payload.position,
                    ContributionTask.id != task_id,
                )
            )
            .values(position=ContributionTask.position + 1)
        )

        # Update moved task
        task.column_id = payload.column_id
        task.position = payload.position

        # Auto-update status based on column
        col = db.get(BoardColumn, payload.column_id)
        if col:
            status_map = {
                "backlog": TaskStatus.OPEN,
                "to do": TaskStatus.OPEN,
                "in progress": TaskStatus.IN_PROGRESS,
                "in review": TaskStatus.IN_REVIEW,
                "done": TaskStatus.DONE,
                "completed": TaskStatus.DONE,
            }
            mapped_status = status_map.get(col.title.lower())
            if mapped_status:
                task.status = mapped_status

        # Log the move
        db.add(
            TaskActivity(
                task_id=task.id,
                actor_id=actor_id,
                action="moved",
                from_value=f"{old_column_id}:{old_position}",
                to_value=f"{payload.column_id}:{payload.position}",
            )
        )

        db.flush()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: uuid.UUID) -> bool:
        task = db.get(ContributionTask, task_id)
        if not task:
            return False
        db.delete(task)
        db.flush()
        return True

    # ── Assignment ─────────────────────────────────────────────────────────

    @staticmethod
    def assign_user(
        db: Session, task_id: uuid.UUID, user_id: uuid.UUID, assigned_by: uuid.UUID
    ) -> TaskAssignment | None:
        existing = db.scalar(
            select(TaskAssignment).where(
                and_(
                    TaskAssignment.task_id == task_id,
                    TaskAssignment.user_id == user_id,
                )
            )
        )
        if existing:
            return None

        assignment = TaskAssignment(
            task_id=task_id, user_id=user_id, assigned_by_id=assigned_by
        )
        db.add(assignment)

        db.add(
            TaskActivity(
                task_id=task_id,
                actor_id=assigned_by,
                action="assigned",
                to_value=str(user_id),
            )
        )
        db.flush()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def unassign_user(db: Session, task_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        assignment = db.scalar(
            select(TaskAssignment).where(
                and_(
                    TaskAssignment.task_id == task_id,
                    TaskAssignment.user_id == user_id,
                )
            )
        )
        if not assignment:
            return False
        db.delete(assignment)
        db.flush()
        return True

    # ── Comments ───────────────────────────────────────────────────────────

    @staticmethod
    def add_comment(
        db: Session,
        task_id: uuid.UUID,
        author_id: uuid.UUID,
        payload: TaskCommentCreate,
    ) -> TaskComment:
        comment = TaskComment(
            task_id=task_id,
            author_id=author_id,
            content=payload.content,
            parent_comment_id=payload.parent_comment_id,
        )
        db.add(comment)

        db.add(
            TaskActivity(
                task_id=task_id,
                actor_id=author_id,
                action="commented",
                to_value=payload.content[:100],
            )
        )
        db.flush()
        db.refresh(comment)
        return comment

    @staticmethod
    def list_comments(db: Session, task_id: uuid.UUID) -> list[TaskComment]:
        return list(
            db.scalars(
                select(TaskComment)
                .where(TaskComment.task_id == task_id)
                .order_by(TaskComment.created_at)
            )
        )

    @staticmethod
    def delete_comment(
        db: Session, comment_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        comment = db.get(TaskComment, comment_id)
        if not comment or comment.author_id != user_id:
            return False
        db.delete(comment)
        db.flush()
        return True

    # ── Activity Log ───────────────────────────────────────────────────────

    @staticmethod
    def get_activity_log(
        db: Session, task_id: uuid.UUID, *, limit: int = 50
    ) -> list[TaskActivity]:
        return list(
            db.scalars(
                select(TaskActivity)
                .where(TaskActivity.task_id == task_id)
                .order_by(TaskActivity.created_at.desc())
                .limit(limit)
            )
        )

    # ── Statistics ─────────────────────────────────────────────────────────

    @staticmethod
    def get_board_statistics(db: Session, board_id: uuid.UUID) -> dict:
        board = db.get(ContributionBoard, board_id)
        if not board:
            return {}

        base = select(func.count()).select_from(ContributionTask).where(
            ContributionTask.board_id == board_id
        )

        total = db.scalar(base) or 0
        open_count = db.scalar(
            base.where(ContributionTask.status == TaskStatus.OPEN)
        ) or 0
        in_progress = db.scalar(
            base.where(ContributionTask.status == TaskStatus.IN_PROGRESS)
        ) or 0
        in_review = db.scalar(
            base.where(ContributionTask.status == TaskStatus.IN_REVIEW)
        ) or 0
        done = db.scalar(
            base.where(ContributionTask.status == TaskStatus.DONE)
        ) or 0
        archived = db.scalar(
            base.where(ContributionTask.status == TaskStatus.ARCHIVED)
        ) or 0

        now = datetime.now(timezone.utc)
        overdue = (
            db.scalar(
                select(func.count())
                .select_from(ContributionTask)
                .where(
                    and_(
                        ContributionTask.board_id == board_id,
                        ContributionTask.due_date < now,
                        ContributionTask.status.notin_(
                            [TaskStatus.DONE, TaskStatus.ARCHIVED]
                        ),
                    )
                )
            )
            or 0
        )

        # Tasks by priority
        tasks_by_priority = {}
        for prio in TaskPriority:
            tasks_by_priority[prio.value] = (
                db.scalar(
                    base.where(ContributionTask.priority == prio)
                )
                or 0
            )

        # Tasks per column
        cols = list(
            db.scalars(
                select(BoardColumn)
                .where(BoardColumn.board_id == board_id)
                .order_by(BoardColumn.position)
            )
        )
        tasks_by_column = []
        for col in cols:
            cnt = (
                db.scalar(
                    select(func.count())
                    .select_from(ContributionTask)
                    .where(ContributionTask.column_id == col.id)
                )
                or 0
            )
            tasks_by_column.append(
                {"column_id": str(col.id), "title": col.title, "count": cnt}
            )

        # Avg estimated hours
        avg_hours = db.scalar(
            select(func.avg(ContributionTask.estimated_hours)).where(
                and_(
                    ContributionTask.board_id == board_id,
                    ContributionTask.estimated_hours.isnot(None),
                )
            )
        )

        # Unique contributors
        contributor_count = db.scalar(
            select(func.count(func.distinct(TaskAssignment.user_id)))
            .select_from(TaskAssignment)
            .join(
                ContributionTask, TaskAssignment.task_id == ContributionTask.id
            )
            .where(ContributionTask.board_id == board_id)
        ) or 0

        return {
            "board_id": board_id,
            "total_tasks": total,
            "open_tasks": open_count,
            "in_progress_tasks": in_progress,
            "in_review_tasks": in_review,
            "done_tasks": done,
            "archived_tasks": archived,
            "overdue_tasks": overdue,
            "tasks_by_priority": tasks_by_priority,
            "tasks_by_column": tasks_by_column,
            "avg_estimated_hours": round(avg_hours, 1) if avg_hours else None,
            "contributor_count": contributor_count,
        }
