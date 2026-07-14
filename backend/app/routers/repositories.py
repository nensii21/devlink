from __future__ import annotations

import uuid

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryResponse,
    RepositoryUpdate,
)
from app.services.repository_service import RepositoryService

router = APIRouter(
    prefix="/repositories",
    tags=["Repositories"],
)


@router.post(
    "/",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def connect_repository(
    repository: RepositoryCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    if RepositoryService.get_by_full_name(
        db,
        repository.full_name,
    ):
        raise HTTPException(
            status_code=400,
            detail="Repository already connected",
        )

    return RepositoryService.connect_repository(
        db=db,
        project_id=repository.project_id,
        user_id=current_user.id,
        repository=repository,
    )


@router.get(
    "/{repository_id}",
    response_model=RepositoryResponse,
)
def get_repository(
    repository_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    repository = RepositoryService.get_repository(
        db,
        repository_id,
    )

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return repository


@router.get(
    "/project/{project_id}",
    response_model=list[RepositoryResponse],
)
def list_project_repositories(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return RepositoryService.list_project_repositories(
        db,
        project_id,
    )


@router.get(
    "/me",
    response_model=list[RepositoryResponse],
)
def my_repositories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return RepositoryService.list_user_repositories(
        db,
        current_user.id,
    )


@router.put(
    "/{repository_id}",
    response_model=RepositoryResponse,
)
def update_repository(
    repository_id: uuid.UUID,
    repository: RepositoryUpdate,
    db: Session = Depends(get_database),
):

    db_repository = RepositoryService.get_repository(
        db,
        repository_id,
    )

    if db_repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return RepositoryService.update_repository(
        db,
        db_repository,
        repository,
    )


@router.patch(
    "/{repository_id}/sync",
    response_model=RepositoryResponse,
)
def sync_repository(
    repository_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    repository = RepositoryService.get_repository(
        db,
        repository_id,
    )

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return RepositoryService.sync_repository(
        db=db,
        db_repository=repository,
        stars=repository.stars,
        forks=repository.forks,
        watchers=repository.watchers,
        open_issues=repository.open_issues,
        contributors=repository.contributors,
        language=repository.language,
        default_branch=repository.default_branch,
    )


@router.patch(
    "/{repository_id}/unsync",
    response_model=RepositoryResponse,
)
def mark_unsynced(
    repository_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    repository = RepositoryService.get_repository(
        db,
        repository_id,
    )

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return RepositoryService.mark_unsynced(
        db,
        repository,
    )


@router.delete(
    "/{repository_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def disconnect_repository(
    repository_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    repository = RepositoryService.get_repository(
        db,
        repository_id,
    )

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    RepositoryService.disconnect_repository(
        db,
        repository,
    )
