from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.recommendation import (
    ProjectRecommendation,
    RecommendationList,
    RecommendationProject,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.get(
    "/projects",
    response_model=RecommendationList,
    status_code=status.HTTP_200_OK,
    summary="Get Project Recommendations",
    description=(
        "Returns a ranked list of projects recommended for the current user."
        " Recommendations are scored based on shared skills, previous"
        " contributions, bookmarked projects, and followed organisations."
    ),
)
def recommend_projects(
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get personalised project recommendations for the authenticated user.

    **Scoring factors (weights):**
    - Shared skills between user and project (40%)
    - Previous contributions to the project (25%)
    - Bookmarked projects by the user (20%)
    - Organisational affiliation (15%)
    """
    projects, total = RecommendationService.get_recommended_projects(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    recommendations = [
        ProjectRecommendation(
            project=RecommendationProject.model_validate(p["project"]),
            score=p["score"],
            skill_match_count=p["skill_match_count"],
            total_skills=p["total_skills"],
            is_previous_contribution=p["is_previous_contribution"],
            is_bookmarked=p["is_bookmarked"],
            is_org_related=p["is_org_related"],
        )
        for p in projects
    ]

    return RecommendationList(
        recommendations=recommendations,
        total=total,
    )
