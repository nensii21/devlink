from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

# pyrefly: ignore [missing-import]

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user, require_project_permission
from app.middleware.rate_limit import limiter, PROJECT_LIMIT
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectStatsResponse,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

from app.middleware.idempotency import IdempotentRoute

router = APIRouter(
    tags=["Projects"],
    route_class=IdempotentRoute,
)


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(PROJECT_LIMIT)
def create_project(
    request: Request,
    project: ProjectCreate,
    db: Session = Depends(get_database),
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
    db: Session = Depends(get_database),
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
    db: Session = Depends(get_database),
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

    ProjectService.increment_views(
        db,
        project,
    )

    return project


@router.get(
    "/",
    response_model=list[ProjectResponse],
)
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_database),
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
    db: Session = Depends(get_database),
):

    return ProjectService.list_owner_projects(
        db,
        current_user.id,
    )


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
)
@limiter.limit("30/minute")
def update_project(
    request: Request,
    project_id: uuid.UUID,
    project: ProjectUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_project_permission("project:update")),
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

    return ProjectService.update_project(
        db,
        db_project,
        project,
    )


@router.patch(
    "/{project_id}/archive",
    response_model=ProjectResponse,
)
@limiter.limit("20/minute")
def archive_project(
    request: Request,
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_project_permission("project:archive")),
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

    return ProjectService.archive_project(
        db,
        project,
    )


@router.patch(
    "/{project_id}/restore",
    response_model=ProjectResponse,
)
@limiter.limit("20/minute")
def restore_project(
    request: Request,
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_project_permission("project:restore")),
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

    return ProjectService.restore_project(
        db,
        project,
    )


@router.patch(
    "/{project_id}/feature",
    response_model=ProjectResponse,
)
@limiter.limit("20/minute")
def feature_project(
    request: Request,
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
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
@limiter.limit("30/minute")
def star_project(
    request: Request,
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
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


@router.get(
    "/{project_id}/stats",
    response_model=ProjectStatsResponse,
)
def get_project_stats(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    project = ProjectService.get_project(db, project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    return ProjectService.get_project_stats(db, project_id)


@router.delete(
    "/{project_id}/star",
)
@limiter.limit("30/minute")
def unstar_project(
    request: Request,
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
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
@limiter.limit("20/minute")
def delete_project(
    request: Request,
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_project_permission("project:delete")),
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

    ProjectService.delete_project(
        db,
        project,
    )


@router.post(
    "/{project_id}/invite/{user_id}",
    status_code=status.HTTP_201_CREATED,
)
def invite_user(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    project = ProjectService.get_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the project owner can invite members",
        )

    from app.models.project_member import ProjectMember, MemberRole

    # pyrefly: ignore [missing-import]
    from sqlalchemy import and_, select

    existing_member = db.scalar(
        select(ProjectMember).where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
    )
    if existing_member:
        raise HTTPException(
            status_code=400,
            detail="User is already invited or a member of the project",
        )

    new_member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=MemberRole.MEMBER,
        is_active=False,
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    from app.models.notification import NotificationType
    from app.schemas.notification import NotificationCreate
    from app.services.notification_service import NotificationService

    notification_data = NotificationCreate(
        recipient_id=user_id,
        type=NotificationType.PROJECT_INVITE,
        title="Project Invitation",
        message=f"You have been invited to join the project '{project.title}'.",
        action_url=f"/projects/{project_id}",
        project_id=project_id,
    )
    NotificationService.create_notification(
        db=db,
        recipient_id=user_id,
        sender_id=current_user.id,
        notification=notification_data,
    )

    return {"message": "User invited successfully"}
