from __future__ import annotations

"""
API Router for project release notes (#1043).
"""

import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.dependencies import (
    get_current_active_user,
    get_database,
    get_optional_current_user,
)
from app.models.user import User
from app.schemas.project_release import (
    ReleaseCreate,
    ReleaseList,
    ReleaseResponse,
    ReleaseUpdate,
)
from app.services.project_release_service import ProjectReleaseService

router = APIRouter(
    prefix="/projects/{project_id}/releases",
    tags=["Project Releases"],
)


@router.get(
    "",
    response_model=ReleaseList,
    summary="List a project's releases",
    description=(
        "Published releases, pinned first then newest. Maintainers can pass "
        "`include_drafts=true` to see unpublished entries; for everyone else "
        "the flag is ignored."
    ),
)
@router.get("/", response_model=ReleaseList, include_in_schema=False)
def list_releases(
    project_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_drafts: bool = Query(
        False, description="Maintainers only; ignored otherwise"
    ),
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
) -> ReleaseList:
    project = ProjectReleaseService.get_project_or_404(db, project_id)

    # Silently downgrading the flag rather than 403-ing keeps the public
    # listing usable for clients that always send it.
    can_see_drafts = include_drafts and ProjectReleaseService.is_maintainer(
        db, project, current_user
    )

    items, total = ProjectReleaseService.list_releases(
        db,
        project_id=project_id,
        limit=limit,
        offset=offset,
        include_drafts=can_see_drafts,
    )
    return ReleaseList(
        items=[ReleaseResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=ReleaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a release",
    description=(
        "Defaults to `draft`. Pass `status: published` to publish immediately, "
        "which also announces it to followers."
    ),
    responses={
        403: {"description": "Not a project maintainer"},
        409: {"description": "That version already exists on this project"},
    },
)
@router.post(
    "/",
    response_model=ReleaseResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_release(
    project_id: uuid.UUID,
    payload: ReleaseCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> ReleaseResponse:
    release = ProjectReleaseService.create_release(
        db, project_id=project_id, payload=payload, actor=current_user
    )
    return ReleaseResponse.model_validate(release)


@router.get(
    "/latest",
    response_model=ReleaseResponse,
    summary="Get the newest published release",
    responses={404: {"description": "No published releases yet"}},
)
def get_latest_release(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
) -> ReleaseResponse:
    ProjectReleaseService.get_project_or_404(db, project_id)
    return ReleaseResponse.model_validate(
        ProjectReleaseService.get_latest(db, project_id)
    )


@router.get(
    "/{release_id}",
    response_model=ReleaseResponse,
    summary="Get one release",
    description="A draft is a 404 for anyone who is not a maintainer.",
)
def get_release(
    project_id: uuid.UUID,
    release_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
) -> ReleaseResponse:
    project = ProjectReleaseService.get_project_or_404(db, project_id)
    is_maintainer = ProjectReleaseService.is_maintainer(db, project, current_user)

    release = ProjectReleaseService.get_release_or_404(
        db, project_id, release_id, viewer_is_maintainer=is_maintainer
    )
    return ReleaseResponse.model_validate(release)


@router.patch(
    "/{release_id}",
    response_model=ReleaseResponse,
    summary="Edit a release",
    responses={409: {"description": "That version already exists on this project"}},
)
def update_release(
    project_id: uuid.UUID,
    release_id: uuid.UUID,
    payload: ReleaseUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> ReleaseResponse:
    release = ProjectReleaseService.update_release(
        db,
        project_id=project_id,
        release_id=release_id,
        payload=payload,
        actor=current_user,
    )
    return ReleaseResponse.model_validate(release)


@router.post(
    "/{release_id}/publish",
    response_model=ReleaseResponse,
    summary="Publish a release",
    description=(
        "Sets `published_at` and announces the release to followers. "
        "Idempotent — re-publishing does not move the date or announce twice."
    ),
)
def publish_release(
    project_id: uuid.UUID,
    release_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> ReleaseResponse:
    release = ProjectReleaseService.publish(
        db, project_id=project_id, release_id=release_id, actor=current_user
    )
    return ReleaseResponse.model_validate(release)


@router.post(
    "/{release_id}/pin",
    response_model=ReleaseResponse,
    summary="Pin a release to the top of the changelog",
    description="Un-pins whichever release was pinned before. Published releases only.",
    responses={400: {"description": "Release is still a draft"}},
)
def pin_release(
    project_id: uuid.UUID,
    release_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> ReleaseResponse:
    release = ProjectReleaseService.pin(
        db, project_id=project_id, release_id=release_id, actor=current_user
    )
    return ReleaseResponse.model_validate(release)


@router.delete(
    "/{release_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a release",
)
def delete_release(
    project_id: uuid.UUID,
    release_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    ProjectReleaseService.delete_release(
        db, project_id=project_id, release_id=release_id, actor=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
