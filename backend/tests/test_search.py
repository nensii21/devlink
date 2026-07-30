from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dependencies import get_database
from app.main import app
from app.models.organization import Organization, OrganizationType
from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.skill import Skill
from app.models.user import User

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _create_user(
    db,
    email: str,
    username: str,
    first_name: str | None = None,
    last_name: str | None = None,
    role: str | None = None,
    headline: str | None = None,
) -> User:
    user = User(
        email=email,
        username=username,
        first_name=first_name or username.capitalize(),
        last_name=last_name or "Test",
        password_hash="fakehash",
        is_active=True,
        role=role,
        headline=headline,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_project(
    db,
    owner: User,
    title: str,
    slug: str,
    description: str = "A test project.",
    tagline: str | None = None,
    tech_stack: str | None = None,
    tags: list[str] | None = None,
    stars: int = 0,
    is_published: bool = True,
) -> Project:
    project = Project(
        owner_id=owner.id,
        title=title,
        slug=slug,
        description=description,
        tagline=tagline,
        tech_stack=tech_stack,
        tags=tags or [],
        stars=stars,
        stage=ProjectStage.MVP,
        visibility=ProjectVisibility.PUBLIC,
        is_published=is_published,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _create_organization(
    db,
    owner: User,
    name: str,
    slug: str,
    description: str | None = None,
    location: str | None = None,
    members_count: int = 1,
    verified: bool = False,
    hiring: bool = False,
    active: bool = True,
) -> Organization:
    org = Organization(
        owner_id=owner.id,
        name=name,
        slug=slug,
        description=description,
        organization_type=OrganizationType.STARTUP,
        location=location,
        members_count=members_count,
        verified=verified,
        hiring=hiring,
        active=active,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _create_skill(db, name: str, slug: str, category: str | None = None) -> Skill:
    skill = Skill(
        name=name,
        normalized_name=name.lower(),
        slug=slug,
        category=category,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


# ---------------------------------------------------------------------
# /api/search — full search
# ---------------------------------------------------------------------


def test_search_empty_query_returns_empty_categories():
    client = TestClient(app)
    r = client.get("/api/search", params={"q": ""})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == ""
    assert body["users"] == []
    assert body["projects"] == []
    assert body["organizations"] == []
    assert body["skills"] == []
    assert body["tags"] == []
    assert body["counts"]["total"] == 0


def test_search_matches_users_by_name_and_username():
    client = TestClient(app)
    db = TestingSessionLocal()
    _create_user(
        db, "alice@example.com", "alice", first_name="Alice", last_name="Wonder"
    )
    _create_user(db, "bob@example.com", "bob", first_name="Bob", last_name="Builder")
    db.close()

    r = client.get("/api/search", params={"q": "alice"})
    assert r.status_code == 200
    users = r.json()["users"]
    assert len(users) == 1
    assert users[0]["username"] == "alice"
    assert "Alice" in users[0]["name"]


def test_search_matches_projects_by_title_and_description():
    client = TestClient(app)
    db = TestingSessionLocal()
    owner = _create_user(db, "owner@example.com", "owner")
    _create_project(
        db,
        owner,
        title="Awesome React App",
        slug="awesome-react-app",
        description="A React app for collaboration.",
    )
    _create_project(
        db,
        owner,
        title="Backend Service",
        slug="backend-service",
        description="A Python FastAPI backend.",
    )
    db.close()

    r = client.get("/api/search", params={"q": "react"})
    assert r.status_code == 200
    titles = [p["title"] for p in r.json()["projects"]]
    assert "Awesome React App" in titles
    assert "Backend Service" not in titles


def test_search_matches_organizations_by_name_and_location():
    client = TestClient(app)
    db = TestingSessionLocal()
    owner = _create_user(db, "orgowner@example.com", "orgowner")
    _create_organization(db, owner, "Acme Inc", "acme-inc", location="San Francisco")
    _create_organization(db, owner, "Globex Corp", "globex-corp", location="Berlin")
    db.close()

    r = client.get("/api/search", params={"q": "berlin"})
    assert r.status_code == 200
    names = [o["name"] for o in r.json()["organizations"]]
    assert "Globex Corp" in names
    assert "Acme Inc" not in names


def test_search_matches_skills_by_name():
    client = TestClient(app)
    db = TestingSessionLocal()
    _create_skill(db, "Python", "python", category="Languages")
    _create_skill(db, "TypeScript", "typescript", category="Languages")
    db.close()

    r = client.get("/api/search", params={"q": "python"})
    assert r.status_code == 200
    names = [s["name"] for s in r.json()["skills"]]
    assert "Python" in names
    assert "TypeScript" not in names


def test_search_matches_tags_inside_project_tags_json():
    client = TestClient(app)
    db = TestingSessionLocal()
    owner = _create_user(db, "tagowner@example.com", "tagowner")
    _create_project(
        db,
        owner,
        title="Tagged Project",
        slug="tagged-project",
        tags=["react", "typescript", "vite"],
    )
    _create_project(
        db,
        owner,
        title="Other Project",
        slug="other-project",
        tags=["python", "fastapi"],
    )
    db.close()

    r = client.get("/api/search", params={"q": "react"})
    assert r.status_code == 200
    tag_names = [t["name"] for t in r.json()["tags"]]
    assert "react" in tag_names
    assert "python" not in tag_names


def test_search_counts_reflect_active_query():
    client = TestClient(app)
    db = TestingSessionLocal()
    owner = _create_user(db, "count@example.com", "countowner")
    _create_user(db, "alice@example.com", "alice", first_name="Alice")
    _create_project(db, owner, title="Alice Project", slug="alice-project")
    _create_organization(db, owner, "Alice Org", "alice-org")
    _create_skill(db, "AliceSkill", "aliceskill")
    _create_project(db, owner, title="Tagged", slug="tagged", tags=["alice-tag"])
    db.close()

    r = client.get("/api/search", params={"q": "alice"})
    assert r.status_code == 200
    counts = r.json()["counts"]
    assert counts["developers"] >= 1
    assert counts["projects"] >= 1
    assert counts["organizations"] >= 1
    assert counts["skills"] >= 1
    assert counts["tags"] >= 1
    assert counts["total"] == sum(
        counts[k] for k in ("developers", "projects", "organizations", "skills", "tags")
    )


def test_search_category_filter_returns_only_that_category():
    client = TestClient(app)
    db = TestingSessionLocal()
    owner = _create_user(db, "filter@example.com", "filterowner")
    _create_user(db, "alice@example.com", "alice", first_name="Alice")
    _create_project(db, owner, title="Alice Project", slug="alice-project")
    db.close()

    r = client.get("/api/search", params={"q": "alice", "category": "projects"})
    assert r.status_code == 200
    body = r.json()
    assert body["category"] == "projects"
    assert len(body["projects"]) >= 1
    # Other categories must be empty in single-category mode.
    assert body["users"] == []
    assert body["organizations"] == []
    assert body["skills"] == []
    assert body["tags"] == []


def test_search_excludes_archived_and_unpublished_projects():
    client = TestClient(app)
    db = TestingSessionLocal()
    owner = _create_user(db, "arch@example.com", "archowner")
    _create_project(
        db,
        owner,
        title="Published Project",
        slug="published-project",
        is_published=True,
    )
    _create_project(
        db,
        owner,
        title="Hidden Project",
        slug="hidden-project",
        is_published=False,
    )
    archived = _create_project(
        db,
        owner,
        title="Archived Project",
        slug="archived-project",
    )
    archived.is_archived = True
    db.commit()
    db.close()

    r = client.get("/api/search", params={"q": "project"})
    assert r.status_code == 200
    titles = [p["title"] for p in r.json()["projects"]]
    assert "Published Project" in titles
    assert "Hidden Project" not in titles
    assert "Archived Project" not in titles


def test_search_excludes_inactive_users():
    client = TestClient(app)
    db = TestingSessionLocal()
    _create_user(db, "active@example.com", "activeuser", first_name="Active")
    inactive = _create_user(
        db, "inactive@example.com", "inactiveuser", first_name="Inactive"
    )
    inactive.is_active = False
    db.commit()
    db.close()

    r = client.get("/api/search", params={"q": "active"})
    assert r.status_code == 200
    usernames = [u["username"] for u in r.json()["users"]]
    assert "activeuser" in usernames


def test_search_excludes_inactive_organizations():
    client = TestClient(app)
    db = TestingSessionLocal()
    owner = _create_user(db, "o@example.com", "orgowner")
    _create_organization(db, owner, "Active Org", "active-org", active=True)
    _create_organization(db, owner, "Dead Org", "dead-org", active=False)
    db.close()

    r = client.get("/api/search", params={"q": "org"})
    assert r.status_code == 200
    names = [o["name"] for o in r.json()["organizations"]]
    assert "Active Org" in names
    assert "Dead Org" not in names


def test_search_pagination_in_category_mode():
    client = TestClient(app)
    db = TestingSessionLocal()
    owner = _create_user(db, "page@example.com", "pageowner")
    # Create 5 matching projects.
    for i in range(5):
        _create_project(
            db,
            owner,
            title=f"Pagination Project {i}",
            slug=f"pagination-project-{i}",
        )
    db.close()

    # Page 1, limit 2 → 2 results.
    r1 = client.get(
        "/api/search",
        params={"q": "pagination", "category": "projects", "page": 1, "limit": 2},
    )
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["page"] == 1
    assert body1["limit"] == 2
    assert len(body1["projects"]) == 2

    # Page 3, limit 2 → 1 result (5 total).
    r3 = client.get(
        "/api/search",
        params={"q": "pagination", "category": "projects", "page": 3, "limit": 2},
    )
    assert r3.status_code == 200
    body3 = r3.json()
    assert len(body3["projects"]) == 1


def test_search_handles_special_characters_safely():
    client = TestClient(app)
    # Characters that have meaning in SQL LIKE patterns must be escaped.
    r = client.get("/api/search", params={"q": "%_%"})
    assert r.status_code == 200


def test_search_unknown_category_returns_empty_results():
    client = TestClient(app)
    r = client.get("/api/search", params={"q": "anything", "category": "unknown"})
    assert r.status_code == 200
    body = r.json()
    assert body["users"] == []
    assert body["projects"] == []
    assert body["organizations"] == []
    assert body["skills"] == []
    assert body["tags"] == []


# ---------------------------------------------------------------------
# /api/search/autocomplete
# ---------------------------------------------------------------------


def test_autocomplete_empty_query_returns_empty_lists():
    client = TestClient(app)
    r = client.get("/api/search/autocomplete", params={"q": ""})
    assert r.status_code == 200
    body = r.json()
    assert body["users"] == []
    assert body["projects"] == []
    assert body["organizations"] == []
    assert body["skills"] == []
    assert body["tags"] == []


def test_autocomplete_returns_per_category_matches():
    client = TestClient(app)
    db = TestingSessionLocal()
    owner = _create_user(db, "ac@example.com", "acowner")
    _create_user(db, "alice@example.com", "alice", first_name="Alice")
    _create_project(db, owner, title="Alice Project", slug="alice-project")
    _create_organization(db, owner, "Alice Org", "alice-org")
    _create_skill(db, "AliceSkill", "aliceskill")
    _create_project(db, owner, title="Tagged", slug="tagged", tags=["alice-tag"])
    db.close()

    r = client.get("/api/search/autocomplete", params={"q": "alice"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["users"]) >= 1
    assert len(body["projects"]) >= 1
    assert len(body["organizations"]) >= 1
    assert len(body["skills"]) >= 1
    assert len(body["tags"]) >= 1


def test_autocomplete_respects_per_category_default_limit():
    client = TestClient(app)
    db = TestingSessionLocal()
    for i in range(10):
        _create_user(db, f"u{i}@example.com", f"user{i}", first_name=f"User{i}")
    db.close()

    r = client.get("/api/search/autocomplete", params={"q": "user"})
    assert r.status_code == 200
    # Default per_category is 3.
    assert len(r.json()["users"]) <= 5


# ---------------------------------------------------------------------
# /api/search/suggestions
# ---------------------------------------------------------------------


def test_suggestions_empty_query_returns_empty_list():
    client = TestClient(app)
    r = client.get("/api/search/suggestions", params={"q": ""})
    assert r.status_code == 200
    assert r.json() == []


def test_suggestions_returns_flat_deduplicated_list():
    client = TestClient(app)
    db = TestingSessionLocal()
    owner = _create_user(db, "sug@example.com", "sugowner")
    _create_user(db, "alice@example.com", "alice", first_name="Alice")
    _create_project(db, owner, title="Alice Project", slug="alice-project")
    _create_organization(db, owner, "Alice Org", "alice-org")
    _create_skill(db, "AliceSkill", "aliceskill")
    db.close()

    r = client.get("/api/search/suggestions", params={"q": "alice"})
    assert r.status_code == 200
    suggestions = r.json()
    assert isinstance(suggestions, list)
    assert len(suggestions) >= 1
    # No duplicates (case-insensitive).
    lowered = [s.lower() for s in suggestions]
    assert len(lowered) == len(set(lowered))


def test_suggestions_respects_limit_param():
    client = TestClient(app)
    db = TestingSessionLocal()
    owner = _create_user(db, "lim@example.com", "limowner")
    for i in range(8):
        _create_user(db, f"u{i}@example.com", f"user{i}", first_name=f"User{i}")
    db.close()

    r = client.get("/api/search/suggestions", params={"q": "user", "limit": 3})
    assert r.status_code == 200
    assert len(r.json()) <= 3
