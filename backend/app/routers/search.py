from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.middleware.rate_limit import limiter, SEARCH_LIMIT
from app.schemas.search import (
    SearchAutocompleteResponse,
    SearchResultGroups,
    SearchResponse,
    SearchSuggestionProject,
    SearchSuggestionSkill,
    SearchSuggestionUser,
)
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


# ---------------------------------------------------------------------------
# Autocomplete (lightweight typeahead for the Topbar search)
# ---------------------------------------------------------------------------


@router.get(
    "/autocomplete",
    response_model=SearchAutocompleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Global search autocomplete",
)
@limiter.limit(SEARCH_LIMIT)
def autocomplete(
    request: Request,
    q: str = Query("", min_length=0, max_length=100, description="Search query"),
    db: Session = Depends(get_database),
) -> SearchAutocompleteResponse:
    """
    Lightweight autocomplete endpoint returning up to 3 suggestions per
    entity type (users, projects, skills).  Used by the Topbar typeahead.
    """
    if not q or not q.strip():
        return SearchAutocompleteResponse(users=[], projects=[], skills=[])

    query_str = f"%{q.strip()}%"

    from sqlalchemy import or_

    from app.models.project import Project
    from app.models.skill import Skill
    from app.models.user import User

    users = (
        db.query(User)
        .filter(
            or_(
                User.username.ilike(query_str),
                User.first_name.ilike(query_str),
                User.last_name.ilike(query_str),
                User.role.ilike(query_str),
            )
        )
        .limit(3)
        .all()
    )

    formatted_users = [
        SearchSuggestionUser(
            id=u.id,
            name=f"{u.first_name} {u.last_name}".strip(),
            username=u.username,
            role=u.role,
            profile_image=u.profile_image,
        )
        for u in users
    ]

    projects = (
        db.query(Project)
        .filter(
            or_(
                Project.title.ilike(query_str),
                Project.tagline.ilike(query_str),
                Project.description.ilike(query_str),
            )
        )
        .limit(3)
        .all()
    )

    formatted_projects = [
        SearchSuggestionProject(id=p.id, title=p.title, icon=p.logo_url or "🚀")
        for p in projects
    ]

    skills = db.query(Skill).filter(Skill.name.ilike(query_str)).limit(3).all()

    formatted_skills = [SearchSuggestionSkill(id=s.id, name=s.name) for s in skills]

    return SearchAutocompleteResponse(
        users=formatted_users,
        projects=formatted_projects,
        skills=formatted_skills,
    )
