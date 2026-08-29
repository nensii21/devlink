from __future__ import annotations

import logging
from collections import Counter
from typing import List, Optional, Sequence

from sqlalchemy import func, or_
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.project import Project
from app.models.skill import Skill
from app.models.user import User
from app.models.user_skill import UserSkill
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


def _is_postgres(db: Session) -> bool:
    """Check if the active database dialect is PostgreSQL."""
    try:
        bind = db.get_bind()
        return bind is not None and bind.dialect.name == "postgresql"
    except Exception:
        return False


# ---------------------------------------------------------------------
# Advanced developer filters (#945)
# ---------------------------------------------------------------------

# Mirrors the experience level vocabulary already used across onboarding
# and skill-level fields (see app.schemas.onboarding / app.models.user_skill).
_EXPERIENCE_RANK = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
}


def _apply_user_filters(
    query,
    *,
    skills: Optional[List[str]] = None,
    location: Optional[str] = None,
    experience: Optional[str] = None,
    availability: Optional[bool] = None,
    organization: Optional[str] = None,
    remote: Optional[bool] = None,
):
    """Apply optional advanced-search filters to a developer (User) query."""
    clean_skills = [s.strip() for s in (skills or []) if s and s.strip()]
    if clean_skills:
        lowered = [s.lower() for s in clean_skills]
        query = (
            query.join(UserSkill, UserSkill.user_id == User.id)
            .join(Skill, Skill.id == UserSkill.skill_id)
            .filter(func.lower(Skill.name).in_(lowered))
            .distinct()
        )

    if location and location.strip():
        query = query.filter(User.location.ilike(_ilike_pattern(location)))

    if experience and experience.strip():
        query = query.filter(
            func.lower(User.experience_level) == experience.strip().lower()
        )

    if organization and organization.strip():
        query = query.filter(User.company.ilike(_ilike_pattern(organization)))

    if availability is not None:
        query = query.filter(User.open_to_work.is_(availability))

    # There is no dedicated "remote" column on User; developers commonly use
    # "Remote" as their location, so we match on that existing field.
    if remote:
        query = query.filter(User.location.ilike("%remote%"))

    return query


def _last_active_sort_key(u: User):
    last = getattr(u, "last_active_at", None) or getattr(u, "last_login", None)
    if not last:
        return datetime.min.replace(tzinfo=timezone.utc)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return last


def _sort_users(users: List[User], sort: Optional[str]) -> List[User]:
    """Apply a non-relevance sort order to an already-filtered user list."""
    key = (sort or "").strip().lower()
    if key == "name":
        return sorted(users, key=lambda u: (u.username or "").lower())
    if key == "experience":
        return sorted(
            users,
            key=lambda u: _EXPERIENCE_RANK.get(
                (u.experience_level or "").strip().lower(), 0
            ),
            reverse=True,
        )
    if key == "recent":
        return sorted(users, key=_last_active_sort_key, reverse=True)
    return users


# ---------------------------------------------------------------------
# Per-category search helpers
# ---------------------------------------------------------------------


def _score_user(u: User, q: str) -> float:
    score = 0.0
    q_lower = q.lower()
    if u.role and q_lower in u.role.lower():
        score += 10.0
    if u.headline and q_lower in u.headline.lower():
        score += 5.0
    if u.bio and q_lower in u.bio.lower():
        score += 5.0

    if getattr(u, "is_verified", False):
        score += 10.0

    last = getattr(u, "last_active_at", None) or getattr(u, "last_login", None)
    if last:
        now = datetime.now(timezone.utc)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        days_ago = (now - last).days
        score += max(0, 20 - (days_ago * 0.5))

    if getattr(u, "profile_image", None):
        score += 5.0
    if getattr(u, "bio", None) and len(u.bio) > 20:
        score += 5.0
    if getattr(u, "location", None):
        score += 2.0
    if getattr(u, "github_url", None):
        score += 3.0
    if getattr(u, "linkedin_url", None):
        score += 3.0
    if getattr(u, "portfolio_url", None):
        score += 3.0
    if getattr(u, "resume_url", None):
        score += 3.0
    return score


def _score_project(p: Project, q: str) -> float:
    score = 0.0
    q_lower = q.lower()

    if p.tech_stack and q_lower in p.tech_stack.lower():
        score += 10.0
    if p.tags and any(q_lower in str(tag).lower() for tag in p.tags):
        score += 10.0

    score += (p.stars or 0) * 2.0
    score += (p.views or 0) * 0.1
    score += (p.applications_count or 0) * 5.0

    if getattr(p, "updated_at", None):
        now = datetime.now(timezone.utc)
        updated = p.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        days_ago = (now - updated).days
        score += max(0, 20 - (days_ago * 0.2))

    if getattr(p, "logo_url", None):
        score += 5.0
    if getattr(p, "banner_url", None):
        score += 2.0
    if getattr(p, "repository_url", None):
        score += 5.0
    if getattr(p, "demo_url", None):
        score += 5.0
    if getattr(p, "website_url", None):
        score += 2.0
    if getattr(p, "description", None) and len(p.description) > 50:
        score += 5.0
    return score


