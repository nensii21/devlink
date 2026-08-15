from __future__ import annotations

"""
API Router for pinned profile projects (#1042).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies import (
    get_current_active_user,
    get_database,
    get_optional_current_user,
)
from app.models.pinned_project import MAX_PINNED_PROJECTS
from app.models.user import User
from app.schemas.pinned_project import (
    PinnedProjectCreate,
    PinnedProjectList,
    PinnedProjectReorder,
    PinnedProjectResponse,
)
from app.services.pinned_project_service import PinnedProjectService

router = APIRouter(
    prefix="/users",
    tags=["Pinned Projects"],
)


def _as_list(pins) -> PinnedProjectList:
    return PinnedProjectList(
        items=[PinnedProjectResponse.model_validate(pin) for pin in pins],
        total=len(pins),
        max_pins=MAX_PINNED_PROJECTS,
    )


@router.get(
    "/me/pinned-projects",
    response_model=PinnedProjectList,
    summary="List your pinned projects",
)
def list_my_pinned_projects(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> PinnedProjectList:
    return _as_list(PinnedProjectService.list_pins(db, current_user.id))


@router.post(
    "/me/pinned-projects",
    response_model=PinnedProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Pin a project to your profile",
    description=(
        f"Appends the project after any existing pins, up to {MAX_PINNED_PROJECTS}. "
        "You may only pin a public, non-archived project you own or are a member of."
    ),
    responses={
        400: {
            "description": "Pin limit reached, or the project is private or archived"
        },
        403: {"description": "Not your project"},
        404: {"description": "Project not found"},
        409: {"description": "Already pinned"},
    },
)
def pin_project(
    payload: PinnedProjectCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> PinnedProjectResponse:
    pin = PinnedProjectService.pin(db, user=current_user, project_id=payload.project_id)
    return PinnedProjectResponse.model_validate(pin)


@router.put(
    "/me/pinned-projects",
    response_model=PinnedProjectList,
    summary="Replace the whole pinned set",
    description=(
        "Sets the complete list of pins, in display order — what a drag-and-drop "
        "UI wants. The batch is validated in full before anything is written, so "
        "one ineligible project rejects the whole request rather than leaving a "
        "half-applied order."
    ),
    responses={
        400: {"description": "Too many pins, a duplicate, or an ineligible project"}
    },
)
def replace_pinned_projects(
    payload: PinnedProjectReorder,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> PinnedProjectList:
    pins = PinnedProjectService.replace(
        db, user=current_user, project_ids=payload.project_ids
    )
    return _as_list(pins)


@router.delete(
    "/me/pinned-projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unpin a project",
    description="Remaining pins are renumbered so positions stay contiguous.",
)
def unpin_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    PinnedProjectService.unpin(db, user=current_user, project_id=project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{username}/pinned-projects",
    response_model=PinnedProjectList,
    summary="List a builder's pinned projects",
    description="Public, ordered by position. Private profiles are visible to their owner only.",
    responses={
        403: {"description": "Profile is private"},
        404: {"description": "User not found"},
    },
)
def list_pinned_projects(
    username: str,
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
) -> PinnedProjectList:
    subject = PinnedProjectService.get_user_or_404(db, username)

    if subject.is_private and (current_user is None or current_user.id != subject.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this private profile.",
        )

    return _as_list(PinnedProjectService.list_pins(db, subject.id))
