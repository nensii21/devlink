from __future__ import annotations

"""
API Router for peer testimonials (#1044).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.dependencies import (
    get_current_active_user,
    get_database,
    get_optional_current_user,
)
from app.models.testimonial import TestimonialStatus
from app.models.user import User
from app.schemas.testimonial import (
    TestimonialCreate,
    TestimonialList,
    TestimonialResponse,
    TestimonialSummary,
    TestimonialUpdate,
)
from app.services.testimonial_service import TestimonialService

router = APIRouter(tags=["Testimonials"])


def _as_list(items, total: int, limit: int, offset: int) -> TestimonialList:
    return TestimonialList(
        items=[TestimonialResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


@router.post(
    "/testimonials",
    response_model=TestimonialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Write a testimonial about someone",
    description=(
        "Lands in `pending` and is visible only to you and the subject until "
        "they approve it. One testimonial per pair — edit yours rather than "
        "writing a second."
    ),
    responses={
        400: {"description": "You cannot write about yourself"},
        403: {"description": "One of you has blocked the other"},
        409: {"description": "You have already written one for this user"},
    },
)
def create_testimonial(
    payload: TestimonialCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TestimonialResponse:
    testimonial = TestimonialService.create(db, author=current_user, payload=payload)
    return TestimonialResponse.model_validate(testimonial)


@router.patch(
    "/testimonials/{testimonial_id}",
    response_model=TestimonialResponse,
    summary="Edit your testimonial",
    description=(
        "Editing the text of an approved testimonial returns it to `pending` "
        "and un-features it — otherwise approval would be a rubber stamp on "
        "text that can be swapped out afterwards."
    ),
    responses={403: {"description": "Not your testimonial, or it has been hidden"}},
)
def update_testimonial(
    testimonial_id: uuid.UUID,
    payload: TestimonialUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TestimonialResponse:
    testimonial = TestimonialService.update(
        db, testimonial_id=testimonial_id, author=current_user, payload=payload
    )
    return TestimonialResponse.model_validate(testimonial)


@router.delete(
    "/testimonials/{testimonial_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete your testimonial",
    description=(
        "Only the author may delete. The subject can hide a testimonial but "
        "not erase it — someone else's opinion is not theirs to destroy."
    ),
)
def delete_testimonial(
    testimonial_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    TestimonialService.delete(db, testimonial_id=testimonial_id, user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Moderation (subject only)
# ---------------------------------------------------------------------------


@router.post(
    "/testimonials/{testimonial_id}/approve",
    response_model=TestimonialResponse,
    summary="Approve a testimonial written about you",
    responses={403: {"description": "You are not the subject"}},
)
def approve_testimonial(
    testimonial_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TestimonialResponse:
    return TestimonialResponse.model_validate(
        TestimonialService.approve(
            db, testimonial_id=testimonial_id, subject=current_user
        )
    )


@router.post(
    "/testimonials/{testimonial_id}/hide",
    response_model=TestimonialResponse,
    summary="Hide a testimonial written about you",
    description="Removes it from your profile and un-features it. The author can still see it.",
)
def hide_testimonial(
    testimonial_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TestimonialResponse:
    return TestimonialResponse.model_validate(
        TestimonialService.hide(db, testimonial_id=testimonial_id, subject=current_user)
    )


@router.post(
    "/testimonials/{testimonial_id}/feature",
    response_model=TestimonialResponse,
    summary="Feature (or un-feature) an approved testimonial",
    responses={400: {"description": "Not approved, or the featured limit is reached"}},
)
def feature_testimonial(
    testimonial_id: uuid.UUID,
    featured: bool = Query(True, description="Set false to un-feature"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TestimonialResponse:
    return TestimonialResponse.model_validate(
        TestimonialService.set_featured(
            db, testimonial_id=testimonial_id, subject=current_user, featured=featured
        )
    )


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


@router.get(
    "/testimonials/received",
    response_model=TestimonialList,
    summary="Testimonials written about you",
    description="Your moderation queue. Includes pending and hidden entries.",
)
def list_received(
    status_filter: TestimonialStatus | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TestimonialList:
    items, total = TestimonialService.list_for_subject(
        db,
        subject=current_user,
        viewer=current_user,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    return _as_list(items, total, limit, offset)


@router.get(
    "/testimonials/written",
    response_model=TestimonialList,
    summary="Testimonials you have written",
)
def list_written(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TestimonialList:
    items, total = TestimonialService.list_written_by(
        db, author=current_user, limit=limit, offset=offset
    )
    return _as_list(items, total, limit, offset)


@router.get(
    "/testimonials/{testimonial_id}",
    response_model=TestimonialResponse,
    summary="Get one testimonial",
    description="A pending or hidden testimonial is a 404 for anyone but its author and subject.",
)
def get_testimonial(
    testimonial_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
) -> TestimonialResponse:
    testimonial = TestimonialService.get_testimonial_or_404(db, testimonial_id)

    # 404 rather than 403: a 403 would confirm that an unapproved testimonial
    # about this person exists, which is exactly what moderation hides.
    if not TestimonialService.can_view(testimonial, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Testimonial not found"
        )

    return TestimonialResponse.model_validate(testimonial)


@router.get(
    "/users/{username}/testimonials",
    response_model=TestimonialList,
    summary="A builder's testimonials",
    description=(
        "Approved only for the public. The subject sees their whole inbox and "
        "may filter with `?status=`."
    ),
)
def list_for_user(
    username: str,
    status_filter: TestimonialStatus | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
) -> TestimonialList:
    subject = TestimonialService.get_user_or_404(db, username)
    items, total = TestimonialService.list_for_subject(
        db,
        subject=subject,
        viewer=current_user,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    return _as_list(items, total, limit, offset)


@router.get(
    "/users/{username}/testimonials/summary",
    response_model=TestimonialSummary,
    summary="Testimonial summary for a profile header",
    description="Approved counts grouped by relationship, plus the featured testimonials.",
)
def get_summary(
    username: str,
    db: Session = Depends(get_database),
) -> TestimonialSummary:
    subject = TestimonialService.get_user_or_404(db, username)
    return TestimonialService.summarise(db, subject)
