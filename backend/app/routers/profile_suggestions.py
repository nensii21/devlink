"""
API Router for AI-Powered Profile Improvement Suggestions (#619)
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.middleware.rate_limit import RECOMMENDATION_LIMIT, limiter
from app.models.user import User
from app.schemas.profile_suggestion import (
    DismissSuggestionResponse,
    ProfileSuggestionsResponse,
    RefreshSuggestionsResponse,
)
from app.services.profile_suggestion_service import ProfileSuggestionService

router = APIRouter(
    prefix="/profile-suggestions",
    tags=["Profile Suggestions"],
)


@router.get(
    "",
    response_model=ProfileSuggestionsResponse,
    summary="Get AI Profile Improvement Suggestions",
    description=(
        "Analyzes the authenticated developer's profile and returns tailored recommendations "
        "across 5 categories: missing_skills, weak_bio, portfolio_improvements, "
        "github_connection, and experience_gaps."
    ),
)
@router.get(
    "/",
    response_model=ProfileSuggestionsResponse,
    include_in_schema=False,
)
@limiter.limit(RECOMMENDATION_LIMIT)
def get_profile_suggestions(
    request: Request,
    include_dismissed: bool = Query(
        False,
        description="Set to true to include previously dismissed suggestions in the response.",
    ),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> ProfileSuggestionsResponse:
    """
    Get AI-powered profile improvement suggestions for current user.
    """
    return ProfileSuggestionService.get_profile_suggestions(
        db=db,
        user=current_user,
        include_dismissed=include_dismissed,
    )


@router.post(
    "/{suggestion_id}/dismiss",
    response_model=DismissSuggestionResponse,
    summary="Dismiss a profile suggestion",
    description="Dismisses a specific profile improvement suggestion so it no longer appears in active suggestions.",
)
def dismiss_suggestion(
    suggestion_id: str,
    category: Optional[str] = Query(
        "general", description="Optional category of suggestion"
    ),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> DismissSuggestionResponse:
    """
    Dismiss a specific suggestion by ID.
    """
    return ProfileSuggestionService.dismiss_suggestion(
        db=db,
        user_id=current_user.id,
        suggestion_id=suggestion_id,
        category=category or "general",
    )


@router.post(
    "/dismiss-all",
    summary="Dismiss all active profile suggestions",
    description="Dismisses all currently active suggestions for the authenticated developer.",
)
def dismiss_all_suggestions(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Dismiss all active suggestions for current user.
    """
    return ProfileSuggestionService.dismiss_all_suggestions(
        db=db,
        user=current_user,
    )


@router.post(
    "/refresh",
    response_model=RefreshSuggestionsResponse,
    summary="Refresh profile recommendations",
    description=(
        "Re-evaluates the developer's profile to generate fresh recommendations. "
        "Optionally resets previously dismissed suggestions."
    ),
)
@limiter.limit(RECOMMENDATION_LIMIT)
def refresh_suggestions(
    request: Request,
    reset_dismissed: bool = Query(
        False,
        description="If set to True, clears previously dismissed suggestions to allow re-evaluation.",
    ),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> RefreshSuggestionsResponse:
    """
    Refresh recommendations and optionally reset dismissals.
    """
    return ProfileSuggestionService.refresh_suggestions(
        db=db,
        user=current_user,
        reset_dismissed=reset_dismissed,
    )
