from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.middleware.rate_limit import limiter
from app.models.project import Project
from app.models.user import User
from app.schemas.contributor_match import (
    ContributorMatchRequest,
    ContributorMatchResponse,
    MatchedContributor,
)
from app.services.contributor_matching_service import ContributorMatchingService

router = APIRouter(
    tags=["Contributor Matching"],
)

MATCHING_RATE_LIMIT = "10/minute"


@router.post(
    "/match",
    response_model=ContributorMatchResponse,
)
@limiter.limit(MATCHING_RATE_LIMIT)
def match_contributors(
    request: Request,
    body: ContributorMatchRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """
    Find matching contributors for a project.

    Uses AI to analyze project requirements and candidate profiles,
    returning a ranked list with match scores and explanations.
    """
    # Verify project exists
    project = db.get(Project, body.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Run AI matching
    matches = ContributorMatchingService.match_contributors(
        db=db,
        project_id=body.project_id,
        limit=min(body.limit, 10),
    )

    # Build response with user details
    matched_contributors = []
    for match in matches:
        user = db.get(User, match.user_id)
        if not user:
            continue

        matched_contributors.append(
            MatchedContributor(
                user_id=user.id,
                username=user.username,
                full_name=f"{user.first_name} {user.last_name}",
                avatar=user.profile_image,
                headline=user.headline,
                match_score=match.match_score,
                match_reason=match.match_reason,
                matching_skills=match.matching_skills,
                availability=user.open_to_work,
            )
        )

    return ContributorMatchResponse(
        project_id=project.id,
        project_title=project.title,
        matches=matched_contributors,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
