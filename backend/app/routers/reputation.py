"""
Reputation System Router (#597)
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.reputation import (
    LeaderboardResponse,
    ReputationAwardRequest,
    ReputationLogResponse,
    ReputationSummaryResponse,
)
from app.services.reputation_service import ReputationService

router = APIRouter(prefix="/reputation", tags=["User Reputation System"])


@router.get(
    "/me",
    response_model=ReputationSummaryResponse,
    summary="Get current user reputation summary & activity log",
)
def get_my_reputation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the authenticated user's total reputation score, rank tier, and recent activity logs.
    """
    return ReputationService.get_user_reputation_summary(db, current_user.id)


@router.get(
    "/user/{user_id}",
    response_model=ReputationSummaryResponse,
    summary="Get specific user reputation summary & activity log",
)
def get_user_reputation(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Returns a specific user's total reputation score, rank tier, and recent activity logs.
    """
    return ReputationService.get_user_reputation_summary(db, user_id)


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    summary="Get community leaderboard ranked by reputation score",
)
def get_leaderboard(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Returns top community members ranked by their reputation score.
    """
    return ReputationService.get_leaderboard(db, skip=skip, limit=limit)


@router.post(
    "/award",
    response_model=ReputationLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Award reputation points to a user",
)
def award_reputation(
    payload: ReputationAwardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Awards reputation points for activities like merged pull requests, completed projects,
    contributions, discussions, profile completions, or mentor recognitions.
    """
    target_user_id = payload.user_id or current_user.id

    _, log_entry = ReputationService.award_reputation(
        db=db,
        user_id=target_user_id,
        action=payload.action,
        points_override=payload.points,
        description=payload.description,
    )

    return ReputationLogResponse.model_validate(log_entry)
