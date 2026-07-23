from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.cache import cached
from app.models.builder_flare import BuilderFlare, FlareStatus
from app.models.organization import Organization
from app.models.project import Project, ProjectVisibility
from app.models.skill import Skill
from app.models.user import User

# Maps the public ``types`` query-param values to internal entity keys.
# Kept module-level so the router can validate without importing models.
SEARCHABLE_TYPES: dict[str, str] = {
    "developers": "users",
    "projects": "projects",
    "organizations": "organizations",
    "skills": "skills",
    "flares": "flares",
}


class SearchService:
    """
    Unified global search across all primary DevLink entities.

    Each entity type is searched with a case-insensitive ``ilike`` across
    its most relevant text fields (name, title, description, etc.).
    Inactive / private / archived records are excluded so search results
    never surface content the requester would not be allowed to view.
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    @staticmethod
    @cached(ttl=60, key_prefix="search")
    def search(
        db: Session,
        q: str,
        types: list[str] | None = None,
        limit: int = 20,
    ) -> dict:
        """
        Run a unified search.

        Parameters
        ----------
        db
            Active SQLAlchemy session.
        q
            Raw query string (already trimmed / length-validated by the router).
        types
            Optional list of entity-type filters.  When ``None`` every
            searchable type is queried.  Accepted values:
            ``developers``, ``projects``, ``organizations``, ``skills``,
            ``flares``.
        limit
            Maximum results **per entity type**.

        Returns
        -------
        dict
            ``{"users": [...], "projects": [...], "organizations": [...],
            "skills": [...], "flares": [...]}`` — ready to be wrapped by
            :class:`app.schemas.search.SearchResponse`.
        """
        keyword = f"%{q}%"
        # Normalise requested types to internal keys; ``None`` → all.
        if types:
            requested = set()
            for t in types:
                key = SEARCHABLE_TYPES.get(t.strip().lower())
                if key:
                    requested.add(key)
        else:
            requested = set(SEARCHABLE_TYPES.values())

        results: dict[str, list] = {}

        if "users" in requested:
            results["users"] = SearchService._search_users(db, keyword, limit)
        if "projects" in requested:
            results["projects"] = SearchService._search_projects(db, keyword, limit)
        if "organizations" in requested:
            results["organizations"] = SearchService._search_organizations(
                db, keyword, limit
            )
        if "skills" in requested:
            results["skills"] = SearchService._search_skills(db, keyword, limit)
        if "flares" in requested:
            results["flares"] = SearchService._search_flares(db, keyword, limit)

        return results

    # ------------------------------------------------------------------
    # Per-entity searches
    # ------------------------------------------------------------------

    @staticmethod
    def _search_users(db: Session, keyword: str, limit: int) -> list[User]:
        """Search active users by name, username, headline, bio, role."""
        stmt = (
            select(User)
            .where(
                User.is_active.is_(True),
                or_(
                    User.first_name.ilike(keyword),
                    User.last_name.ilike(keyword),
                    User.username.ilike(keyword),
                    User.headline.ilike(keyword),
                    User.bio.ilike(keyword),
                    User.role.ilike(keyword),
                    User.company.ilike(keyword),
                    User.location.ilike(keyword),
                ),
            )
            .order_by(User.first_name, User.last_name)
            .limit(limit)
        )
        return list(db.scalars(stmt))

    @staticmethod
    def _search_projects(db: Session, keyword: str, limit: int) -> list[Project]:
        """Search public, non-archived projects by title, tagline, description, tech."""
        stmt = (
            select(Project)
            .options(selectinload(Project.owner))
            .where(
                Project.visibility == ProjectVisibility.PUBLIC,
                Project.is_archived.is_(False),
                or_(
                    Project.title.ilike(keyword),
                    Project.slug.ilike(keyword),
                    Project.tagline.ilike(keyword),
                    Project.description.ilike(keyword),
                    Project.tech_stack.ilike(keyword),
                ),
            )
            .order_by(Project.stars.desc(), Project.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt))

    @staticmethod
    def _search_organizations(
        db: Session, keyword: str, limit: int
    ) -> list[Organization]:
        """Search active organizations by name, slug, description."""
        stmt = (
            select(Organization)
            .options(selectinload(Organization.owner))
            .where(
                Organization.active.is_(True),
                or_(
                    Organization.name.ilike(keyword),
                    Organization.slug.ilike(keyword),
                    Organization.description.ilike(keyword),
                    Organization.location.ilike(keyword),
                ),
            )
            .order_by(Organization.members_count.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt))

    @staticmethod
    def _search_skills(db: Session, keyword: str, limit: int) -> list[Skill]:
        """Search skills by name, normalized name, category, description."""
        stmt = (
            select(Skill)
            .where(
                or_(
                    Skill.name.ilike(keyword),
                    Skill.normalized_name.ilike(keyword),
                    Skill.category.ilike(keyword),
                    Skill.description.ilike(keyword),
                ),
            )
            .order_by(Skill.name)
            .limit(limit)
        )
        return list(db.scalars(stmt))

    @staticmethod
    def _search_flares(db: Session, keyword: str, limit: int) -> list[BuilderFlare]:
        """Search open/paused flares by title, description, role."""
        stmt = (
            select(BuilderFlare)
            .where(
                BuilderFlare.status != FlareStatus.CLOSED,
                or_(
                    BuilderFlare.title.ilike(keyword),
                    BuilderFlare.description.ilike(keyword),
                    BuilderFlare.role.ilike(keyword),
                ),
            )
            .order_by(BuilderFlare.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt))