def _score_organization(o: Organization, q: str) -> float:
    score = 0.0
    q_lower = q.lower()

    if o.description and q_lower in o.description.lower():
        score += 10.0

    score += (o.members_count or 0) * 2.0
    if getattr(o, "verified", False):
        score += 20.0

    if getattr(o, "updated_at", None):
        now = datetime.now(timezone.utc)
        updated = o.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        days_ago = (now - updated).days
        score += max(0, 20 - (days_ago * 0.5))

    if getattr(o, "logo_url", None):
        score += 5.0
    if getattr(o, "location", None):
        score += 2.0
    if getattr(o, "description", None) and len(o.description) > 50:
        score += 5.0
    if getattr(o, "website_url", None):
        score += 3.0
    return score


def _score_skill(s: Skill, q: str) -> float:
    score = 0.0
    q_lower = q.lower()
    if s.name and q_lower in s.name.lower():
        score += 20.0
    if getattr(s, "category", None) and q_lower in s.category.lower():
        score += 10.0
    if getattr(s, "description", None):
        score += 5.0
    return score


def search_users(
    db: Session,
    q: str,
    limit: int = 20,
    *,
    skills: Optional[List[str]] = None,
    location: Optional[str] = None,
    experience: Optional[str] = None,
    availability: Optional[bool] = None,
    organization: Optional[str] = None,
    remote: Optional[bool] = None,
    sort: Optional[str] = None,
) -> List[User]:
    """Search active users by name / username / role / headline.

    Uses PostgreSQL Full-Text Search when connected to PostgreSQL,
    with a fallback to ILIKE for SQLite/other databases.

    Supports optional advanced filters (skills, location, experience level,
    open-to-work availability, organization/company, remote) and an
    alternate sort order (relevance, name, experience, recent).
    """
    clean_q = _normalize_query(q)
    if not clean_q:
        return []

    fetch_limit = max(limit * 3, 100)

    if _is_postgres(db):
        ts_vector = func.to_tsvector(
            "english",
            func.coalesce(User.username, "")
            + " "
            + func.coalesce(User.first_name, "")
            + " "
            + func.coalesce(User.last_name, "")
            + " "
            + func.coalesce(User.role, "")
            + " "
            + func.coalesce(User.headline, ""),
        )
        ts_query = func.websearch_to_tsquery("english", clean_q)
        query = db.query(User).filter(
            User.is_active.is_(True),
            ts_vector.op("@@")(ts_query),
        )
        query = _apply_user_filters(
            query,
            skills=skills,
            location=location,
            experience=experience,
            availability=availability,
            organization=organization,
            remote=remote,
        )
        results = (
            query.order_by(
                User.is_verified.desc(),
                User.premium.desc(),
                func.ts_rank(ts_vector, ts_query).desc(),
                User.username.asc(),
            )
            .limit(fetch_limit)
            .all()
        )
    else:
        pattern = _ilike_pattern(q)
        query = db.query(User).filter(
            User.is_active.is_(True),
            or_(
                User.username.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                User.role.ilike(pattern),
                User.headline.ilike(pattern),
            ),
        )
        query = _apply_user_filters(
            query,
            skills=skills,
            location=location,
            experience=experience,
            availability=availability,
            organization=organization,
            remote=remote,
        )
        results = (
            query.order_by(
                User.is_verified.desc(), User.premium.desc(), User.username.asc()
            )
            .limit(fetch_limit)
            .all()
        )

    if sort and sort.strip().lower() != "relevance":
        results = _sort_users(results, sort)
    else:
        results.sort(key=lambda x: _score_user(x, clean_q), reverse=True)
    return results[:limit]


def search_projects(db: Session, q: str, limit: int = 20) -> List[Project]:
    """Search published projects by title / tagline / description / tech stack.

    Uses PostgreSQL Full-Text Search when connected to PostgreSQL,
    with a fallback to ILIKE for SQLite/other databases.
    """
    clean_q = _normalize_query(q)
    if not clean_q:
        return []

    fetch_limit = max(limit * 3, 100)

    if _is_postgres(db):
        ts_vector = func.to_tsvector(
            "english",
            func.coalesce(Project.title, "")
            + " "
            + func.coalesce(Project.tagline, "")
            + " "
            + func.coalesce(Project.description, "")
            + " "
            + func.coalesce(Project.tech_stack, ""),
        )
        ts_query = func.websearch_to_tsquery("english", clean_q)
        results = (
            db.query(Project)
            .filter(
                Project.is_published.is_(True),
                Project.is_archived.is_(False),
                ts_vector.op("@@")(ts_query),
            )
            .order_by(
                func.ts_rank(ts_vector, ts_query).desc(),
                Project.stars.desc(),
                Project.created_at.desc(),
            )
            .limit(fetch_limit)
            .all()
        )
    else:
        pattern = _ilike_pattern(q)
        results = (
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
            .limit(fetch_limit)
            .all()
        )

    results.sort(key=lambda x: _score_project(x, clean_q), reverse=True)
    return results[:limit]


