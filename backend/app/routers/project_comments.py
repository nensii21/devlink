"""
API Router for Project Discussions (#930)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.dependencies import (
    get_current_active_user,
    get_database,
    get_optional_current_user,
)
from app.models.project_comment import ProjectComment
from app.models.user import User
from app.schemas.project_comment import (
    DELETED_BODY_PLACEHOLDER,
    ProjectCommentCreate,
    ProjectCommentList,
    ProjectCommentResponse,
    ProjectCommentThread,
    ProjectCommentUpdate,
)
from app.services.project_comment_service import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    ProjectCommentService,
)

router = APIRouter(
    prefix="/projects/{project_id}/comments",
    tags=["Project Comments"],
)


def _to_response(comment: ProjectComment) -> ProjectCommentResponse:
    """Serialise a comment, tombstoning the body if it was deleted.

    The row is kept so replies do not lose their parent, but the text is not
    handed back -- "deleted" has to mean the words are gone.
    """
    deleted = comment.deleted_at is not None

    return ProjectCommentResponse(
        id=comment.id,
        project_id=comment.project_id,
        parent_id=comment.parent_id,
        body=DELETED_BODY_PLACEHOLDER if deleted else comment.body,
        author=None if deleted else comment.author,
        is_edited=comment.is_edited,
        edited_at=comment.edited_at,
        is_deleted=deleted,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


def _to_thread(comment: ProjectComment) -> ProjectCommentThread:
    replies = ProjectCommentService.visible_replies(comment)
    base = _to_response(comment)

    return ProjectCommentThread(
        **base.model_dump(),
        replies=[_to_response(reply) for reply in replies],
        reply_count=len(replies),
    )


@router.get(
    "",
    response_model=ProjectCommentList,
    summary="List project comments",
    description=(
        "Top-level comments for a project, newest first, each with its "
        "replies. Comments on a private project are only visible to people "
        "who can see the project."
    ),
)
@router.get("/", response_model=ProjectCommentList, include_in_schema=False)
def list_comments(
    project_id: uuid.UUID,
    limit: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Top-level comments per page.",
    ),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
) -> ProjectCommentList:
    project = ProjectCommentService.get_project_or_404(db, project_id)
    ProjectCommentService.require_can_view(db, project, current_user)

    comments, total = ProjectCommentService.list_thread(
        db, project_id, limit=limit, offset=offset
    )

    return ProjectCommentList(
        items=[_to_thread(comment) for comment in comments],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/count",
    response_model=dict,
    summary="Count project comments",
    description="Live comments on the project, replies included.",
)
def count_comments(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
) -> dict:
    project = ProjectCommentService.get_project_or_404(db, project_id)
    ProjectCommentService.require_can_view(db, project, current_user)

    return {"count": ProjectCommentService.count_comments(db, project_id)}


@router.post(
    "",
    response_model=ProjectCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Post a comment or reply",
    description=(
        "Add a comment to the project discussion. Pass `parent_id` to reply. "
        "Replies are one level deep -- replying to a reply attaches to its "
        "parent instead."
    ),
)
@router.post(
    "/",
    response_model=ProjectCommentResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_comment(
    project_id: uuid.UUID,
    payload: ProjectCommentCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> ProjectCommentResponse:
    project = ProjectCommentService.get_project_or_404(db, project_id)
    ProjectCommentService.require_can_view(db, project, current_user)

    comment = ProjectCommentService.create_comment(db, project, payload, current_user)
    db.commit()
    db.refresh(comment)

    return _to_response(comment)


@router.patch(
    "/{comment_id}",
    response_model=ProjectCommentResponse,
    summary="Edit a comment",
    description="Authors may edit their own comments. Nobody else can.",
)
def update_comment(
    project_id: uuid.UUID,
    comment_id: uuid.UUID,
    payload: ProjectCommentUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> ProjectCommentResponse:
    project = ProjectCommentService.get_project_or_404(db, project_id)
    ProjectCommentService.require_can_view(db, project, current_user)

    comment = ProjectCommentService.get_comment_or_404(db, project_id, comment_id)
    ProjectCommentService.require_can_edit(comment, current_user)

    comment = ProjectCommentService.update_comment(db, comment, payload)
    db.commit()
    db.refresh(comment)

    return _to_response(comment)


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment",
    description=(
        "Soft delete. Authors may remove their own comments; a project owner "
        "may remove any comment on their project. The row is tombstoned so "
        "replies underneath keep their context."
    ),
)
def delete_comment(
    project_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    project = ProjectCommentService.get_project_or_404(db, project_id)
    ProjectCommentService.require_can_view(db, project, current_user)

    comment = ProjectCommentService.get_comment_or_404(db, project_id, comment_id)
    ProjectCommentService.require_can_delete(db, project, comment, current_user)

    ProjectCommentService.delete_comment(db, comment, current_user)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
