from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.project import Project
from app.models.application import Application
from app.models.follower import Follower
from app.models.bookmark import Bookmark
from app.models.message import Message
from app.models.notification import Notification
from app.models.builder_flare import BuilderFlare
from app.models.organization import Organization
from app.models.activity import Activity
from app.models.user_skill import UserSkill
from app.models.project_member import ProjectMember
from app.schemas.export import (
    ExportedApplication,
    ExportedBookmark,
    ExportedConnection,
    ExportedMessage,
    ExportedOrganization,
    ExportedProject,
    ExportedSkill,
    UserExportData,
)


class ExportService:
    """
    Collects and serialises every piece of data belonging to a user.
    """

    @staticmethod
    def collect_user_data(db: Session, user: User) -> UserExportData:
        now = datetime.now(timezone.utc)

        profile = ExportService._build_profile(user)
        skills = ExportService._get_skills(db, user.id)
        projects = ExportService._get_projects(db, user.id)
        project_memberships = ExportService._get_project_memberships(db, user.id)
        applications = ExportService._get_applications(db, user.id)
        connections = ExportService._get_connections(db, user.id)
        messages = ExportService._get_messages(db, user.id)
        bookmarks = ExportService._get_bookmarks(db, user.id)
        organizations = ExportService._get_organizations(db, user.id)
        activities = ExportService._get_activities(db, user.id)
        notifications = ExportService._get_notifications(db, user.id)
        builder_flares = ExportService._get_builder_flares(db, user.id)

        return UserExportData(
            exported_at=now,
            profile=profile,
            skills=skills,
            projects=projects,
            project_memberships=project_memberships,
            applications=applications,
            connections=connections,
            messages=messages,
            bookmarks=bookmarks,
            organizations=organizations,
            activities=activities,
            notifications=notifications,
            builder_flares=builder_flares,
        )

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------

    @staticmethod
    def _build_profile(user: User) -> dict:
        return {
            "id": str(user.id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "headline": user.headline,
            "bio": user.bio,
            "profile_image": user.profile_image,
            "cover_image": user.cover_image,
            "location": user.location,
            "timezone": user.timezone,
            "website": str(user.website) if user.website else None,
            "portfolio_url": str(user.portfolio_url) if user.portfolio_url else None,
            "public_email": user.public_email,
            "github_url": str(user.github_url) if user.github_url else None,
            "linkedin_url": str(user.linkedin_url) if user.linkedin_url else None,
            "role": user.role,
            "experience_level": user.experience_level,
            "company": user.company,
            "open_to_work": user.open_to_work,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    # ------------------------------------------------------------------
    # Skills
    # ------------------------------------------------------------------

    @staticmethod
    def _get_skills(db: Session, user_id: uuid.UUID) -> list[ExportedSkill]:
        from app.models.skill import Skill

        rows = (
            db.query(UserSkill, Skill)
            .join(Skill, UserSkill.skill_id == Skill.id)
            .filter(UserSkill.user_id == user_id)
            .all()
        )
        return [
            ExportedSkill(
                id=skill.id,
                name=skill.name,
                level=us.level.value if us.level else None,
                years_of_experience=us.years_of_experience,
            )
            for us, skill in rows
        ]

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    @staticmethod
    def _get_projects(db: Session, user_id: uuid.UUID) -> list[ExportedProject]:
        rows = (
            db.query(Project)
            .filter(Project.owner_id == user_id)
            .order_by(Project.created_at.desc())
            .all()
        )
        return [
            ExportedProject(
                id=p.id,
                title=p.title,
                slug=p.slug,
                tagline=p.tagline,
                description=p.description,
                stage=p.stage.value if p.stage else "IDEA",
                visibility=p.visibility.value if p.visibility else "PUBLIC",
                tech_stack=p.tech_stack,
                repository_url=p.repository_url,
                website_url=p.website_url,
                team_size=p.team_size,
                hiring=p.hiring,
                is_archived=p.is_archived,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in rows
        ]

    # ------------------------------------------------------------------
    # Project Memberships
    # ------------------------------------------------------------------

    @staticmethod
    def _get_project_memberships(db: Session, user_id: uuid.UUID) -> list[dict]:
        rows = db.query(ProjectMember).filter(ProjectMember.user_id == user_id).all()
        return [
            {
                "project_id": str(pm.project_id),
                "role": pm.role.value if pm.role else "MEMBER",
                "is_active": pm.is_active,
                "joined_at": pm.joined_at.isoformat() if pm.joined_at else None,
            }
            for pm in rows
        ]

    # ------------------------------------------------------------------
    # Applications
    # ------------------------------------------------------------------

    @staticmethod
    def _get_applications(db: Session, user_id: uuid.UUID) -> list[ExportedApplication]:
        rows = (
            db.query(Application)
            .filter(Application.applicant_id == user_id)
            .order_by(Application.created_at.desc())
            .all()
        )
        return [
            ExportedApplication(
                id=a.id,
                project_id=a.project_id,
                status=a.status.value if a.status else "PENDING",
                message=a.message,
                portfolio_url=a.portfolio_url,
                github_url=a.github_url,
                created_at=a.created_at,
            )
            for a in rows
        ]

    # ------------------------------------------------------------------
    # Connections (followers + following)
    # ------------------------------------------------------------------

    @staticmethod
    def _get_connections(db: Session, user_id: uuid.UUID) -> list[ExportedConnection]:
        connections: list[ExportedConnection] = []

        following_rows = (
            db.query(Follower).filter(Follower.follower_id == user_id).all()
        )
        for f in following_rows:
            target = db.get(User, f.following_id)
            connections.append(
                ExportedConnection(
                    user_id=f.following_id,
                    username=target.username if target else None,
                    full_name=(
                        f"{target.first_name} {target.last_name}" if target else None
                    ),
                    direction="following",
                    created_at=f.created_at,
                )
            )

        follower_rows = (
            db.query(Follower).filter(Follower.following_id == user_id).all()
        )
        for f in follower_rows:
            source = db.get(User, f.follower_id)
            connections.append(
                ExportedConnection(
                    user_id=f.follower_id,
                    username=source.username if source else None,
                    full_name=(
                        f"{source.first_name} {source.last_name}" if source else None
                    ),
                    direction="follower",
                    created_at=f.created_at,
                )
            )

        return connections

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    @staticmethod
    def _get_messages(db: Session, user_id: uuid.UUID) -> list[ExportedMessage]:
        rows = (
            db.query(Message)
            .filter(Message.sender_id == user_id)
            .order_by(Message.created_at.desc())
            .limit(1000)
            .all()
        )
        return [
            ExportedMessage(
                id=m.id,
                conversation_id=m.conversation_id,
                content=m.content,
                type=m.type.value if m.type else "TEXT",
                created_at=m.created_at,
            )
            for m in rows
        ]

    # ------------------------------------------------------------------
    # Bookmarks
    # ------------------------------------------------------------------

    @staticmethod
    def _get_bookmarks(db: Session, user_id: uuid.UUID) -> list[ExportedBookmark]:
        rows = (
            db.query(Bookmark)
            .filter(Bookmark.user_id == user_id)
            .order_by(Bookmark.created_at.desc())
            .all()
        )
        return [
            ExportedBookmark(
                id=b.id,
                project_id=b.project_id,
                created_at=b.created_at,
            )
            for b in rows
        ]

    # ------------------------------------------------------------------
    # Organizations
    # ------------------------------------------------------------------

    @staticmethod
    def _get_organizations(
        db: Session, user_id: uuid.UUID
    ) -> list[ExportedOrganization]:
        rows = db.query(Organization).filter(Organization.owner_id == user_id).all()
        return [
            ExportedOrganization(
                id=o.id,
                name=o.name,
                slug=o.slug,
                organization_type=(
                    o.organization_type.value if o.organization_type else "STARTUP"
                ),
                description=o.description,
                created_at=o.created_at,
            )
            for o in rows
        ]

    # ------------------------------------------------------------------
    # Activities
    # ------------------------------------------------------------------

    @staticmethod
    def _get_activities(db: Session, user_id: uuid.UUID) -> list[dict]:
        rows = (
            db.query(Activity)
            .filter(Activity.actor_id == user_id)
            .order_by(Activity.created_at.desc())
            .limit(500)
            .all()
        )
        return [
            {
                "id": str(a.id),
                "activity_type": a.activity_type.value if a.activity_type else None,
                "title": a.title,
                "description": a.description,
                "target_id": str(a.target_id) if a.target_id else None,
                "target_type": a.target_type,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in rows
        ]

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    @staticmethod
    def _get_notifications(db: Session, user_id: uuid.UUID) -> list[dict]:
        rows = (
            db.query(Notification)
            .filter(Notification.recipient_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(500)
            .all()
        )
        return [
            {
                "id": str(n.id),
                "type": n.type.value if n.type else None,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in rows
        ]

    # ------------------------------------------------------------------
    # Builder Flares
    # ------------------------------------------------------------------

    @staticmethod
    def _get_builder_flares(db: Session, user_id: uuid.UUID) -> list[dict]:
        rows = (
            db.query(BuilderFlare)
            .filter(BuilderFlare.created_by == user_id)
            .order_by(BuilderFlare.created_at.desc())
            .all()
        )
        return [
            {
                "id": str(f.id),
                "project_id": str(f.project_id),
                "title": f.title,
                "description": f.description,
                "role": f.role,
                "status": f.status.value if f.status else "OPEN",
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in rows
        ]