def search_organizations(db: Session, q: str, limit: int = 20) -> List[Organization]:
    """Search active organizations by name / slug / description / location.

    Uses PostgreSQL Full-Text Search when connected to PostgreSQL,
    with a fallback to ILIKE for SQLite/other databases.
    """
    clean_q = _normalize_query(q)
    if not clean_q:
        return []

    fetch_limit = max(limit * 3, 100)

    if _is_postgres(db):
        ts_vector = func.to_tsvector(
            "english",
            func.coalesce(Organization.name, "")
            + " "
            + func.coalesce(Organization.slug, "")
            + " "
            + func.coalesce(Organization.description, "")
            + " "
            + func.coalesce(Organization.location, ""),
        )
        ts_query = func.websearch_to_tsquery("english", clean_q)
        results = (
            db.query(Organization)
            .filter(
                Organization.active.is_(True),
                ts_vector.op("@@")(ts_query),
            )
            .order_by(
                func.ts_rank(ts_vector, ts_query).desc(),
                Organization.members_count.desc(),
                Organization.name.asc(),
            )
            .limit(fetch_limit)
            .all()
        )
    else:
        pattern = _ilike_pattern(q)
        results = (
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
            .limit(fetch_limit)
            .all()
        )

    results.sort(key=lambda x: _score_organization(x, clean_q), reverse=True)
    return results[:limit]


def search_skills(db: Session, q: str, limit: int = 20) -> List[Skill]:
    """Search skills by name / normalized_name / category / description.

    Uses PostgreSQL Full-Text Search when connected to PostgreSQL,
    with a fallback to ILIKE for SQLite/other databases.
    """
    clean_q = _normalize_query(q)
    if not clean_q:
        return []

    fetch_limit = max(limit * 3, 100)

    if _is_postgres(db):
        ts_vector = func.to_tsvector(
            "english",
            func.coalesce(Skill.name, "")
            + " "
            + func.coalesce(Skill.normalized_name, "")
            + " "
            + func.coalesce(Skill.category, "")
            + " "
            + func.coalesce(Skill.description, ""),
        )
        ts_query = func.websearch_to_tsquery("english", clean_q)
        results = (
            db.query(Skill)
            .filter(ts_vector.op("@@")(ts_query))
            .order_by(func.ts_rank(ts_vector, ts_query).desc(), Skill.name.asc())
            .limit(fetch_limit)
            .all()
        )
    else:
        pattern = _ilike_pattern(q)
        results = (
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
            .limit(fetch_limit)
            .all()
        )

    results.sort(key=lambda x: _score_skill(x, clean_q), reverse=True)
    return results[:limit]


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
        skills_filter: Optional[List[str]] = None,
        location: Optional[str] = None,
        experience: Optional[str] = None,
        availability: Optional[bool] = None,
        organization: Optional[str] = None,
        remote: Optional[bool] = None,
        sort: Optional[str] = None,
    ) -> dict:
        """Full paginated search across categories.

        When ``category`` is provided, only that category's results are
        returned (paginated). Otherwise, the top ``limit`` results from
        *each* category are returned (no cross-category pagination).

        The advanced filter parameters (``skills_filter``, ``location``,
        ``experience``, ``availability``, ``organization``, ``remote``) and
        ``sort`` only affect the "developers" (users) results, since those
        are attributes of developer profiles.
        """
        page = max(1, int(page or 1))
        limit = max(1, min(int(limit or 20), 100))

        user_filter_kwargs = dict(
            skills=skills_filter,
            location=location,
            experience=experience,
            availability=availability,
            organization=organization,
            remote=remote,
            sort=sort,
        )

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
                users = search_users(db, q, limit=limit + offset, **user_filter_kwargs)[
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
            users = search_users(db, q, limit=limit, **user_filter_kwargs)
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
                    is_verified=u.is_verified,
                    premium=u.premium,
                    experience_level=u.experience_level,
                    company=u.company,
                    open_to_work=u.open_to_work,
                    skills=[us.skill.name for us in (u.user_skills or []) if us.skill][
                        :6
                    ],
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
