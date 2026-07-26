from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas.profile_summary import (
    ProfileSummaryRequest,
    ProfileSummaryResponse,
)
from app.services.profile_summary_service import ProfileSummaryService
from app.services.user_service import UserService

router = APIRouter(
    tags=["Profile Summary"],
)

PROFILE_SUMMARY_LIMIT = "5/minute"


@router.post(
    "/profile-summary",
    response_model=ProfileSummaryResponse,
)
@limiter.limit(PROFILE_SUMMARY_LIMIT)
def generate_profile_summary(
    request: Request,
    body: ProfileSummaryRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """
    Generate an AI-powered professional summary for a developer profile.

    Creates a concise summary based on the user's profile data,
    skills, and activity. Limited to 500 characters.
    """
    # Verify target user exists
    target_user = db.get(User, body.user_id)
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Get user stats for context
    stats = UserService.get_user_stats(db, body.user_id)
    stats_dict = {
        "projects": stats.projects,
        "followers": stats.followers,
        "accepted": stats.accepted,
    }

    # Generate summary
    summary = ProfileSummaryService.generate_summary(
        db=db,
        user=target_user,
        stats=stats_dict,
    )

    return ProfileSummaryResponse(
        summary=summary,
        user_id=target_user.id,
        user_name=f"{target_user.first_name} {target_user.last_name}",
    )
