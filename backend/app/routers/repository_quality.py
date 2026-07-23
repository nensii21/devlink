"""
API router for the AI Repository Quality Analyzer.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas.repository_quality import (
    RepositoryQualityRequest,
    RepositoryQualityResponse,
)
from app.services.repository_quality_service import (
    RepositoryQualityService,
    _parse_github_url,
)

router = APIRouter(
    prefix="/repository-quality",
    tags=["Repository Quality"],
)


@router.post(
    "/analyze",
    response_model=RepositoryQualityResponse,
    summary="Analyze a GitHub repository's quality",
)
@limiter.limit("10/minute")
def analyze_repository(
    request: Request,
    body: RepositoryQualityRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> RepositoryQualityResponse:
    """
    Analyze a GitHub repository and return an overall quality score
    with individual metric breakdown and improvement suggestions.

    **Metrics analyzed:**

    | Metric          | Weight | Description |
    | --------------- | ------ | ----------- |
    | README          | 0.20   | Quality and completeness of README |
    | Documentation   | 0.15   | Presence of docs/, guides, changelog |
    | License         | 0.10   | License file presence |
    | Test Coverage   | 0.20   | Test directories, test files, coverage config |
    | CI/CD           | 0.15   | GitHub Actions, CI config files |
    | Recent Activity | 0.10   | Commit recency and frequency |
    | Open Issues     | 0.10   | Issue backlog ratio |

    Results are cached for 30 minutes.
    """
    try:
        _parse_github_url(body.repository_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    try:
        return RepositoryQualityService.analyze_repository(body.repository_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze repository: {e!s}",
        )
