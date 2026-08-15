from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

# pyrefly: ignore [missing-import]

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user, require_org_permission
from app.middleware.rate_limit import limiter, SEARCH_LIMIT
from app.models.user import User
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    SlugCheckResponse,
)
from app.schemas.organization_member import (
    OrganizationMemberResponse,
    OrganizationMemberUpdate,
)
from app.services.organization_service import OrganizationService

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization(
    organization: OrganizationCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if OrganizationService.get_by_slug(db, organization.slug):
        raise HTTPException(
            status_code=400,
            detail="Organization slug already exists",
        )

    new_org = OrganizationService.create_organization(
        db=db,
        owner_id=current_user.id,
        organization=organization,
    )

    from app.services.audit_log_service import AuditLogService
    from app.models.audit_log import AuditAction

    AuditLogService.create_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.ORGANIZATION_CREATED,
        entity_type="organization",
        entity_id=str(new_org.id),
        organization_id=new_org.id,
        new_values=organization.model_dump(exclude_unset=True),
    )

    return new_org


@router.get(
    "/check-slug/{slug}",
    response_model=SlugCheckResponse,
)
def check_slug_availability(
    slug: str,
    db: Session = Depends(get_database),
):
    existing = OrganizationService.get_by_slug(db, slug)
    return SlugCheckResponse(
        slug=slug,
        available=existing is None,
    )


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def get_organization(
    organization_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    organization = OrganizationService.get_organization(
        db,
        organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    return organization


@router.get(
    "/slug/{slug}",
    response_model=OrganizationResponse,
)
def get_organization_by_slug(
    slug: str,
    db: Session = Depends(get_database),
):

    organization = OrganizationService.get_by_slug(
        db,
        slug,
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    return organization


@router.get(
    "/",
    response_model=list[OrganizationResponse],
)
@limiter.limit(SEARCH_LIMIT)
def list_organizations(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_database),
):

    return OrganizationService.list_organizations(
        db,
        skip,
        limit,
    )


@router.get(
    "/me",
    response_model=list[OrganizationResponse],
)
@limiter.limit(SEARCH_LIMIT)
def my_organizations(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return OrganizationService.list_owner_organizations(
        db,
        current_user.id,
    )


@router.get(
    "/search/{keyword}",
    response_model=list[OrganizationResponse],
)
@limiter.limit(SEARCH_LIMIT)
def search_organizations(
    request: Request,
    keyword: str,
    db: Session = Depends(get_database),
):

    return OrganizationService.search_organizations(
        db,
        keyword,
    )


@router.put(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def update_organization(
    organization_id: uuid.UUID,
    organization: OrganizationUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_org_permission("org:update")),
):

    db_organization = OrganizationService.get_organization(
        db,
        organization_id,
    )

    if db_organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    old_values = {}
    for key in organization.model_dump(exclude_unset=True).keys():
        old_values[key] = getattr(db_organization, key, None)

    updated_org = OrganizationService.update_organization(
        db,
        db_organization,
        organization,
    )

    from app.services.audit_log_service import AuditLogService
    from app.models.audit_log import AuditAction

    AuditLogService.create_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.ORGANIZATION_UPDATED,
        entity_type="organization",
        entity_id=str(updated_org.id),
        organization_id=updated_org.id,
        old_values=old_values,
        new_values=organization.model_dump(exclude_unset=True),
    )

    return updated_org


@router.patch(
    "/{organization_id}/verify",
    response_model=OrganizationResponse,
)
def verify_organization(
    organization_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_org_permission("org:update")),
):

    organization = OrganizationService.get_organization(
        db,
        organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    return OrganizationService.verify_organization(
        db,
        organization,
    )


@router.patch(
    "/{organization_id}/activate",
    response_model=OrganizationResponse,
)
def activate_organization(
    organization_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_org_permission("org:update")),
):

    organization = OrganizationService.get_organization(
        db,
        organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    return OrganizationService.activate_organization(
        db,
        organization,
    )


@router.patch(
    "/{organization_id}/deactivate",
    response_model=OrganizationResponse,
)
def deactivate_organization(
    organization_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_org_permission("org:update")),
):

    organization = OrganizationService.get_organization(
        db,
        organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    return OrganizationService.deactivate_organization(
        db,
        organization,
    )


@router.patch(
    "/{organization_id}/enable-hiring",
    response_model=OrganizationResponse,
)
def enable_hiring(
    organization_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_org_permission("org:update")),
):

    organization = OrganizationService.get_organization(
        db,
        organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    return OrganizationService.enable_hiring(
        db,
        organization,
    )


@router.patch(
    "/{organization_id}/disable-hiring",
    response_model=OrganizationResponse,
)
def disable_hiring(
    organization_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_org_permission("org:update")),
):

    organization = OrganizationService.get_organization(
        db,
        organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    return OrganizationService.disable_hiring(
        db,
        organization,
    )


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_organization(
    organization_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_org_permission("org:delete")),
):

    organization = OrganizationService.get_organization(
        db,
        organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    OrganizationService.soft_delete_organization(
        db,
        organization,
        deleted_by_id=current_user.id,
    )


@router.patch(
    "/{organization_id}/restore-soft-delete",
    response_model=OrganizationResponse,
)
def restore_organization_soft_delete(
    organization_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    organization = OrganizationService.get_organization_including_deleted(
        db, organization_id
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    if organization.deleted_at is None:
        raise HTTPException(
            status_code=400,
            detail="Organization is not deleted",
        )

    if organization.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )

    return OrganizationService.restore_soft_deleted_organization(
        db,
        organization,
    )


@router.delete(
    "/{organization_id}/hard",
    status_code=status.HTTP_204_NO_CONTENT,
)
def hard_delete_organization(
    organization_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only admins can permanently delete organizations",
        )

    organization = OrganizationService.get_organization_including_deleted(
        db, organization_id
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )

    OrganizationService.hard_delete_organization(
        db,
        organization,
    )

    from app.services.audit_log_service import AuditLogService
    from app.models.audit_log import AuditAction

    AuditLogService.create_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.ORGANIZATION_DELETED,
        entity_type="organization",
        entity_id=str(organization_id),
        organization_id=organization_id,
    )


@router.get(
    "/{organization_id}/members",
    response_model=list[OrganizationMemberResponse],
)
def list_organization_members(
    organization_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    organization = OrganizationService.get_organization(db, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Anyone authenticated can view members for now if the org is public,
    # but strictly speaking we could require "org:view_content" or similar.
    # We will just return the list.
    return OrganizationService.list_members(db, organization_id)


@router.patch(
    "/{organization_id}/members/{user_id}",
    response_model=OrganizationMemberResponse,
)
def update_member_role(
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    update: OrganizationMemberUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_org_permission("org:manage_roles")),
):
    organization = OrganizationService.get_organization(db, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    try:
        return OrganizationService.update_member_role(
            db, organization_id, user_id, update.role, current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{organization_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_organization_member(
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    organization = OrganizationService.get_organization(db, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    try:
        OrganizationService.remove_member(db, organization_id, user_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
