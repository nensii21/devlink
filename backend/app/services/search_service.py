from __future__ import annotations

import logging
from collections import Counter
from typing import List, Optional, Sequence

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.project import Project
from app.models.skill import Skill
from app.models.user import User
from app.schemas.search import (
    SearchAutocompleteResponse,
    SearchCounts,
    SearchResultOrganization,
    SearchResultProject,
    SearchResultSkill,
    SearchResultTag,
    SearchResultUser,
    SearchSuggestionOrganization,
    SearchSuggestionProject,
    SearchSuggestionSkill,
    SearchSuggestionTag,
    SearchSuggestionUser,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _normalize_query(q: str) -> str:
    """Trim and lower-case the search query for matching."""
    return (q or "").strip()


def _ilike_pattern(q: str) -> str:
    """Build a SQLAlchemy ILIKE pattern with wildcards on both ends."""
    # Escape SQL LIKE wildcards inside the user query so a literal '%' or '_'
    # in the search string does not act as a wildcard.
    escaped = (
        _normalize_query(q)
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"


# ---------------------------------------------------------------------
# Per-category search helpers
# ---------------------------------------------------------------------


def search_users(db: Session, q: str, limit: int = 20) -> List[User]:
    """Search active users by name / username / role / headline."""
    if not _normalize_query(q):
        return []
    pattern = _ilike_pattern(q)
    return (
        db.query(User)
        .filter(
            User.is_active.is_(True),
            or_(
                User.username.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                User.role.ilike(pattern),
                User.headline.ilike(pattern),
            ),
        )
        .order_by(User.username.asc())
        .limit(limit)
        .all()
    )


def search_projects(db: Session, q: str, limit: int = 20) -> List[Project]:
    """Search published projects by title / tagline / description / tech stack."""
    if not _normalize_query(q):
        return []
    pattern = _ilike_pattern(q)
    return (
        db.query(Project)
        .filter(
            Project.is_published.is_(True),
            Project.is_archived.is_(False),
            or_(
                Project.title.ilike(pattern),
                Project.tagline.ilike(pattern),
                Project.description.ilike(pattern),
                Project.tech_stack.ilike(pattern),
            ),
        )
        .order_by(Project.stars.desc(), Project.created_at.desc())
        .limit(limit)
        .all()
    )


def search_organizations(db: Session, q: str, limit: int = 20) -> List[Organization]:
    """Search active organizations by name / slug / description / location."""
    if not _normalize_query(q):
        return []
    pattern = _ilike_pattern(q)
    return (
        db.query(Organization)
        .filter(
            Organization.active.is_(True),
            or_(
                Organization.name.ilike(pattern),
                Organization.slug.ilike(pattern),
                Organization.description.ilike(pattern),
                Organization.location.ilike(pattern),
            ),
        )
        .order_by(Organization.members_count.desc(), Organization.name.asc())
        .limit(limit)
        .all()
    )


def search_skills(db: Session, q: str, limit: int = 20) -> List[Skill]:
    """Search skills by name / normalized_name / category / description."""
    if not _normalize_query(q):
        return []
    pattern = _ilike_pattern(q)
    return (
        db.query(Skill)
        .filter(
            or_(
                Skill.name.ilike(pattern),
                Skill.normalized_name.ilike(pattern),
                Skill.category.ilike(pattern),
                Skill.description.ilike(pattern),
            )
        )
        .order_by(Skill.name.asc())
        .limit(limit)
        .all()
    )


def search_tags(db: Session, q: str, limit: int = 20) -> List[SearchResultTag]:
    """Aggregate project tags matching the query.

    Project.tags is a JSON array stored as a string list — we pull all
    published projects' tags in Python and filter/aggregate them. This keeps
    the implementation portable across SQLite (tests) and Postgres (prod)
    without needing JSONB-specific operators.
    """
    if not _normalize_query(q):
        return []
    needle = _normalize_query(q).lower()

    rows = (
        db.query(Project.tags)
        .filter(
            Project.is_published.is_(True),
            Project.is_archived.is_(False),
            Project.tags.isnot(None),
        )
        .all()
    )

    counter: Counter[str] = Counter()
    for (tags,) in rows:
        if not tags:
            continue
        if not isinstance(tags, list):
            # Defensive: skip malformed rows.
            continue
        for tag in tags:
            if not isinstance(tag, str):
                continue
            if needle in tag.lower():
                counter[tag.strip()] += 1

    return [
        SearchResultTag(name=name, project_count=count)
        for name, count in counter.most_common(limit)
    ]


# ---------------------------------------------------------------------
# Counts (for tab badges)
# ---------------------------------------------------------------------


def count_results(db: Session, q: str) -> SearchCounts:
    """Return per-category counts for the active query without fetching rows."""
    users = len(search_users(db, q, limit=10_000))
    projects = len(search_projects(db, q, limit=10_000))
    organizations = len(search_organizations(db, q, limit=10_000))
    skills = len(search_skills(db, q, limit=10_000))
    tags_count = len(search_tags(db, q, limit=10_000))
    return SearchCounts(
        developers=users,
        projects=projects,
        organizations=organizations,
        skills=skills,
        tags=tags_count,
        total=users + projects + organizations + skills + tags_count,
    )


# ---------------------------------------------------------------------
# Public service surface
# ---------------------------------------------------------------------


class SearchService:
    """Modular global search service.

    All public methods are pure functions of ``(db, query, ...opts)`` and
    return Pydantic schema instances ready to be serialized by the router.
    """

    # ---------------- autocomplete / suggestions ----------------

    @staticmethod
    def autocomplete(
        db: Session,
        q: str,
        per_category: int = 3,
    ) -> SearchAutocompleteResponse:
        """Lightweight autocomplete payload — small per-category lists.

        Always returns a ``SearchAutocompleteResponse`` so the router can
        directly validate / serialize it.
        """
        if not _normalize_query(q):
            return SearchAutocompleteResponse(
                users=[],
                projects=[],
                organizations=[],
                skills=[],
                tags=[],
            )

        users = search_users(db, q, limit=per_category)
        projects = search_projects(db, q, limit=per_category)
        organizations = search_organizations(db, q, limit=per_category)
        skills = search_skills(db, q, limit=per_category)
        tags = search_tags(db, q, limit=per_category)

        return SearchAutocompleteResponse(
            users=[
                SearchSuggestionUser(
                    id=u.id,
                    name=f"{u.first_name} {u.last_name}".strip(),
                    username=u.username,
                    role=u.role,
                    profile_image=u.profile_image,
                )
                for u in users
            ],
            projects=[
                SearchSuggestionProject(
                    id=p.id,
                    title=p.title,
                    icon=p.logo_url or "🚀",
                    tagline=p.tagline,
                )
                for p in projects
            ],
            organizations=[
                SearchSuggestionOrganization(
                    id=o.id,
                    name=o.name,
                    slug=o.slug,
                    logo_url=o.logo_url,
                    organization_type=(
                        o.organization_type.value if o.organization_type else None
                    ),
                    verified=o.verified,
                )
                for o in organizations
            ],
            skills=[
                SearchSuggestionSkill(id=s.id, name=s.name, category=s.category)
                for s in skills
            ],
            tags=[
                SearchSuggestionTag(name=t.name, project_count=t.project_count)
                for t in tags
            ],
        )

    @staticmethod
    def suggestions(db: Session, q: str, limit: int = 8) -> List[str]:
        """Flat list of suggestion strings (for keyboard-navigable dropdowns).

        Combines the top matches across all categories into a single list,
        deduplicated, preserving a stable order: users → projects → orgs →
        skills → tags.
        """
        if not _normalize_query(q):
            return []
        out: List[str] = []
        seen: set[str] = set()

        def _add(value: Optional[str]) -> None:
            if not value:
                return
            key = value.strip()
            if not key or key.lower() in seen:
                return
            seen.add(key.lower())
            out.append(key)

        per = max(1, limit // 5)
        for u in search_users(db, q, limit=per):
            _add(u.username)
        for p in search_projects(db, q, limit=per):
            _add(p.title)
        for o in search_organizations(db, q, limit=per):
            _add(o.name)
        for s in search_skills(db, q, limit=per):
            _add(s.name)
        for t in search_tags(db, q, limit=per):
            _add(t.name)
        return out[:limit]

    # ---------------- full search ----------------

    @staticmethod
    def search(
        db: Session,
        q: str,
        category: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """Full paginated search across categories.

        When ``category`` is provided, only that category's results are
        returned (paginated). Otherwise, the top ``limit`` results from
        *each* category are returned (no cross-category pagination).
        """
        page = max(1, int(page or 1))
        limit = max(1, min(int(limit or 20), 100))

        # For single-category search, apply offset pagination.
        if category:
            offset = (page - 1) * limit
            cat = category.lower().strip()
            users: Sequence[User] = []
            projects: Sequence[Project] = []
            organizations: Sequence[Organization] = []
            skills: Sequence[Skill] = []
            tags: Sequence[SearchResultTag] = []

            if cat == "developers":
                users = search_users(db, q, limit=limit + offset)[
                    offset : offset + limit
                ]
            elif cat == "projects":
                projects = search_projects(db, q, limit=limit + offset)[
                    offset : offset + limit
                ]
            elif cat == "organizations":
                organizations = search_organizations(db, q, limit=limit + offset)[
                    offset : offset + limit
                ]
            elif cat == "skills":
                skills = search_skills(db, q, limit=limit + offset)[
                    offset : offset + limit
                ]
            elif cat == "tags":
                tags = search_tags(db, q, limit=limit + offset)[offset : offset + limit]
            else:
                # Unknown category — return empty results but valid shape.
                logger.warning("Unknown search category: %s", cat)
        else:
            # All-categories mode: top ``limit`` from each category.
            users = search_users(db, q, limit=limit)
            projects = search_projects(db, q, limit=limit)
            organizations = search_organizations(db, q, limit=limit)
            skills = search_skills(db, q, limit=limit)
            tags = search_tags(db, q, limit=limit)

        counts = count_results(db, q)

        return {
            "query": _normalize_query(q),
            "category": category,
            "page": page,
            "limit": limit,
            "counts": counts,
            "users": [
                SearchResultUser(
                    id=u.id,
                    name=f"{u.first_name} {u.last_name}".strip(),
                    username=u.username,
                    role=u.role,
                    headline=u.headline,
                    profile_image=u.profile_image,
                    location=u.location,
                )
                for u in users
            ],
            "projects": [
                SearchResultProject(
                    id=p.id,
                    title=p.title,
                    slug=p.slug,
                    tagline=p.tagline,
                    description=p.description or "",
                    logo_url=p.logo_url,
                    stage=p.stage.value if p.stage else None,
                    stars=p.stars or 0,
                    tags=list(p.tags) if isinstance(p.tags, list) else [],
                )
                for p in projects
            ],
            "organizations": [
                SearchResultOrganization(
                    id=o.id,
                    name=o.name,
                    slug=o.slug,
                    description=o.description,
                    logo_url=o.logo_url,
                    organization_type=(
                        o.organization_type.value if o.organization_type else None
                    ),
                    location=o.location,
                    members_count=o.members_count or 0,
                    verified=o.verified,
                    hiring=o.hiring,
                )
                for o in organizations
            ],
            "skills": [
                SearchResultSkill(
                    id=s.id,
                    name=s.name,
                    slug=s.slug,
                    category=s.category,
                    description=s.description,
                )
                for s in skills
            ],
            "tags": list(tags),
        }
