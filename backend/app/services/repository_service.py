from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryUpdate,
)


class RepositoryService:
    """
    Business logic for repository operations.
    """

    @staticmethod
    def connect_repository(
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        repository: RepositoryCreate,
    ) -> Repository:

        db_repository = Repository(
            project_id=project_id,
            connected_by=user_id,
            provider=repository.provider,
            repository_id=repository.repository_id,
            owner=repository.owner,
            name=repository.name,
            full_name=repository.full_name,
            description=repository.description,
            default_branch=repository.default_branch,
            clone_url=repository.clone_url,
            html_url=repository.html_url,
            homepage=repository.homepage,
            language=repository.language,
            stars=repository.stars,
            forks=repository.forks,
            watchers=repository.watchers,
            open_issues=repository.open_issues,
            contributors=repository.contributors,
            is_private=repository.is_private,
        )

        db.add(db_repository)
        db.commit()
        db.refresh(db_repository)

        return db_repository

    @staticmethod
    def get_repository(
        db: Session,
        repository_id: uuid.UUID,
    ) -> Repository | None:

        return db.get(Repository, repository_id)

    @staticmethod
    def get_by_full_name(
        db: Session,
        full_name: str,
    ) -> Repository | None:

        stmt = (
            select(Repository)
            .where(Repository.full_name == full_name)
        )

        return db.scalar(stmt)

    @staticmethod
    def list_project_repositories(
        db: Session,
        project_id: uuid.UUID,
    ) -> list[Repository]:

        stmt = (
            select(Repository)
            .where(Repository.project_id == project_id)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_user_repositories(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[Repository]:

        stmt = (
            select(Repository)
            .where(Repository.connected_by == user_id)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def update_repository(
        db: Session,
        db_repository: Repository,
        repository: RepositoryUpdate,
    ) -> Repository:

        data = repository.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_repository, key, value)

        db.commit()
        db.refresh(db_repository)

        return db_repository

    @staticmethod
    def sync_repository(
        db: Session,
        db_repository: Repository,
        *,
        stars: int,
        forks: int,
        watchers: int,
        open_issues: int,
        contributors: int,
        language: str | None,
        default_branch: str,
    ) -> Repository:

        db_repository.stars = stars
        db_repository.forks = forks
        db_repository.watchers = watchers
        db_repository.open_issues = open_issues
        db_repository.contributors = contributors
        db_repository.language = language
        db_repository.default_branch = default_branch
        db_repository.synced = True

        db.commit()
        db.refresh(db_repository)

        return db_repository

    @staticmethod
    def mark_unsynced(
        db: Session,
        db_repository: Repository,
    ) -> Repository:

        db_repository.synced = False

        db.commit()
        db.refresh(db_repository)

        return db_repository

    @staticmethod
    def disconnect_repository(
        db: Session,
        db_repository: Repository,
    ) -> None:

        db.delete(db_repository)
        db.commit()