"""
API router for the AI-Powered Builder Recommendation System.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.middleware.rate_limit import RECOMMENDATION_LIMIT, limiter
from app.models.user import User
from app.schemas.recommendation import (
    ProjectRecommendationResponse,
    RecommendationResponse,
    RecommendedBuilder,
    RecommendedProject,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.get(
    "/builders",
    response_model=RecommendationResponse,
    summary="Get recommended builders (collaborators)",
)
@limiter.limit(RECOMMENDATION_LIMIT)
def get_recommended_builders(
    request: Request,
    project_id: uuid.UUID | None = Query(
        None,
        description=(
            "Optional project ID. When supplied, builders are ranked "
            "against that project's required skills, tech stack and "
            "minimum experience. When omitted, builders are ranked "
            "against the requester's own profile (find-collaborators mode)."
        ),
    ),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> RecommendationResponse:
    """
    Returns a ranked list of recommended builders (potential collaborators).

    **Scoring factors** (each in ``[0, 1]``):

    | Factor          | Weight | Source |
    | --------------- | ------ | ------ |
    | Skills          | 0.30   | Jaccard overlap weighted by skill level |
    | Technologies   | 0.20   | Builder skills vs. ``project.tech_stack`` |
    | Experience      | 0.15   | Builder years vs. ``project_skill.minimum_experience`` |
    | Interests       | 0.10   | Bio/headline keyword overlap with project description |
    | Availability    | 0.10   | ``user.open_to_work`` |
    | Contributions   | 0.10   | Owned projects + accepted applications (log scale) |
    | Network         | 0.05   | Mutual-follower social boost |

    Results are cached for 10 minutes.
    """
    if project_id is not None:
        # Verify the project exists; 404 early otherwise.
        from app.services.project_service import ProjectService

        if ProjectService.get_project(db, project_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

    results: list[RecommendedBuilder] = RecommendationService.recommend_builders(
        db=db,
        requester=current_user,
        project_id=project_id,
        limit=limit,
    )

    context_label = f"project:{project_id}" if project_id else f"user:{current_user.id}"
    return RecommendationResponse(
        query_context=context_label,
        total=len(results),
        limit=limit,
        results=results,
    )


@router.get(
    "/projects",
    response_model=ProjectRecommendationResponse,
    summary="Get recommended projects",
)
@limiter.limit(RECOMMENDATION_LIMIT)
def get_recommended_projects(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> ProjectRecommendationResponse:
    """
    Returns a ranked list of recommended projects for the authenticated developer.

    **Scoring factors**:
    - **Skills**: Project requirements vs Developer's skills
    - **Technologies**: Project tech stack vs Developer's skills
    - **Experience**: Project minimum experience vs Developer's experience
    - **Interests**: Project title/description vs Developer's bio/headline
    """
    results: list[RecommendedProject] = RecommendationService.recommend_projects(
        db=db,
        requester=current_user,
        limit=limit,
    )

    return ProjectRecommendationResponse(
        query_context=f"projects_for_user:{current_user.id}",
        total=len(results),
        limit=limit,
        results=results,
    )
