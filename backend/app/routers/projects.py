from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

# pyrefly: ignore [missing-import]
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.core.cache import cache_manager, cached
from app.dependencies import get_current_user, get_database, require_project_permission
from app.middleware.idempotency import IdempotentRoute
from app.middleware.rate_limit import PROJECT_LIMIT, limiter
from app.models.user import User
from app.schemas.ai import (
    ProjectDescriptionGenerateRequest,
    ProjectDescriptionGenerateResponse,
)
from app.schemas.duplicate_detection import (
    DuplicateProjectCheckRequest,
    DuplicateProjectCheckResponse,
)
from app.schemas.project import (
    ProjectCloneRequest,
    ProjectCreate,
    ProjectResponse,
    ProjectStatsResponse,
    ProjectUpdate,
    SimilarProjectWarning,
)
from app.schemas.project_audit import (
    PaginatedProjectAuditLogsResponse,
    ProjectAuditLogResponse,
)
from app.services.ai_service import AIService
from app.services.project_service import ProjectService

router = APIRouter(
    tags=["Projects"],
    route_class=IdempotentRoute,
)


@router.post(
    "/generate-description",
    response_model=ProjectDescriptionGenerateResponse,
    summary="Generate AI project description",
    description="Generates a comprehensive project description based on a short prompt.",
)
@limiter.limit(PROJECT_LIMIT)
def generate_project_description(
    request: Request,
    body: ProjectDescriptionGenerateRequest,
    current_user: User = Depends(get_current_user),
) -> ProjectDescriptionGenerateResponse:
    """Generate a project description using AI."""
    return AIService.generate_project_description(body)


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

    new_project = ProjectService.create_project(
        db=db,
        owner_id=current_user.id,
        project=project,
    )

    from app.models.audit_log import AuditAction
    from app.services.audit_log_service import AuditLogService

    AuditLogService.create_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.PROJECT_CREATED,
        entity_type="project",
        entity_id=str(new_project.id),
        project_id=new_project.id,
        new_values=project.model_dump(exclude_unset=True),
    )

    cache_manager.delete_pattern("projects:*")
    return new_project


@router.post(
    "/check-duplicate",
    response_model=DuplicateProjectCheckResponse,
    summary="Check AI-based duplicate projects",
    description="Compare project title, description, and tags against existing projects using semantic embedding and token similarity.",
)
def check_duplicate_project(
    req: DuplicateProjectCheckRequest,
    db: Session = Depends(get_database),
) -> DuplicateProjectCheckResponse:
    from app.services.duplicate_detection_service import DuplicateDetectionService

    return DuplicateDetectionService.find_duplicate_projects(
        db,
        title=req.title,
        description=req.description,
        tags=req.tags,
        threshold=req.similarity_threshold,
        limit=req.limit,
    )


