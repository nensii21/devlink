from __future__ import annotations

import uuid
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, joinedload

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.milestone import Milestone
from app.models.announcement import Announcement
from app.models.user import User
from app.models.activity import ActivityType
from app.services.activity_service import ActivityService
from app.schemas.milestone import MilestoneCreate
from app.schemas.announcement import AnnouncementCreate
from app.schemas.project_dashboard import (
    DashboardMember,
    DashboardInvitation,
    ProjectDashboardResponse,
)


class ProjectDashboardService:
    """
    Business logic for Project Team Workspace Dashboard operations.
    """

    @staticmethod
    def get_dashboard_data(
        db: Session, project_id: uuid.UUID
    ) -> ProjectDashboardResponse:
        project = db.get(Project, project_id)
        if not project:
            return None

        # 1. Fetch recent activity
        activities = ActivityService.list_project_activities(db, project_id)

        # 2. Fetch milestones
        milestones = db.scalars(
            select(Milestone)
            .where(Milestone.project_id == project_id)
            .order_by(Milestone.due_date.asc(), Milestone.created_at.asc())
        ).all()

        # 3. Fetch announcements (with author relationship loaded)
        announcements = db.scalars(
            select(Announcement)
            .where(Announcement.project_id == project_id)
            .options(joinedload(Announcement.author))
            .order_by(Announcement.created_at.desc())
        ).all()

        # 4. Fetch active members
        active_members_db = db.scalars(
            select(ProjectMember)
            .where(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.is_active == True,
                )
            )
            .options(joinedload(ProjectMember.user))
        ).all()

        members = []
        for m in active_members_db:
            if m.user:
                members.append(
                    DashboardMember(
                        user_id=m.user.id,
                        username=m.user.username,
                        full_name=f"{m.user.first_name} {m.user.last_name}",
                        profile_image=m.user.profile_image,
                        role=m.role,
                        is_online=getattr(m.user, "is_online", False),
                        last_seen=m.user.last_seen,
                    )
                )

        # Also include project owner as an active member if not already in the list
        owner_in_list = any(m.user_id == project.owner_id for m in members)
        if not owner_in_list:
            owner_user = db.get(User, project.owner_id)
            if owner_user:
                members.insert(
                    0,
                    DashboardMember(
                        user_id=owner_user.id,
                        username=owner_user.username,
                        full_name=f"{owner_user.first_name} {owner_user.last_name}",
                        profile_image=owner_user.profile_image,
                        role="owner",
                        is_online=getattr(owner_user, "is_online", False),
                        last_seen=owner_user.last_seen,
                    ),
                )

        # 5. Fetch pending invitations
        pending_invites_db = db.scalars(
            select(ProjectMember)
            .where(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.is_active == False,
                )
            )
            .options(joinedload(ProjectMember.user))
        ).all()

        pending_invitations = []
        for m in pending_invites_db:
            if m.user:
                pending_invitations.append(
                    DashboardInvitation(
                        user_id=m.user.id,
                        username=m.user.username,
                        full_name=f"{m.user.first_name} {m.user.last_name}",
                        profile_image=m.user.profile_image,
                        role=m.role,
                        invited_at=m.created_at,
                    )
                )

        return ProjectDashboardResponse(
            project_id=project.id,
            title=project.title,
            stage=(
                project.stage.value
                if hasattr(project.stage, "value")
                else str(project.stage)
            ),
            recent_activity=activities,
            milestones=milestones,
            announcements=announcements,
            members=members,
            pending_invitations=pending_invitations,
        )

    @staticmethod
    def create_milestone(
        db: Session,
        project_id: uuid.UUID,
        actor_id: uuid.UUID,
        milestone_in: MilestoneCreate,
    ) -> Milestone:
        actor = db.get(User, actor_id)
        milestone = Milestone(
            project_id=project_id,
            title=milestone_in.title,
            description=milestone_in.description,
            due_date=milestone_in.due_date,
            is_completed=False,
        )
        db.add(milestone)
        db.flush()

        ActivityService.record_activity(
            db,
            actor_id=actor_id,
            activity_type=ActivityType.PROJECT_MILESTONE,
            title="Milestone Created",
            description=f"Milestone '{milestone.title}' was created by {actor.username if actor else 'a team member'}.",
            target_id=project_id,
            target_type="project",
        )
        db.commit()
        db.refresh(milestone)
        return milestone

    @staticmethod
    def complete_milestone(
        db: Session,
        project_id: uuid.UUID,
        milestone_id: uuid.UUID,
        actor_id: uuid.UUID,
        is_completed: bool,
    ) -> Milestone | None:
        milestone = db.scalar(
            select(Milestone).where(
                and_(
                    Milestone.id == milestone_id,
                    Milestone.project_id == project_id,
                )
            )
        )
        if not milestone:
            return None

        milestone.is_completed = is_completed
        db.flush()

        actor = db.get(User, actor_id)
        status_text = "completed" if is_completed else "reopened"
        ActivityService.record_activity(
            db,
            actor_id=actor_id,
            activity_type=ActivityType.PROJECT_MILESTONE,
            title=f"Milestone {status_text.capitalize()}",
            description=f"Milestone '{milestone.title}' was {status_text} by {actor.username if actor else 'a team member'}.",
            target_id=project_id,
            target_type="project",
        )
        db.commit()
        db.refresh(milestone)
        return milestone

    @staticmethod
    def create_announcement(
        db: Session,
        project_id: uuid.UUID,
        author_id: uuid.UUID,
        announcement_in: AnnouncementCreate,
    ) -> Announcement:
        author = db.get(User, author_id)
        announcement = Announcement(
            project_id=project_id,
            author_id=author_id,
            title=announcement_in.title,
            content=announcement_in.content,
        )
        db.add(announcement)
        db.flush()

        ActivityService.record_activity(
            db,
            actor_id=author_id,
            activity_type=ActivityType.PROJECT_ANNOUNCEMENT,
            title="Announcement Posted",
            description=f"Announcement '{announcement.title}' was posted by {author.username if author else 'a team member'}.",
            target_id=project_id,
            target_type="project",
        )
        db.commit()
        db.refresh(announcement)
        announcement.author = author  # Ensure relationship is loaded for schema mapping
        return announcement
