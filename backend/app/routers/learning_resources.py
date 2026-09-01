import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.models.project import Project
from app.models.user import User
from app.schemas.learning_resource import (
    LearningResourceCreate,
    LearningResourceUpdate,
    LearningResourceResponse,
    LearningResourceListResponse,
    LearningResourceStatsResponse,
    VoteRequest,
)
from app.services.learning_resource_service import LearningResourceService

router = APIRouter(
    prefix="/learning-resources",
    tags=["Learning Resources"],
)


@router.post(
    "/project/{project_id}",
    response_model=LearningResourceResponse,
    status_code=201,
    summary="Add a learning resource to a project",
)
def create_resource(
    project_id: uuid.UUID,
    body: LearningResourceCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    resource = LearningResourceService.create(db, project_id, current_user.id, body)
    return resource


@router.get(
    "/project/{project_id}",
    response_model=LearningResourceListResponse,
    summary="List learning resources for a project",
)
def list_resources(
    project_id: uuid.UUID,
    category: Optional[str] = Query(None, max_length=50),
    difficulty: Optional[str] = Query(None, max_length=20),
    language: Optional[str] = Query(None, max_length=50),
    search: Optional[str] = Query(None, max_length=200),
    sort_by: str = Query("newest", regex="^(newest|votes|popular)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_database),
):
    result = LearningResourceService.list_resources(
        db,
        project_id,
        category=category,
        difficulty=difficulty,
        language=language,
        search=search,
        sort_by=sort_by,
        page=page,
        limit=limit,
    )
    return result


@router.get(
    "/project/{project_id}/stats",
    response_model=LearningResourceStatsResponse,
    summary="Get learning resource statistics for a project",
)
def get_stats(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    return LearningResourceService.get_stats(db, project_id)


@router.get(
    "/{resource_id}",
    response_model=LearningResourceResponse,
    summary="Get a single learning resource",
)
def get_resource(
    resource_id: str,
    db: Session = Depends(get_database),
):
    data = LearningResourceService.get_with_author(db, resource_id)
    if not data:
        raise HTTPException(status_code=404, detail="Resource not found")
    LearningResourceService.increment_view(db, resource_id)
    resource = data["resource"]
    return {
        "id": resource.id,
        "project_id": resource.project_id,
        "author_id": resource.author_id,
        "author_name": data["author_name"],
        "title": resource.title,
        "url": resource.url,
        "description": resource.description,
        "category": resource.category,
        "language": resource.language,
        "difficulty": resource.difficulty,
        "is_external": resource.is_external,
        "is_pinned": resource.is_pinned,
        "view_count": resource.view_count + 1,
        "vote_score": resource.vote_score,
        "created_at": resource.created_at,
        "updated_at": resource.updated_at,
    }


@router.patch(
    "/{resource_id}",
    response_model=LearningResourceResponse,
    summary="Update a learning resource",
)
def update_resource(
    resource_id: str,
    body: LearningResourceUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    resource = LearningResourceService.update(db, resource_id, current_user.id, body)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found or not owned by you")
    return resource


@router.delete(
    "/{resource_id}",
    status_code=204,
    summary="Delete a learning resource",
)
def delete_resource(
    resource_id: str,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    deleted = LearningResourceService.delete(db, resource_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resource not found or not owned by you")


@router.post(
    "/{resource_id}/vote",
    summary="Vote on a learning resource",
)
def vote_resource(
    resource_id: str,
    body: VoteRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    result = LearningResourceService.vote(db, resource_id, current_user.id, body)
    if not result:
        raise HTTPException(status_code=404, detail="Resource not found")
    return result


@router.patch(
    "/{resource_id}/pin",
    summary="Toggle pin status on a learning resource",
)
def toggle_pin(
    resource_id: str,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    resource = LearningResourceService.toggle_pin(db, resource_id, current_user.id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found or not owned by you")
    return {"id": resource.id, "is_pinned": resource.is_pinned}
