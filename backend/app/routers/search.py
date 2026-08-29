from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.cache import cached

from app.dependencies import (
    get_database,
    get_current_user,
    get_optional_current_user,
)
from app.schemas.search import (
    SearchAutocompleteResponse,
    SearchRequest,
    SearchResponse,
)
from app.models.centralized_analytics import CentralizedAnalyticsEvent
from app.schemas.search_index import (
    SearchIndexedResponse,
    SearchAnalyticsMetric,
    SearchBenchmarkReport,
)
from app.services.search_service import SearchService
from app.services.search_index_service import SearchIndexService
from app.services.search_analytics_service import SearchAnalyticsService
from app.models.user import User, UserRole
import time
import uuid
from pydantic import BaseModel

router = APIRouter()


@router.post(
    "/semantic",
    response_model=SearchResponse,
    summary="Semantic vector search with keyword fallback",
)
async def semantic_search(
    payload: SearchRequest,
    db: Session = Depends(get_database),
):
    """
    Execute semantic vector search across projects, profiles, discussions, and skills,
    with an automatic fallback mechanism to standard keyword search.
    """
    return await SearchService.search(db=db, request=payload)


@router.get("", summary="Full multi-category search")
@cached(ttl=60, key_prefix="search")
def full_search(
    q: str = Query("", max_length=200),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    skills: Optional[str] = Query(
        None, description="Comma-separated list of skill names to filter developers by"
    ),
    location: Optional[str] = Query(
        None, max_length=150, description="Filter developers by location"
    ),
    experience: Optional[str] = Query(
        None,
        max_length=50,
        description="Filter developers by experience level (e.g. beginner, intermediate, advanced, expert)",
    ),
    availability: Optional[bool] = Query(
        None, description="Filter developers by open-to-work availability"
    ),
    organization: Optional[str] = Query(
        None,
        max_length=150,
        description="Filter developers by company/organization name",
    ),
    remote: Optional[bool] = Query(
        None, description="Filter developers open to remote work"
    ),
    sort: Optional[str] = Query(
        None,
        description="Sort order for developers: relevance, name, experience, recent",
    ),
    db: Session = Depends(get_database),
    user: Optional[User] = Depends(get_optional_current_user),
):
    """Full-text paginated search across Users, Projects, Organizations, Skills, and Tags.

    Supports advanced filters (skills, location, experience, availability,
    organization, remote) and a sort order, which apply to the developers
    (users) results.
    """
    start_time = time.time()

    skills_list = (
        [s.strip() for s in skills.split(",") if s.strip()] if skills else None
    )

    results = SearchService.search(
        db=db,
        q=q,
        category=category,
        page=page,
        limit=limit,
        skills_filter=skills_list,
        location=location,
        experience=experience,
        availability=availability,
        organization=organization,
        remote=remote,
        sort=sort,
    )

    latency_ms = (time.time() - start_time) * 1000

    # Calculate total results returned in this page
    total_results = 0
    if isinstance(results, dict):
        if category:
            for v in results.values():
                if isinstance(v, list):
                    total_results += len(v)
        else:
            for k, v in results.items():
                if isinstance(v, list):
                    total_results += len(v)

    if q.strip():
        applied_filters = {
            k: v
            for k, v in {
                "category": category,
                "skills": skills_list,
                "location": location,
                "experience": experience,
                "availability": availability,
                "organization": organization,
                "remote": remote,
                "sort": sort,
            }.items()
            if v not in (None, "", [])
        }
        SearchAnalyticsService.log_search(
            db=db,
            query=q,
            results_count=total_results,
            latency_ms=latency_ms,
            user_id=user.id if user else None,
            filters=applied_filters or None,
        )

        # Log search appearances for returned users/developers
        if results.get("users"):
            for u in results["users"]:
                db.add(
                    CentralizedAnalyticsEvent(
                        event_type="profile_search_appearance",
                        user_id=user.id if user else None,
                        properties={"target_user_id": str(u.id), "query": q},
                    )
                )
            db.commit()

    return results


