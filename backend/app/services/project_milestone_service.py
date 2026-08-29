from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.milestone import Milestone
from app.models.project import Project
from app.models.project_member import MemberRole, ProjectMember
from app.models.user import User
from app.schemas.milestone import (
    MilestoneCreate,
    MilestoneProgressResponse,
    MilestoneResponse,
    MilestoneTimelineItem,
    MilestoneTimelineResponse,
    MilestoneUpdate,
)

logger = logging.getLogger(__name__)


class ProjectMilestoneService:
    """
    Business logic for Project Milestone Management (#618).
    """

    # ------------------------------------------------------------------
    # Authorization & Validation Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_project_or_404(db: Session, project_id: uuid.UUID) -> Project:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return project

    @staticmethod
    def is_user_project_maintainer(
        db: Session, project: Project, user_id: uuid.UUID
    ) -> bool:
        """
        Check if user is project owner, co-owner, admin, or maintainer.
        """
        if project.owner_id == user_id:
            return True

        stmt = select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_active.is_(True),
        )
        member = db.scalar(stmt)
        if member and member.role in {
            MemberRole.OWNER,
            MemberRole.CO_OWNER,
            MemberRole.ADMIN,
            MemberRole.MAINTAINER,
        }:
            return True

        return False

    @staticmethod
    def require_project_maintainer(db: Session, project: Project, user: User) -> None:
        """
        Raise 403 Forbidden if user is not authorized to edit project milestones.
        """
        if (
            getattr(user, "system_role", None) == "admin"
            or getattr(user, "role", None) == "admin"
        ):
            return

        if not ProjectMilestoneService.is_user_project_maintainer(db, project, user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owners and maintainers can manage milestones.",
            )

    @staticmethod
    def validate_milestone_owner(
        db: Session, project: Project, owner_id: uuid.UUID
    ) -> None:
        """Ensure the given owner_id is a valid active member or the owner of the project."""
        if project.owner_id == owner_id:
            return

        stmt = select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == owner_id,
            ProjectMember.is_active.is_(True),
        )
        if not db.scalar(stmt):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Milestone owner must be an active member of the project.",
            )

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------

    @staticmethod
    def create_milestone(
        db: Session,
        project_id: uuid.UUID,
        milestone_in: MilestoneCreate,
        actor: User,
    ) -> Milestone:
        project = ProjectMilestoneService.get_project_or_404(db, project_id)
        ProjectMilestoneService.require_project_maintainer(db, project, actor)

        if milestone_in.owner_id:
            ProjectMilestoneService.validate_milestone_owner(
                db, project, milestone_in.owner_id
            )

        now = datetime.now(timezone.utc)
        milestone = Milestone(
            id=uuid.uuid4(),
            project_id=project_id,
            title=milestone_in.title.strip(),
            description=(
                milestone_in.description.strip() if milestone_in.description else None
            ),
            due_date=milestone_in.due_date,
            owner_id=milestone_in.owner_id,
            is_completed=False,
            is_archived=False,
            created_at=now,
            updated_at=now,
        )

        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        return milestone

    @staticmethod
    def get_milestone_or_404(
        db: Session, project_id: uuid.UUID, milestone_id: uuid.UUID
    ) -> Milestone:
        stmt = select(Milestone).where(
            Milestone.id == milestone_id,
            Milestone.project_id == project_id,
        )
        milestone = db.scalar(stmt)
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Milestone not found",
            )
        return milestone

    @staticmethod
    def list_milestones(
        db: Session,
        project_id: uuid.UUID,
        include_archived: bool = False,
        is_completed: Optional[bool] = None,
    ) -> list[Milestone]:
        ProjectMilestoneService.get_project_or_404(db, project_id)

        stmt = select(Milestone).where(Milestone.project_id == project_id)

        if not include_archived:
            stmt = stmt.where(Milestone.is_archived.is_(False))

        if is_completed is not None:
            stmt = stmt.where(Milestone.is_completed.is_(is_completed))

        # Order by due_date nulls last, then created_at
        stmt = stmt.order_by(
            Milestone.due_date.asc().nulls_last(), Milestone.created_at.asc()
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def update_milestone(
        db: Session,
        project_id: uuid.UUID,
        milestone_id: uuid.UUID,
        milestone_in: MilestoneUpdate,
        actor: User,
    ) -> Milestone:
        project = ProjectMilestoneService.get_project_or_404(db, project_id)
        ProjectMilestoneService.require_project_maintainer(db, project, actor)

        milestone = ProjectMilestoneService.get_milestone_or_404(
            db, project_id, milestone_id
        )

        now = datetime.now(timezone.utc)

        if milestone_in.title is not None:
            milestone.title = milestone_in.title.strip()
        if milestone_in.description is not None:
            milestone.description = (
                milestone_in.description.strip() if milestone_in.description else None
            )
        if milestone_in.due_date is not None:
            milestone.due_date = milestone_in.due_date

        # We check if owner_id was explicitly provided, since it can be nullified.
        # But wait, milestone_in is a Pydantic model. If it was passed in the update payload, it will be in the fields set.
        if "owner_id" in milestone_in.model_fields_set:
            if milestone_in.owner_id is not None:
                ProjectMilestoneService.validate_milestone_owner(
                    db, project, milestone_in.owner_id
                )
            milestone.owner_id = milestone_in.owner_id

        if milestone_in.is_completed is not None:
            if milestone_in.is_completed and not milestone.is_completed:
                milestone.is_completed = True
                milestone.completed_at = now
            elif not milestone_in.is_completed and milestone.is_completed:
                milestone.is_completed = False
                milestone.completed_at = None

        if milestone_in.is_archived is not None:
            if milestone_in.is_archived and not milestone.is_archived:
                milestone.is_archived = True
                milestone.archived_at = now
            elif not milestone_in.is_archived and milestone.is_archived:
                milestone.is_archived = False
                milestone.archived_at = None

        milestone.updated_at = now
        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        return milestone

    @staticmethod
    def archive_milestone(
        db: Session,
        project_id: uuid.UUID,
        milestone_id: uuid.UUID,
        actor: User,
        archive: bool = True,
    ) -> Milestone:
        project = ProjectMilestoneService.get_project_or_404(db, project_id)
        ProjectMilestoneService.require_project_maintainer(db, project, actor)

        milestone = ProjectMilestoneService.get_milestone_or_404(
            db, project_id, milestone_id
        )
        now = datetime.now(timezone.utc)

        milestone.is_archived = archive
        milestone.archived_at = now if archive else None
        milestone.updated_at = now

        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        return milestone

    @staticmethod
    def delete_milestone(
        db: Session,
        project_id: uuid.UUID,
        milestone_id: uuid.UUID,
        actor: User,
    ) -> None:
        project = ProjectMilestoneService.get_project_or_404(db, project_id)
        ProjectMilestoneService.require_project_maintainer(db, project, actor)

        milestone = ProjectMilestoneService.get_milestone_or_404(
            db, project_id, milestone_id
        )
        db.delete(milestone)
        db.commit()

    # ------------------------------------------------------------------
    # Progress & Timeline Calculations
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_progress(
        db: Session, project_id: uuid.UUID
    ) -> MilestoneProgressResponse:
        ProjectMilestoneService.get_project_or_404(db, project_id)

        stmt = select(Milestone).where(Milestone.project_id == project_id)
        milestones = list(db.scalars(stmt).all())

        now = datetime.now(timezone.utc)

        total_cnt = len(milestones)
        archived_cnt = len([m for m in milestones if m.is_archived])
        active_milestones = [m for m in milestones if not m.is_archived]
        active_cnt = len(active_milestones)

        completed_cnt = len([m for m in active_milestones if m.is_completed])
        overdue_cnt = len(
            [
                m
                for m in active_milestones
                if not m.is_completed and m.due_date and m.due_date < now
            ]
        )

        if active_cnt > 0:
            percentage = round((completed_cnt / active_cnt) * 100.0, 1)
        elif total_cnt > 0:
            percentage = round(
                (len([m for m in milestones if m.is_completed]) / total_cnt) * 100.0, 1
            )
        else:
            percentage = 0.0

        return MilestoneProgressResponse(
            total_milestones=total_cnt,
            completed_milestones=completed_cnt,
            active_milestones=active_cnt,
            archived_milestones=archived_cnt,
            overdue_milestones=overdue_cnt,
            completion_percentage=percentage,
        )

    @staticmethod
    def get_timeline(db: Session, project_id: uuid.UUID) -> MilestoneTimelineResponse:
        project = ProjectMilestoneService.get_project_or_404(db, project_id)
        progress = ProjectMilestoneService.calculate_progress(db, project_id)

        stmt = select(Milestone).where(Milestone.project_id == project_id)
        # Order by due_date asc (nulls last), then created_at
        stmt = stmt.order_by(
            Milestone.due_date.asc().nulls_last(), Milestone.created_at.asc()
        )
        milestones = list(db.scalars(stmt).all())

        now = datetime.now(timezone.utc)
        timeline_items: list[MilestoneTimelineItem] = []

        for m in milestones:
            days_rem: Optional[int] = None
            if m.due_date:
                # Ensure timezone aware comparison
                due_dt = (
                    m.due_date
                    if m.due_date.tzinfo
                    else m.due_date.replace(tzinfo=timezone.utc)
                )
                delta = due_dt - now
                days_rem = delta.days

            if m.is_archived:
                m_status = "archived"
            elif m.is_completed:
                m_status = "completed"
            elif (
                m.due_date
                and (
                    m.due_date
                    if m.due_date.tzinfo
                    else m.due_date.replace(tzinfo=timezone.utc)
                )
                < now
            ):
                m_status = "overdue"
            else:
                m_status = "upcoming"

            timeline_items.append(
                MilestoneTimelineItem(
                    milestone=MilestoneResponse.model_validate(m),
                    status=m_status,
                    days_remaining=days_rem,
                )
            )

        return MilestoneTimelineResponse(
            project_id=project.id,
            project_title=project.title,
            progress=progress,
            timeline=timeline_items,
        )