@router.post(
    "/check-similarity",
    response_model=list[SimilarProjectWarning],
)
def check_project_similarity(
    project: ProjectCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    return ProjectService.find_similar_projects(
        db,
        title=project.title,
        description=project.description,
    )


from app.dependencies import (
    get_current_user,
    get_database,
    get_optional_current_user,
)
from app.schemas.project_analytics import ProjectAnalyticsResponse
from app.services.project_analytics_service import ProjectAnalyticsService


@router.get(
    "/{project_id}/analytics",
    response_model=ProjectAnalyticsResponse,
    summary="Get Project View Analytics",
)
def get_project_analytics(
    project_id: uuid.UUID,
    days: int = Query(
        30, ge=1, le=365, description="Number of days for daily views breakdown"
    ),
    db: Session = Depends(get_database),
):
    """
    Get project view analytics including total views, unique viewers, and daily views.
    """
    return ProjectAnalyticsService.get_analytics(db, project_id, days=days)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
@cached(ttl=60, key_prefix="projects:get")
def get_project(
    request: Request,
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
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

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    viewer_id = current_user.id if current_user else None

    ProjectAnalyticsService.record_view(
        db=db,
        project_id=project_id,
        viewer_id=viewer_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return project


@router.get(
    "/slug/{slug}",
    response_model=ProjectResponse,
)
@cached(ttl=60, key_prefix="projects:slug")
def get_project_by_slug(
    request: Request,
    slug: str,
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
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

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    viewer_id = current_user.id if current_user else None

    ProjectAnalyticsService.record_view(
        db=db,
        project_id=project.id,
        viewer_id=viewer_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return project


@router.get(
    "/",
    response_model=list[ProjectResponse],
)
@cached(ttl=120, key_prefix="projects:list")
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    language: str | None = Query(None),
    experience: str | None = Query(None),
    remote: bool | None = Query(None),
    paid: bool | None = Query(None),
    opensource: bool | None = Query(None),
    tech: str | None = Query(None),
    sort_by: str | None = Query(
        "newest",
        description="Sorting option: newest, oldest, most_active, most_bookmarked, most_applications, recently_updated, ai_match_score",
    ),
    db: Session = Depends(get_database),
):

    return ProjectService.list_projects(
        db,
        skip=skip,
        limit=limit,
        language=language,
        experience=experience,
        remote=remote,
        paid=paid,
        opensource=opensource,
        tech=tech,
        sort_by=sort_by,
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


@router.get(
    "/user/{user_id}",
    response_model=list[ProjectResponse],
    summary="List projects owned by a specific user",
)
def list_user_projects(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    return ProjectService.list_owner_projects(
        db,
        user_id,
    )


@router.post(
    "/{project_id}/clone",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone an existing project as a starting template",
)
@limiter.limit("10/minute")
def clone_project(
    request: Request,
    project_id: str,
    clone_data: ProjectCloneRequest | None = None,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    source_project = None
    try:
        val_uuid = uuid.UUID(project_id)
        source_project = ProjectService.get_project(db, val_uuid)
    except ValueError:
        source_project = ProjectService.get_by_slug(db, project_id)

    if (
        not source_project
        or getattr(source_project, "is_deleted", False)
        or getattr(source_project, "deleted_at", None) is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source project not found",
        )

    from app.models.project import ProjectVisibility

    if (
        source_project.visibility == ProjectVisibility.PRIVATE
        and source_project.owner_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to clone this private project",
        )

    cloned_project = ProjectService.clone_project(
        db=db,
        source_project=source_project,
        user=current_user,
        clone_data=clone_data,
    )
    cache_manager.delete_pattern("projects:*")
    return cloned_project


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

    old_values = {}
    new_values = project.model_dump(exclude_unset=True)
    for key in new_values.keys():
        val = getattr(db_project, key, None)
        old_values[key] = str(val) if hasattr(val, "value") else val

    updated_project = ProjectService.update_project(
        db,
        db_project,
        project,
    )

    from enum import Enum

    from app.models.audit_log import AuditAction
    from app.services.audit_log_service import AuditLogService

    # 1. Title update event
    if "title" in new_values and old_values.get("title") != new_values["title"]:
        AuditLogService.create_log(
            db=db,
            actor_id=current_user.id,
            action=AuditAction.PROJECT_TITLE_UPDATED,
            entity_type="project",
            entity_id=str(updated_project.id),
            project_id=updated_project.id,
            old_values={"title": old_values.get("title")},
            new_values={"title": new_values["title"]},
        )

    # 2. Description update event
    if (
        "description" in new_values
        and old_values.get("description") != new_values["description"]
    ):
        AuditLogService.create_log(
            db=db,
            actor_id=current_user.id,
            action=AuditAction.PROJECT_DESCRIPTION_UPDATED,
            entity_type="project",
            entity_id=str(updated_project.id),
            project_id=updated_project.id,
            old_values={"description": old_values.get("description")},
            new_values={"description": new_values["description"]},
        )

    # 3. Status/Stage change event
    status_keys = {"stage", "visibility", "is_published", "hiring"}
    if any(k in new_values for k in status_keys):
        changed_old = {
            k: (
                str(old_values[k])
                if isinstance(old_values.get(k), Enum)
                else old_values.get(k)
            )
            for k in status_keys
            if k in new_values
        }
        changed_new = {
            k: (
                str(new_values[k])
                if isinstance(new_values.get(k), Enum)
                else new_values.get(k)
            )
            for k in status_keys
            if k in new_values
        }
        AuditLogService.create_log(
            db=db,
            actor_id=current_user.id,
            action=AuditAction.PROJECT_STATUS_CHANGED,
            entity_type="project",
            entity_id=str(updated_project.id),
            project_id=updated_project.id,
            old_values=changed_old,
            new_values=changed_new,
        )

    AuditLogService.create_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.PROJECT_UPDATED,
        entity_type="project",
        entity_id=str(updated_project.id),
        project_id=updated_project.id,
        old_values=old_values,
        new_values=new_values,
    )

    cache_manager.delete_pattern("projects:*")
    return updated_project


@router.get(
    "/{project_id}/audit-trail",
    response_model=PaginatedProjectAuditLogsResponse,
    summary="Get Project Audit Trail",
    description="Retrieve paginated audit trail history of project events (creations, title/description updates, member changes, status changes, and archiving).",
)
def get_project_audit_trail(
    project_id: uuid.UUID,
    event_type: str | None = Query(None, description="Filter by event type substring"),
    user_id: uuid.UUID | None = Query(
        None, description="Filter by actor or target user ID"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_database),
    current_user: User = Depends(require_project_permission("project:read")),
) -> PaginatedProjectAuditLogsResponse:
    from app.services.audit_log_service import AuditLogService

    result = AuditLogService.search_project_audit_logs(
        db,
        project_id=project_id,
        user_id=user_id,
        event_type=event_type,
        page=page,
        limit=limit,
    )
    items = [ProjectAuditLogResponse.model_validate(log) for log in result["items"]]
    return PaginatedProjectAuditLogsResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        limit=result["limit"],
        pages=result["pages"],
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

    archived_project = ProjectService.archive_project(
        db,
        project,
    )

    from app.models.audit_log import AuditAction
    from app.services.audit_log_service import AuditLogService

    AuditLogService.create_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.PROJECT_ARCHIVED,
        entity_type="project",
        entity_id=str(archived_project.id),
        project_id=archived_project.id,
    )

    return archived_project


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

    restored_project = ProjectService.restore_project(
        db,
        project,
    )

    from app.models.audit_log import AuditAction
    from app.services.audit_log_service import AuditLogService

    AuditLogService.create_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.PROJECT_RESTORED,
        entity_type="project",
        entity_id=str(restored_project.id),
        project_id=restored_project.id,
    )

    return restored_project


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

    ProjectService.soft_delete_project(
        db,
        project,
        deleted_by_id=current_user.id,
    )

    from app.models.audit_log import AuditAction
    from app.services.audit_log_service import AuditLogService

    AuditLogService.create_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.PROJECT_DELETED,
        entity_type="project",
        entity_id=str(project_id),
        project_id=project_id,
    )

    cache_manager.delete_pattern("projects:*")


@router.post(
    "/{project_id}/invite/{user_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
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

    from sqlalchemy import and_, select

    from app.models.project_member import MemberRole, ProjectMember

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

    from app.services.notification_service import NotificationService

    NotificationService.create_project_invitation(
        db=db,
        recipient_id=user_id,
        actor_id=current_user.id,
        project_id=project_id,
        title="Project Invitation",
        message=f"You have been invited to join the project '{project.title}'.",
        action_url=f"/projects/{project_id}",
    )

    from app.models.audit_log import AuditAction
    from app.services.audit_log_service import AuditLogService

    AuditLogService.create_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.INVITATION_SENT,
        entity_type="project",
        entity_id=str(project_id),
        project_id=project_id,
        target_user_id=user_id,
    )

    cache_manager.delete_pattern("projects:*")
    return {"message": "User invited successfully"}


@router.delete(
    "/{project_id}/soft",
    status_code=status.HTTP_204_NO_CONTENT,
)
def soft_delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    project = ProjectService.get_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if project.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )

    ProjectService.soft_delete_project(
        db,
        project,
        deleted_by_id=current_user.id,
    )


@router.patch(
    "/{project_id}/restore-soft-delete",
    response_model=ProjectResponse,
)
def restore_project_soft_delete(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    project = ProjectService.get_project_including_deleted(db, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    if project.deleted_at is None:
        raise HTTPException(
            status_code=400,
            detail="Project is not deleted",
        )

    if project.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )

    return ProjectService.restore_soft_deleted_project(
        db,
        project,
    )


@router.delete(
    "/{project_id}/hard",
    status_code=status.HTTP_204_NO_CONTENT,
)
def hard_delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only admins can permanently delete projects",
        )

    project = ProjectService.get_project_including_deleted(db, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    ProjectService.hard_delete_project(
        db,
        project,
    )
