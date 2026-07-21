from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.middleware.rate_limit import limiter, SEARCH_LIMIT
from app.schemas.search import SearchResultGroups, SearchResponse
from app.services.search_service import SEARCHABLE_TYPES, SearchService

router = APIRouter(tags=["Search"])


@router.get(
    "/",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(SEARCH_LIMIT)
def global_search(
    request: Request,
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    types: list[str] | None = Query(
        default=None,
        description="Optional entity-type filter. One or more of: "
        "developers, projects, organizations, skills, flares",
    ),
    limit: int = Query(default=20, ge=1, le=50, description="Max results per type"),
    db: Session = Depends(get_database),
) -> SearchResponse:
    """
    Unified global search across developers, projects, organizations,
    skills and flares.

    Returns grouped results — each group is capped at ``limit`` items.
    Inactive / private / archived / closed entities are never returned.
    """
    query = q.strip()
    if not query:
        # FastAPI's ``min_length=1`` already guards this, but an
        # all-whitespace query slips through — normalise here.
        return SearchResponse(
            query=query,
            types=types or [],
            total=0,
            results=SearchResultGroups(),
        )

    raw = SearchService.search(db, query, types, limit)

    groups = SearchResultGroups(
        users=raw.get("users", []),
        projects=raw.get("projects", []),
        organizations=raw.get("organizations", []),
        skills=raw.get("skills", []),
        flares=raw.get("flares", []),
    )
    total = (
        len(groups.users)
        + len(groups.projects)
        + len(groups.organizations)
        + len(groups.skills)
        + len(groups.flares)
    )

    return SearchResponse(
        query=query,
        types=list(SEARCHABLE_TYPES.keys()) if types is None else types,
        total=total,
        results=groups,
    )
