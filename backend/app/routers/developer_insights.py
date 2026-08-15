from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.developer_insights import DeveloperInsightsResponse
from app.services.developer_insights_service import DeveloperInsightsService

router = APIRouter(prefix="/developer-insights", tags=["Developer Insights"])


@router.get(
    "",
    response_model=DeveloperInsightsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Developer Insights Dashboard Data",
    description="Returns personalized activity metrics, engagement trends, contribution streak, and AI match rate for current user.",
)
@router.get(
    "/",
    response_model=DeveloperInsightsResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_developer_insights(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    range: str = Query(
        default="30d",
        pattern="^(7d|30d|90d|1y|all)$",
        description="Date range filter: 7d, 30d, 90d, 1y, or all",
    ),
) -> DeveloperInsightsResponse:
    return DeveloperInsightsService.get_user_insights(
        db=db, user=current_user, date_range=range
    )