@router.get(
    "/autocomplete",
    response_model=SearchAutocompleteResponse,
    summary="Global search autocomplete",
)
def autocomplete(
    q: str = Query("", min_length=0, max_length=100),
    db: Session = Depends(get_database),
):
    """Lightweight autocomplete endpoint returning top matches per category."""
    return SearchService.autocomplete(db=db, q=q)


@router.get(
    "/suggestions",
    response_model=List[str],
    summary="Global search suggestions",
)
def suggestions(
    q: str = Query("", min_length=0, max_length=100),
    limit: int = Query(8, ge=1, le=50),
    db: Session = Depends(get_database),
):
    """Returns a flat list of matching query suggestion strings."""
    return SearchService.suggestions(db=db, q=q, limit=limit)


# ---------------------------------------------------------------------
# Optimized Inverted Search Index Endpoints (#647)
# ---------------------------------------------------------------------


@router.get(
    "/indexed",
    response_model=SearchIndexedResponse,
    summary="Optimized global index search",
)
def search_indexed(
    q: str = Query("", max_length=200, description="Search query string"),
    category: Optional[str] = Query(
        None,
        description="Resource category: developers, projects, organizations, discussions, skills, technologies",
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database),
):
    """Executes high-performance tokenized search across inverted index with weighted relevance ranking."""
    return SearchIndexService.execute_search(
        db=db,
        query=q,
        category=category,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/index/reindex",
    summary="Reindex global search resources",
)
def reindex_search_resources(
    db: Session = Depends(get_database),
):
    """Rebuilds the inverted search index across developers, projects, organizations, discussions, skills, and technologies."""
    return SearchIndexService.reindex_all(db)


class TrackClickRequest(BaseModel):
    query: str
    clicked_entity_type: str
    clicked_entity_id: uuid.UUID


@router.post(
    "/track-click",
    summary="Track a click from search results",
)
def track_click(
    request: TrackClickRequest,
    db: Session = Depends(get_database),
    user: Optional[User] = Depends(get_optional_current_user),
):
    """Track which entity a user clicked from their search results."""
    from sqlalchemy import select
    from app.models.search_analytics import SearchQueryLog

    stmt = select(SearchQueryLog).where(SearchQueryLog.query == request.query)
    if user:
        stmt = stmt.where(SearchQueryLog.user_id == user.id)

    stmt = stmt.order_by(SearchQueryLog.created_at.desc()).limit(1)

    log = db.scalar(stmt)
    if not log:
        return {"status": "ignored"}

    SearchAnalyticsService.log_click(
        db=db,
        search_query_id=log.id,
        clicked_entity_type=request.clicked_entity_type,
        clicked_entity_id=request.clicked_entity_id,
        user_id=user.id if user else None,
    )
    return {"status": "success"}


@router.get(
    "/analytics",
    response_model=SearchAnalyticsMetric,
    summary="Get search analytics & latency metrics",
)
def get_search_analytics():
    """Returns search query latency metrics, top search terms, zero-result counts, and category distribution."""
    return SearchIndexService.get_analytics()


@router.get(
    "/benchmark",
    response_model=SearchBenchmarkReport,
    summary="Run search index performance benchmark",
)
def run_search_benchmark(
    q: str = Query("dev", description="Query to benchmark"),
    iterations: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_database),
):
    """Benchmarks query execution latency comparing Inverted Index search vs Naive SQL ILIKE search."""
    return SearchIndexService.run_benchmark(db=db, query=q, iterations=iterations)


@router.get(
    "/analytics/dashboard",
    summary="Get search analytics dashboard metrics",
)
def get_analytics_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if getattr(current_user, "role", None) != UserRole.ADMIN and not getattr(
        current_user, "is_admin", False
    ):
        raise HTTPException(status_code=403, detail="Admin only")

    return SearchAnalyticsService.get_dashboard_metrics(db, days=days)
