from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import ActivityType
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
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
        db.commit()
        db.refresh(db_project)

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
    def get_project(
        db: Session,
        project_id: uuid.UUID,
    ) -> Project | None:

        return db.get(Project, project_id)

    @staticmethod
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> Project | None:

        stmt = select(Project).where(Project.slug == slug)
        return db.scalar(stmt)

    @staticmethod
    def list_projects(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Project]:

        stmt = select(Project).offset(skip).limit(limit)

        return list(db.scalars(stmt))

    @staticmethod
    def list_owner_projects(
        db: Session,
        owner_id: uuid.UUID,
    ) -> list[Project]:

        stmt = select(Project).where(Project.owner_id == owner_id)

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

        db.commit()
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

        db.commit()
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

        db.commit()
        db.refresh(db_project)

        return db_project

    @staticmethod
    def feature_project(
        db: Session,
        db_project: Project,
    ) -> Project:

        db_project.is_featured = True

        db.commit()
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
        db.commit()

    @staticmethod
    def decrement_stars(
        db: Session,
        db_project: Project,
    ) -> None:

        if db_project.stars > 0:
            db_project.stars -= 1

        db.commit()

    @staticmethod
    def delete_project(
        db: Session,
        db_project: Project,
    ) -> None:

        db.delete(db_project)
        db.commit()
