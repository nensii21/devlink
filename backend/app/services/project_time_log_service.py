from __future__ import annotations

"""
Business logic for project time tracking (#1041).
"""

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.milestone import Milestone
from app.models.project import Project
from app.models.project_member import MemberRole, ProjectMember
from app.models.project_time_log import ProjectTimeLog
from app.models.user import User
from app.schemas.project_time_log import (
    MAX_BACKFILL_DAYS,
    MAX_MINUTES_PER_ENTRY,
    ContributorTotal,
    MilestoneTotal,
    TimeLogCreate,
    TimeLogSummary,
    TimeLogUpdate,
)

logger = logging.getLogger(__name__)

# Nobody works more than 24 hours on one project in one day. A total that says
# otherwise is a double-entry or a typo, and silently accepting it poisons every
# report built on top.
MAX_MINUTES_PER_DAY = 24 * 60

MAINTAINER_ROLES = {
    MemberRole.OWNER,
    MemberRole.CO_OWNER,
    MemberRole.ADMIN,
    MemberRole.MAINTAINER,
}


class ProjectTimeLogService:
    """Log, edit and summarise work recorded against a project."""

    # ------------------------------------------------------------------
    # Lookups & authorization
    # ------------------------------------------------------------------

    @staticmethod
    def get_project_or_404(db: Session, project_id: uuid.UUID) -> Project:
        project = db.get(Project, project_id)
        if project is None or getattr(project, "deleted_at", None) is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return project

    @staticmethod
    def get_membership(
        db: Session, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[ProjectMember]:
        stmt = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_active.is_(True),
        )
        return db.scalar(stmt)

    @staticmethod
    def is_admin(user: User) -> bool:
        return (
            getattr(user, "system_role", None) == "admin"
            or getattr(user, "role", None) == "admin"
        )

    @staticmethod
    def require_member(db: Session, project: Project, user: User) -> None:
        """
        Only people actually on the project may log against it. Time logs feed
        contributor-level reporting, so letting a stranger add rows would let
        them write into someone else's numbers.
        """
        if project.owner_id == user.id or ProjectTimeLogService.is_admin(user):
            return
        if ProjectTimeLogService.get_membership(db, project.id, user.id) is not None:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project members can log time against this project.",
        )

    @staticmethod
    def is_maintainer(db: Session, project: Project, user: User) -> bool:
        if project.owner_id == user.id or ProjectTimeLogService.is_admin(user):
            return True
        member = ProjectTimeLogService.get_membership(db, project.id, user.id)
        return member is not None and member.role in MAINTAINER_ROLES

    @staticmethod
    def require_can_modify(
        db: Session, project: Project, log: ProjectTimeLog, user: User
    ) -> None:
        """
        An entry belongs to whoever did the work. Maintainers get delete rights
        so a project can clean up after a departed member, but nobody may
        *rewrite* someone else's hours -- an edited entry that still carries
        another person's name is worse than no entry at all.
        """
        if log.user_id == user.id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own time entries.",
        )

    @staticmethod
    def require_can_delete(
        db: Session, project: Project, log: ProjectTimeLog, user: User
    ) -> None:
        if log.user_id == user.id or ProjectTimeLogService.is_maintainer(
            db, project, user
        ):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own time entries.",
        )

    @staticmethod
    def get_log_or_404(
        db: Session, project_id: uuid.UUID, log_id: uuid.UUID
    ) -> ProjectTimeLog:
        stmt = select(ProjectTimeLog).where(
            ProjectTimeLog.id == log_id,
            ProjectTimeLog.project_id == project_id,
        )
        log = db.scalar(stmt)
        if log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found",
            )
        return log

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_work_date(work_date: date, today: date | None = None) -> None:
        reference = today or datetime.now(timezone.utc).date()

        if work_date > reference:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="work_date cannot be in the future.",
            )
        if work_date < reference - timedelta(days=MAX_BACKFILL_DAYS):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"work_date cannot be more than {MAX_BACKFILL_DAYS} days in the past.",
            )

    @staticmethod
    def validate_milestone(
        db: Session, project_id: uuid.UUID, milestone_id: uuid.UUID | None
    ) -> None:
        if milestone_id is None:
            return
        stmt = select(Milestone.id).where(
            Milestone.id == milestone_id,
            Milestone.project_id == project_id,
        )
        if db.scalar(stmt) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found on this project.",
            )

    @staticmethod
    def minutes_logged_on(
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        work_date: date,
        exclude_log_id: uuid.UUID | None = None,
    ) -> int:
        stmt = select(func.coalesce(func.sum(ProjectTimeLog.minutes), 0)).where(
            ProjectTimeLog.project_id == project_id,
            ProjectTimeLog.user_id == user_id,
            ProjectTimeLog.work_date == work_date,
        )
        if exclude_log_id is not None:
            stmt = stmt.where(ProjectTimeLog.id != exclude_log_id)
        return int(db.scalar(stmt) or 0)

    @staticmethod
    def validate_daily_cap(
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        work_date: date,
        minutes: int,
        exclude_log_id: uuid.UUID | None = None,
    ) -> None:
        already = ProjectTimeLogService.minutes_logged_on(
            db, project_id, user_id, work_date, exclude_log_id=exclude_log_id
        )
        if already + minutes > MAX_MINUTES_PER_DAY:
            remaining = max(0, MAX_MINUTES_PER_DAY - already)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Logging {minutes} minutes would exceed the 24-hour daily limit "
                    f"for {work_date.isoformat()}. {remaining} minutes remain."
                ),
            )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @staticmethod
    def create_log(
        db: Session,
        project_id: uuid.UUID,
        payload: TimeLogCreate,
        actor: User,
        today: date | None = None,
    ) -> ProjectTimeLog:
        project = ProjectTimeLogService.get_project_or_404(db, project_id)
        ProjectTimeLogService.require_member(db, project, actor)

        ProjectTimeLogService.validate_work_date(payload.work_date, today=today)
        ProjectTimeLogService.validate_milestone(db, project_id, payload.milestone_id)
        ProjectTimeLogService.validate_daily_cap(
            db, project_id, actor.id, payload.work_date, payload.minutes
        )

        now = datetime.now(timezone.utc)
        log = ProjectTimeLog(
            id=uuid.uuid4(),
            project_id=project_id,
            user_id=actor.id,
            milestone_id=payload.milestone_id,
            minutes=payload.minutes,
            work_date=payload.work_date,
            description=payload.description,
            is_billable=payload.is_billable,
            created_at=now,
            updated_at=now,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def update_log(
        db: Session,
        project_id: uuid.UUID,
        log_id: uuid.UUID,
        payload: TimeLogUpdate,
        actor: User,
        today: date | None = None,
    ) -> ProjectTimeLog:
        project = ProjectTimeLogService.get_project_or_404(db, project_id)
        log = ProjectTimeLogService.get_log_or_404(db, project_id, log_id)
        ProjectTimeLogService.require_can_modify(db, project, log, actor)

        data = payload.model_dump(exclude_unset=True)

        new_date = data.get("work_date", log.work_date)
        new_minutes = data.get("minutes", log.minutes)

        if "work_date" in data:
            ProjectTimeLogService.validate_work_date(new_date, today=today)
        if "milestone_id" in data:
            ProjectTimeLogService.validate_milestone(
                db, project_id, data["milestone_id"]
            )

        # Re-check the cap whenever either half of the (date, minutes) pair
        # moves -- shifting an entry onto an already-full day is just as much a
        # violation as growing it in place.
        if "minutes" in data or "work_date" in data:
            ProjectTimeLogService.validate_daily_cap(
                db,
                project_id,
                log.user_id,
                new_date,
                new_minutes,
                exclude_log_id=log.id,
            )

        for field, value in data.items():
            setattr(log, field, value)
        log.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def delete_log(
        db: Session, project_id: uuid.UUID, log_id: uuid.UUID, actor: User
    ) -> None:
        project = ProjectTimeLogService.get_project_or_404(db, project_id)
        log = ProjectTimeLogService.get_log_or_404(db, project_id, log_id)
        ProjectTimeLogService.require_can_delete(db, project, log, actor)

        db.delete(log)
        db.commit()

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    @staticmethod
    def _filtered_query(
        project_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        milestone_id: uuid.UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        is_billable: bool | None = None,
    ):
        conditions = [ProjectTimeLog.project_id == project_id]
        if user_id is not None:
            conditions.append(ProjectTimeLog.user_id == user_id)
        if milestone_id is not None:
            conditions.append(ProjectTimeLog.milestone_id == milestone_id)
        if from_date is not None:
            conditions.append(ProjectTimeLog.work_date >= from_date)
        if to_date is not None:
            conditions.append(ProjectTimeLog.work_date <= to_date)
        if is_billable is not None:
            conditions.append(ProjectTimeLog.is_billable.is_(is_billable))
        return conditions

    @staticmethod
    def list_logs(
        db: Session,
        project_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        user_id: uuid.UUID | None = None,
        milestone_id: uuid.UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        is_billable: bool | None = None,
    ) -> tuple[list[ProjectTimeLog], int, int]:
        """Return ``(page, total_rows, total_minutes_across_all_rows)``."""
        conditions = ProjectTimeLogService._filtered_query(
            project_id,
            user_id=user_id,
            milestone_id=milestone_id,
            from_date=from_date,
            to_date=to_date,
            is_billable=is_billable,
        )

        total = int(
            db.scalar(select(func.count(ProjectTimeLog.id)).where(*conditions)) or 0
        )
        # The total is over the whole filter, not the page -- a report that
        # only adds up the visible page is a report nobody can trust.
        total_minutes = int(
            db.scalar(
                select(func.coalesce(func.sum(ProjectTimeLog.minutes), 0)).where(
                    *conditions
                )
            )
            or 0
        )

        stmt = (
            select(ProjectTimeLog)
            .where(*conditions)
            .options(selectinload(ProjectTimeLog.user))
            # Newest work first, with created_at as the tiebreak so a page
            # boundary cannot repeat or drop an entry.
            .order_by(ProjectTimeLog.work_date.desc(), ProjectTimeLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        items = list(db.scalars(stmt).all())
        return items, total, total_minutes

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    @staticmethod
    def summarise(
        db: Session,
        project_id: uuid.UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> TimeLogSummary:
        ProjectTimeLogService.get_project_or_404(db, project_id)

        conditions = ProjectTimeLogService._filtered_query(
            project_id, from_date=from_date, to_date=to_date
        )

        totals_row = db.execute(
            select(
                func.coalesce(func.sum(ProjectTimeLog.minutes), 0),
                func.count(ProjectTimeLog.id),
                func.min(ProjectTimeLog.work_date),
                func.max(ProjectTimeLog.work_date),
            ).where(*conditions)
        ).one()
        total_minutes, total_entries, first_day, last_day = totals_row

        billable_minutes = int(
            db.scalar(
                select(func.coalesce(func.sum(ProjectTimeLog.minutes), 0)).where(
                    *conditions, ProjectTimeLog.is_billable.is_(True)
                )
            )
            or 0
        )

        contributor_rows = db.execute(
            select(
                ProjectTimeLog.user_id,
                User.username,
                func.sum(ProjectTimeLog.minutes),
                func.count(ProjectTimeLog.id),
            )
            .join(User, User.id == ProjectTimeLog.user_id, isouter=True)
            .where(*conditions)
            .group_by(ProjectTimeLog.user_id, User.username)
            .order_by(func.sum(ProjectTimeLog.minutes).desc())
        ).all()

        milestone_rows = db.execute(
            select(
                ProjectTimeLog.milestone_id,
                Milestone.title,
                func.sum(ProjectTimeLog.minutes),
                func.count(ProjectTimeLog.id),
            )
            .join(Milestone, Milestone.id == ProjectTimeLog.milestone_id, isouter=True)
            .where(*conditions)
            .group_by(ProjectTimeLog.milestone_id, Milestone.title)
            .order_by(func.sum(ProjectTimeLog.minutes).desc())
        ).all()

        total_minutes = int(total_minutes or 0)

        return TimeLogSummary(
            project_id=project_id,
            total_minutes=total_minutes,
            total_hours=ProjectTimeLogService.to_hours(total_minutes),
            total_entries=int(total_entries or 0),
            billable_minutes=billable_minutes,
            billable_hours=ProjectTimeLogService.to_hours(billable_minutes),
            non_billable_minutes=total_minutes - billable_minutes,
            non_billable_hours=ProjectTimeLogService.to_hours(
                total_minutes - billable_minutes
            ),
            contributor_count=len(contributor_rows),
            first_logged_date=first_day,
            last_logged_date=last_day,
            by_contributor=[
                ContributorTotal(
                    user_id=user_id,
                    username=username,
                    minutes=int(minutes or 0),
                    hours=ProjectTimeLogService.to_hours(int(minutes or 0)),
                    entries=int(entries or 0),
                )
                for user_id, username, minutes, entries in contributor_rows
            ],
            by_milestone=[
                MilestoneTotal(
                    milestone_id=milestone_id,
                    milestone_title=title,
                    minutes=int(minutes or 0),
                    hours=ProjectTimeLogService.to_hours(int(minutes or 0)),
                    entries=int(entries or 0),
                )
                for milestone_id, title, minutes, entries in milestone_rows
            ],
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def to_hours(minutes: int) -> float:
        """
        Minutes to hours for display. Rounding happens once, at the edge --
        every stored and summed value stays an integer, so a summary and its
        line items can never disagree.
        """
        return round(minutes / 60, 2)


__all__ = ["ProjectTimeLogService", "MAX_MINUTES_PER_DAY", "MAX_MINUTES_PER_ENTRY"]
