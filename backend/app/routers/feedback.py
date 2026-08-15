from __future__ import annotations

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.models.feedback import UserFeedback, FeedbackCategory, FeedbackStatus
from app.models.user import User, UserRole
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackStatusUpdate

router = APIRouter()


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit user feedback or feature request",
)
def submit_feedback(
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    valid_categories = [c.value for c in FeedbackCategory]
    if payload.category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}",
        )

    feedback = UserFeedback(
        user_id=current_user.id,
        category=payload.category,
        title=payload.title,
        description=payload.description,
        status=FeedbackStatus.OPEN.value,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.get(
    "/me",
    response_model=List[FeedbackResponse],
    summary="Get user's submitted feedbacks and status tracking",
)
def get_my_feedbacks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    stmt = (
        select(UserFeedback)
        .where(UserFeedback.user_id == current_user.id)
        .order_by(UserFeedback.created_at.desc())
    )
    return db.scalars(stmt).all()


@router.get(
    "/admin",
    response_model=List[FeedbackResponse],
    summary="Admin list feedback submissions",
)
def admin_list_feedbacks(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    stmt = select(UserFeedback)
    if category:
        stmt = stmt.where(UserFeedback.category == category)
    if status:
        stmt = stmt.where(UserFeedback.status == status)

    stmt = stmt.order_by(UserFeedback.created_at.desc())
    return db.scalars(stmt).all()


@router.patch(
    "/admin/{feedback_id}",
    response_model=FeedbackResponse,
    summary="Admin update feedback status & response",
)
def admin_update_feedback(
    feedback_id: uuid.UUID,
    payload: FeedbackStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    feedback = db.get(UserFeedback, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    feedback.status = payload.status
    if payload.admin_response is not None:
        feedback.admin_response = payload.admin_response

    db.commit()
    db.refresh(feedback)
    return feedback
