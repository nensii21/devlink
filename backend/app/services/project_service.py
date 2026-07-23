from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.activity import ActivityType
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.activity_service import ActivityService
from app.core.cache import cached
from app.schemas.project import (
    ProjectCreate,
    ProjectDraftCreate,
    ProjectDraftUpdate,
    ProjectStatsResponse,
    ProjectUpdate,
)


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

        db_project = Project(
            owner_id=owner_id,
            title=project.title,
            slug=project.slug,
            tagline=project.tagline,
            description=project.description,
            stage=project.stage,
            visibility=project.visibility,
            tech_stack=project.tech_stack,
            repository_url=project.repository_url,
            website_url=project.website_url,
            demo_url=project.demo_url,
            team_size=project.team_size,
            max_team_size=project.max_team_size,
            hiring=project.hiring,
        )

        db.add(db_project)
        db.flush()
        db.refresh(db_project)

        # Create ProjectMember record for owner
        from app.models.project_member import ProjectMember, MemberRole

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
            project_id=db_project.id,
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

        return db.get(Project, project_id)

    @staticmethod
    @cached(ttl=300, key_prefix="proj")
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> Project | None:

        stmt = (
            select(Project)
            .options(selectinload(Project.owner))
            .where(Project.slug == slug)
        )
        return db.scalar(stmt)

    @staticmethod
    @cached(ttl=300, key_prefix="proj")
    def list_projects(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Project]:

        stmt = (
            select(Project)
            .options(selectinload(Project.owner))
            .offset(skip)
            .limit(limit)
        )

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
            .where(Project.owner_id == owner_id)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def update_project(
        db: Session,
        db_project: Project,
        project: ProjectUpdate,
    ) -> Project:

        data = project.model_dump(exclude_unset=True)

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
            project_id=db_project.id,
            icon="pencil",
            color="info",
        )

        return db_project

    @staticmethod
    def archive_project(
        db: Session,
        db_project: Project,
    ) -> Project:

        db_project.is_archived = True

        db.flush()
        db.refresh(db_project)

        ActivityService.record_activity(
            db=db,
            actor_id=db_project.owner_id,
            activity_type=ActivityType.PROJECT_ARCHIVED,
            title="Archived project",
            description=db_project.title,
            project_id=db_project.id,
            icon="archive",
            color="warning",
        )

        return db_project

    @staticmethod
    def restore_project(
        db: Session,
        db_project: Project,
    ) -> Project:

        db_project.is_archived = False

        db.flush()
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
        from app.models.project_member import ProjectMember, MemberRole

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
                .where(Bookmark.project_id == project_id)
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
    def delete_project(
        db: Session,
        db_project: Project,
    ) -> None:
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
            project_id=db_project.id,
            icon="folder-plus",
            color="primary",
        )

        return db_project
