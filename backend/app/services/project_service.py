from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


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

        return db_project

    @staticmethod
    def get_project(
        db: Session,
        project_id: uuid.UUID,
    ) -> Project | None:

        stmt = select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    @staticmethod
    def get_project_including_deleted(
        db: Session,
        project_id: uuid.UUID,
    ) -> Project | None:
        """Retrieve a project regardless of soft-delete status (admin use)."""
        return db.get(Project, project_id)

    @staticmethod
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> Project | None:

        stmt = select(Project).where(
            Project.slug == slug,
            Project.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    @staticmethod
    def list_projects(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Project]:

        stmt = (
            select(Project)
            .where(Project.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_owner_projects(
        db: Session,
        owner_id: uuid.UUID,
    ) -> list[Project]:

        stmt = select(Project).where(
            Project.owner_id == owner_id,
            Project.deleted_at.is_(None),
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

        db.commit()
        db.refresh(db_project)

        return db_project

    @staticmethod
    def archive_project(
        db: Session,
        db_project: Project,
    ) -> Project:

        db_project.is_archived = True

        db.commit()
        db.refresh(db_project)

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
        db.delete(db_project)
        db.commit()
