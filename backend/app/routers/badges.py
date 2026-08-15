import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.models.user import User
from app.schemas.badge import BadgeResponse, UserBadgeResponse, BadgeEvaluationResponse
from app.services.badge_service import BadgeService

router = APIRouter(
    prefix="/badges",
    tags=["Badges"],
)


@router.get(
    "/",
    response_model=List[BadgeResponse],
    summary="Get all available achievement badges",
)
def get_all_badges(
    db: Session = Depends(get_database),
):
    """Retrieve all standard achievement badges defined in the platform."""
    return BadgeService.get_all_badges(db)


@router.get(
    "/me",
    response_model=List[UserBadgeResponse],
    summary="Get current user's earned badges",
)
def get_my_badges(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all achievement badges earned by the currently logged-in user."""
    return BadgeService.get_user_badges(db, current_user.id)


@router.get(
    "/user/{user_id}",
    response_model=List[UserBadgeResponse],
    summary="Get earned badges for a specific user",
)
def get_user_badges(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    """Retrieve all achievement badges earned by a user by UUID."""
    return BadgeService.get_user_badges(db, user_id)


@router.post(
    "/evaluate",
    response_model=BadgeEvaluationResponse,
    summary="Evaluate and award achievement badges",
)
def evaluate_badges(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """Evaluate user milestones and automatically award any newly achieved badges."""
    return BadgeService.evaluate_user_badges(db, current_user.id)
