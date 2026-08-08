from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database, get_optional_current_user
from app.models.user import User
from app.schemas.project import ProjectResponse
from app.schemas.project_template import (
    ProjectTemplateCloneRequest,
    ProjectTemplateCreate,
    ProjectTemplateListResponse,
    ProjectTemplateResponse,
    ProjectTemplateUpdate,
)
from app.services.project_template_service import ProjectTemplateService

router = APIRouter(
    prefix="/templates",
    tags=["Project Templates Marketplace"],
)


@router.post(
    "",
    response_model=ProjectTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish a new Project Template",
)
def create_template(
    payload: ProjectTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    template = ProjectTemplateService.create_template(
        db=db,
        author_id=current_user.id,
        payload=payload,
    )
    detail = ProjectTemplateService.get_template_detail(
        db=db,
        template_id=template.id,
        current_user_id=current_user.id,
    )
    return detail


@router.get(
    "",
    response_model=ProjectTemplateListResponse,
    summary="List and search project templates",
)
def list_templates(
    search: Optional[str] = Query(None, description="Search term in title or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tag: Optional[str] = Query(None, description="Filter by tech stack tag"),
    sort_by: str = Query("popular", description="Sort by: popular, recent, clones"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_database),
):
    user_id = current_user.id if current_user else None
    items, total = ProjectTemplateService.list_templates(
        db=db,
        search=search,
        category=category,
        tag=tag,
        sort_by=sort_by,
        current_user_id=user_id,
        skip=skip,
        limit=limit,
    )
    return ProjectTemplateListResponse(templates=items, total=total)


@router.get(
    "/{template_id}",
    response_model=ProjectTemplateResponse,
    summary="Get project template by ID",
)
def get_template(
    template_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_database),
):
    user_id = current_user.id if current_user else None
    template = ProjectTemplateService.get_template_detail(
        db=db,
        template_id=template_id,
        current_user_id=user_id,
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project template not found.",
        )
    return template


@router.patch(
    "/{template_id}",
    response_model=ProjectTemplateResponse,
    summary="Update project template",
)
def update_template(
    template_id: uuid.UUID,
    payload: ProjectTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    updated = ProjectTemplateService.update_template(
        db=db,
        template_id=template_id,
        user_id=current_user.id,
        payload=payload,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or unauthorized.",
        )
    return ProjectTemplateService.get_template_detail(
        db=db,
        template_id=template_id,
        current_user_id=current_user.id,
    )


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project template",
)
def delete_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    deleted = ProjectTemplateService.delete_template(
        db=db,
        template_id=template_id,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or unauthorized.",
        )


@router.post(
    "/{template_id}/favorite",
    summary="Toggle favorite status for template",
)
def toggle_favorite(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    try:
        is_favorited, stars_count = ProjectTemplateService.toggle_favorite(
            db=db,
            template_id=template_id,
            user_id=current_user.id,
        )
        return {
            "success": True,
            "is_favorited": is_favorited,
            "stars_count": stars_count,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post(
    "/{template_id}/clone",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone project template into a new project",
)
def clone_template(
    template_id: uuid.UUID,
    payload: ProjectTemplateCloneRequest = ProjectTemplateCloneRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    try:
        project = ProjectTemplateService.clone_template(
            db=db,
            template_id=template_id,
            user_id=current_user.id,
            new_project_title=payload.new_project_title,
            description=payload.description,
        )
        return project
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
