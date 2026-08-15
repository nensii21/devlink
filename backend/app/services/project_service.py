from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.core.cache import cached
from app.models.activity import ActivityType
from app.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectDraftCreate,
    ProjectDraftUpdate,
    ProjectStatsResponse,
    ProjectUpdate,
    SimilarProjectWarning,
)
from app.services.activity_service import ActivityService


class ProjectService:
    """
    Business logic for Project operations.
    """

    @staticmethod
    def create_project(
        db: Session,
        owner_id: uuid.UUID,
        project: ProjectCreate,
    ) -> Project:
        # AI-based duplicate project detection check (#608)
        allow_dup = getattr(project, "allow_duplicate", False)
        if not allow_dup:
            from app.services.duplicate_detection_service import (
                DuplicateDetectionService,
            )

            dup_res = DuplicateDetectionService.find_duplicate_projects(
                db,
                title=project.title,
                description=project.description,
                threshold=0.80,
                limit=3,
            )
            if dup_res.has_duplicates:
                top_match = dup_res.suggested_projects[0]
                from fastapi import HTTPException, status

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": f"Potential duplicate project detected: '{top_match.title}' ({top_match.confidence_score}% match).",
                        "max_similarity_score": dup_res.max_similarity_score,
                        "suggested_projects": [
                            p.model_dump() for p in dup_res.suggested_projects
                        ],
                        "manual_override_instruction": "Pass 'allow_duplicate': true in request payload to bypass this check.",
                    },
                )

        db_project = Project(
            owner_id=owner_id,
            title=project.title,
            slug=project.slug,
            tagline=project.tagline,
            description=project.description,
            stage=project.stage,
            visibility=project.visibility,
            status=project.status,
            tech_stack=project.tech_stack,
            repository_url=project.repository_url,
            website_url=project.website_url,
            demo_url=project.demo_url,
            team_size=project.team_size,
            max_team_size=project.max_team_size,
            hiring=project.hiring,
            scheduled_publish_at=project.scheduled_publish_at,
            is_published=(project.scheduled_publish_at is None),
        )

        db.add(db_project)
        db.flush()
        db.refresh(db_project)

        # Create ProjectMember record for owner
        from app.models.project_member import MemberRole, ProjectMember

        member = ProjectMember(
            project_id=db_project.id,
            user_id=owner_id,
            role=MemberRole.OWNER,
            is_active=True,
        )
        db.add(member)
        db.commit()
        ActivityService.record_activity(
            db=db,
            actor_id=owner_id,
            activity_type=ActivityType.PROJECT_CREATED,
            title="Created project",
            description=db_project.title,
            target_id=db_project.id,
            target_type="project",
            icon="folder-plus",
            color="primary",
        )

        return db_project

    @staticmethod
    @cached(ttl=300, key_prefix="proj")
    def get_project(
        db: Session,
        project_id: uuid.UUID,
    ) -> Project | None:

        stmt = (
            select(Project)
            .options(selectinload(Project.owner))
            .where(
                Project.id == project_id,
                Project.deleted_at.is_(None),
            )
        )
        return db.scalar(stmt)

    @staticmethod
    def get_project_including_deleted(
        db: Session,
        project_id: uuid.UUID,
    ) -> Project | None:
        """Retrieve a project regardless of soft-delete status (admin use)."""
        stmt = (
            select(Project)
            .options(selectinload(Project.owner))
            .where(Project.id == project_id)
        )
        return db.scalar(stmt)

    @staticmethod
    @cached(ttl=300, key_prefix="proj")
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> Project | None:

        stmt = (
            select(Project)
            .options(selectinload(Project.owner))
            .where(
                Project.slug == slug,
                Project.deleted_at.is_(None),
            )
        )
        return db.scalar(stmt)

    @staticmethod
    @cached(ttl=300, key_prefix="proj")
    def list_projects(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        language: str | None = None,
        experience: str | None = None,
        remote: bool | None = None,
        paid: bool | None = None,
        opensource: bool | None = None,
        tech: str | None = None,
        sort_by: str | None = "newest",
    ) -> list[Project]:

        stmt = (
            select(Project)
            .options(selectinload(Project.owner))
            .where(
                Project.deleted_at.is_(None),
                Project.is_published.is_(True),
            )
        )

        if language:
            lang_list = [l.strip() for l in language.split(",") if l.strip()]
            if lang_list:
                stmt = stmt.where(Project.language.in_(lang_list))
        if experience:
            exp_list = [e.strip() for e in experience.split(",") if e.strip()]
            if exp_list:
                stmt = stmt.where(Project.experience.in_(exp_list))
        if remote is not None:
            stmt = stmt.where(Project.is_remote == remote)
        if paid is not None:
            stmt = stmt.where(Project.is_paid == paid)
        if opensource is not None:
            stmt = stmt.where(Project.is_open_source == opensource)
        if tech:
            tech_list = [t.strip() for t in tech.split(",") if t.strip()]
            if tech_list:
                from sqlalchemy import or_

                stmt = stmt.where(
                    or_(*[Project.tech_stack.ilike(f"%{t}%") for t in tech_list])
                )

        # Apply sorting logic
        from sqlalchemy import desc, asc

        if sort_by == "oldest":
            stmt = stmt.order_by(asc(Project.created_at))
        elif sort_by in ("recently_updated", "most_active"):
            stmt = stmt.order_by(desc(Project.updated_at))
        elif sort_by == "most_bookmarked":
            if hasattr(Project, "bookmarks_count"):
                stmt = stmt.order_by(desc(Project.bookmarks_count))
            else:
                stmt = stmt.order_by(desc(Project.created_at))
        elif sort_by == "most_applications":
            if hasattr(Project, "applications_count"):
                stmt = stmt.order_by(desc(Project.applications_count))
            else:
                stmt = stmt.order_by(desc(Project.created_at))
        elif sort_by == "ai_match_score":
            stmt = stmt.order_by(desc(Project.updated_at), desc(Project.created_at))
        else:
            # Default "newest"
            stmt = stmt.order_by(desc(Project.created_at))

        stmt = stmt.offset(skip).limit(limit)

        return list(db.scalars(stmt))

    @staticmethod
    @cached(ttl=300, key_prefix="proj")
    def list_owner_projects(
        db: Session,
        owner_id: uuid.UUID,
    ) -> list[Project]:

        stmt = (
            select(Project)
            .options(selectinload(Project.owner))
            .where(
                Project.owner_id == owner_id,
                Project.deleted_at.is_(None),
            )
        )

        return list(db.scalars(stmt))

    @staticmethod
    def update_project(
        db: Session,
        db_project: Project,
        project: ProjectUpdate,
    ) -> Project:

        data = project.model_dump(exclude_unset=True)

        from datetime import datetime, timezone
        from app.models.project import ProjectStatus
        from app.services.project_status_service import ProjectStatusService

        current_status = getattr(db_project, "status", None) or (
            ProjectStatus.ARCHIVED
            if db_project.is_archived
            else ProjectStatus.RECRUITING
        )

        if "status" in data and data["status"] is not None:
            new_status = data["status"]
            ProjectStatusService.validate_status_transition(current_status, new_status)
            if new_status == ProjectStatus.ARCHIVED:
                data["is_archived"] = True
            else:
                data["is_archived"] = False
        elif (
            "is_archived" in data
            and data["is_archived"] is True
            and not db_project.is_archived
        ):
            ProjectStatusService.validate_status_transition(
                current_status, ProjectStatus.ARCHIVED
            )
            data["status"] = ProjectStatus.ARCHIVED
        elif (
            "is_archived" in data
            and data["is_archived"] is False
            and db_project.is_archived
        ):
            ProjectStatusService.validate_status_transition(
                current_status, ProjectStatus.DRAFT
            )
            data["status"] = ProjectStatus.DRAFT

        if "scheduled_publish_at" in data and data["scheduled_publish_at"] is not None:
            data["is_published"] = data["scheduled_publish_at"] <= datetime.now(
                timezone.utc
            )

        for key, value in data.items():
            setattr(db_project, key, value)

        db.flush()
        db.refresh(db_project)

        ActivityService.record_activity(
            db=db,
            actor_id=db_project.owner_id,
            activity_type=ActivityType.PROJECT_UPDATED,
            title="Updated project",
            description=db_project.title,
            target_id=db_project.id,
            target_type="project",
            icon="pencil",
            color="info",
        )

        from sqlalchemy import select
        from app.models.project_member import ProjectMember
        from app.services.notification_service import NotificationService

        members = db.scalars(
            select(ProjectMember).where(ProjectMember.project_id == db_project.id)
        ).all()
        for member in members:
            if member.user_id != db_project.owner_id:
                NotificationService.create_project_activity_notification(
                    db=db,
                    recipient_id=member.user_id,
                    actor_id=db_project.owner_id,
                    project_id=db_project.id,
                    title="Project Updated",
                    message=f"The project '{db_project.title}' has been updated.",
                    action_url=f"/projects/{db_project.id}",
                )

        return db_project

    @staticmethod
    def archive_project(
        db: Session,
        db_project: Project,
    ) -> Project:
        from app.models.project import ProjectStatus
        from app.services.project_status_service import ProjectStatusService

        current_status = getattr(db_project, "status", None) or (
            ProjectStatus.ARCHIVED
            if db_project.is_archived
            else ProjectStatus.RECRUITING
        )
        ProjectStatusService.validate_status_transition(
            current_status, ProjectStatus.ARCHIVED
        )

        db_project.status = ProjectStatus.ARCHIVED.value
        db_project.is_archived = True

        db.commit()
        db.refresh(db_project)

        ActivityService.record_activity(
            db=db,
            actor_id=db_project.owner_id,
            activity_type=ActivityType.PROJECT_ARCHIVED,
            title="Archived project",
            description=db_project.title,
            target_id=db_project.id,
            target_type="project",
            icon="archive",
            color="warning",
        )

        return db_project

    @staticmethod
    def restore_project(
        db: Session,
        db_project: Project,
    ) -> Project:
        from app.models.project import ProjectStatus
        from app.services.project_status_service import ProjectStatusService

        current_status = (
            ProjectStatus.ARCHIVED
            if db_project.is_archived
            else (getattr(db_project, "status", None) or ProjectStatus.RECRUITING)
        )
        ProjectStatusService.validate_status_transition(
            current_status, ProjectStatus.DRAFT
        )

        db_project.status = ProjectStatus.DRAFT.value
        db_project.is_archived = False

        db.commit()
        db.refresh(db_project)

        return db_project

    @staticmethod
    def feature_project(
        db: Session,
        db_project: Project,
    ) -> Project:

        db_project.is_featured = True

        db.flush()
        db.refresh(db_project)

        return db_project

    @staticmethod
    def increment_views(
        db: Session,
        db_project: Project,
    ) -> None:

        db_project.views += 1
        db.commit()

    @staticmethod
    def increment_stars(
        db: Session,
        db_project: Project,
    ) -> None:

        db_project.stars += 1
        db.flush()

    @staticmethod
    def decrement_stars(
        db: Session,
        db_project: Project,
    ) -> None:

        if db_project.stars > 0:
            db_project.stars -= 1

        db.flush()

    @staticmethod
    def get_project_stats(
        db: Session,
        project_id: uuid.UUID,
    ) -> ProjectStatsResponse:
        from sqlalchemy import func, select

        from app.models.application import Application
        from app.models.bookmark import Bookmark
        from app.models.project_member import MemberRole, ProjectMember

        project = db.get(Project, project_id)
        assert project is not None

        applicants = (
            db.scalar(
                select(func.count())
                .select_from(Application)
                .where(Application.project_id == project_id)
            )
            or 0
        )

        accepted_members = (
            db.scalar(
                select(func.count())
                .select_from(ProjectMember)
                .where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.is_active.is_(True),
                    ProjectMember.role != MemberRole.OWNER,
                )
            )
            or 0
        )

        bookmark_count = (
            db.scalar(
                select(func.count())
                .select_from(Bookmark)
                .where(
                    Bookmark.target_type == "project",
                    Bookmark.target_id == project_id,
                )
            )
            or 0
        )

        return ProjectStatsResponse(
            project_id=project_id,
            views=project.views,
            applicants=applicants,
            accepted_members=accepted_members,
            bookmark_count=bookmark_count,
        )

    @staticmethod
    def find_similar_projects(
        db: Session,
        title: str,
        description: str,
        title_threshold: float = 0.75,
        description_threshold: float = 0.65,
    ) -> list[SimilarProjectWarning]:
        from difflib import SequenceMatcher

        candidates = list(
            db.scalars(select(Project).where(Project.is_archived.is_(False)))
        )

        results = []
        title_lower = title.lower()
        desc_lower = description.lower()

        for project in candidates:
            title_sim = SequenceMatcher(
                None, title_lower, project.title.lower()
            ).ratio()
            desc_sim = SequenceMatcher(
                None, desc_lower, project.description.lower()
            ).ratio()

            if title_sim >= title_threshold or desc_sim >= description_threshold:
                results.append(
                    SimilarProjectWarning(
                        id=project.id,
                        title=project.title,
                        slug=project.slug,
                        title_similarity=round(title_sim, 2),
                        description_similarity=round(desc_sim, 2),
                    )
                )

        return results

    @staticmethod
    def soft_delete_project(
        db: Session,
        db_project: Project,
        deleted_by_id: uuid.UUID,
    ) -> None:
        """Mark a project as deleted without removing the row."""
        db_project.deleted_at = func.now()
        db_project.deleted_by_id = deleted_by_id
        db.commit()

    @staticmethod
    def restore_soft_deleted_project(
        db: Session,
        db_project: Project,
    ) -> Project:
        """Restore a soft-deleted project."""
        db_project.deleted_at = None
        db_project.deleted_by_id = None
        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def hard_delete_project(
        db: Session,
        db_project: Project,
    ) -> None:
        """Permanently remove a project from the database (admin only)."""
        from app.models.project_member import ProjectMember

        # Explicitly delete member rows first to avoid SQLAlchemy FK nullification
        db.query(ProjectMember).filter(
            ProjectMember.project_id == db_project.id
        ).delete(synchronize_session=False)
        db.delete(db_project)
        db.flush()

    @staticmethod
    def create_draft(
        db: Session,
        owner_id: uuid.UUID,
        project: ProjectDraftCreate,
    ) -> Project:

        from datetime import datetime, timezone

        db_project = Project(
            owner_id=owner_id,
            title=project.title,
            slug=project.slug,
            description=project.description or "",
            tagline=project.tagline,
            stage=project.stage,
            visibility=project.visibility,
            tech_stack=project.tech_stack,
            repository_url=project.repository_url,
            website_url=project.website_url,
            demo_url=project.demo_url,
            team_size=project.team_size,
            max_team_size=project.max_team_size,
            hiring=project.hiring,
            logo_url=project.logo_url,
            banner_url=project.banner_url,
            is_draft=True,
            last_draft_save=datetime.now(timezone.utc),
        )

        db.add(db_project)
        db.flush()
        db.refresh(db_project)

        from app.models.project_member import ProjectMember, MemberRole

        member = ProjectMember(
            project_id=db_project.id,
            user_id=owner_id,
            role=MemberRole.OWNER,
            is_active=True,
        )
        db.add(member)
        db.commit()

        return db_project

    @staticmethod
    def update_draft(
        db: Session,
        db_project: Project,
        project: ProjectDraftUpdate,
    ) -> Project:

        from datetime import datetime, timezone

        data = project.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_project, key, value)

        db_project.last_draft_save = datetime.now(timezone.utc)

        db.flush()
        db.refresh(db_project)

        return db_project

    @staticmethod
    def publish_draft(
        db: Session,
        db_project: Project,
    ) -> Project:

        if not db_project.title or not db_project.slug:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400,
                detail="Title and slug are required to publish a project",
            )

        if (
            ProjectService.get_by_slug(db, db_project.slug)
            and ProjectService.get_by_slug(db, db_project.slug).id != db_project.id
        ):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400,
                detail="Project slug already exists",
            )

        db_project.is_draft = False
        db_project.last_draft_save = None

        db.flush()
        db.refresh(db_project)

        ActivityService.record_activity(
            db=db,
            actor_id=db_project.owner_id,
            activity_type=ActivityType.PROJECT_CREATED,
            title="Published project",
            description=db_project.title,
            target_id=db_project.id,
            target_type="project",
            icon="folder-plus",
            color="primary",
        )

        return db_project
