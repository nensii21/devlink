from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if ProjectService.get_by_slug(db, project.slug):
        raise HTTPException(
            status_code=400,
            detail="Project slug already exists",
        )

    return ProjectService.create_project(
        db=db,
        owner_id=current_user.id,
        project=project,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    project = ProjectService.get_project(
        db,
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    ProjectService.increment_views(
        db,
        project,
    )

    return project


@router.get(
    "/slug/{slug}",
    response_model=ProjectResponse,
)
def get_project_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):

    project = ProjectService.get_by_slug(
        db,
        slug,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project


@router.get(
    "/",
    response_model=list[ProjectResponse],
)
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):

    return ProjectService.list_projects(
        db,
        skip,
        limit,
    )


@router.get(
    "/me/list",
    response_model=list[ProjectResponse],
)
def my_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return ProjectService.list_owner_projects(
        db,
        current_user.id,
    )


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_project(
    project_id: uuid.UUID,
    project: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    db_project = ProjectService.get_project(
        db,
        project_id,
    )

    if db_project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if db_project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )

    return ProjectService.update_project(
        db,
        db_project,
        project,
    )


@router.patch(
    "/{project_id}/archive",
    response_model=ProjectResponse,
)
def archive_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    project = ProjectService.get_project(
        db,
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )

    return ProjectService.archive_project(
        db,
        project,
    )


@router.patch(
    "/{project_id}/restore",
    response_model=ProjectResponse,
)
def restore_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    project = ProjectService.get_project(
        db,
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )

    return ProjectService.restore_project(
        db,
        project,
    )


@router.patch(
    "/{project_id}/feature",
    response_model=ProjectResponse,
)
def feature_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    project = ProjectService.get_project(
        db,
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return ProjectService.feature_project(
        db,
        project,
    )


@router.post(
    "/{project_id}/star",
)
def star_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    project = ProjectService.get_project(
        db,
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    ProjectService.increment_stars(
        db,
        project,
    )

    return {
        "message": "Project starred",
    }


@router.delete(
    "/{project_id}/star",
)
def unstar_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    project = ProjectService.get_project(
        db,
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    ProjectService.decrement_stars(
        db,
        project,
    )

    return {
        "message": "Project unstarred",
    }


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    project = ProjectService.get_project(
        db,
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )

    ProjectService.delete_project(
        db,
        project,
    )
