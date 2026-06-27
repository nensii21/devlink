from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if OrganizationService.get_by_slug(db, organization.slug):
        raise HTTPException(
            status_code=400,
            detail="Organization slug already exists",
        )

    return OrganizationService.create_organization(
        db=db,
        owner_id=current_user.id,
        organization=organization,
    )
    
@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def get_organization(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
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
def my_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return OrganizationService.list_owner_organizations(
        db,
        current_user.id,
    )
    
@router.get(
    "/search/{keyword}",
    response_model=list[OrganizationResponse],
)
def search_organizations(
    keyword: str,
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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

    return OrganizationService.update_organization(
        db,
        db_organization,
        organization,
    )
    
@router.patch(
    "/{organization_id}/verify",
    response_model=OrganizationResponse,
)
def verify_organization(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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

    OrganizationService.delete_organization(
        db,
        organization,
    )