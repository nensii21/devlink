from __future__ import annotations

import pytest
from app.database.base import Base
from app.dependencies import get_database
from app.main import app
from app.models.project import ProjectStage, ProjectVisibility
from app.models.user import User
from app.schemas.project import ProjectCreate
from app.services.project_service import ProjectService
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_database] = override_get_db
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def _create_user(db, email: str, username: str) -> User:
    user = User(
        email=email,
        username=username,
        first_name=username.capitalize(),
        last_name="Test",
        password_hash="fakehash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_get_project_by_id_increments_views():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = _create_user(db, "owner@example.com", "owner")

    project_in = ProjectCreate(
        title="Test Project ID",
        slug="test-project-id",
        description="A project to test views by ID.",
        stage=ProjectStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
    )
    project = ProjectService.create_project(db, user.id, project_in)
    project_id = str(project.id)

    # Views should initially be 0
    assert project.views == 0

    # Request the project by ID
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["views"] == 1

    # Request the project again by ID
    response2 = client.get(f"/api/projects/{project_id}")
    assert response2.status_code == 200
    assert response2.json()["views"] == 2

    db.close()


def test_get_project_by_slug_increments_views():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = _create_user(db, "owner2@example.com", "owner2")

    project_in = ProjectCreate(
        title="Test Project Slug",
        slug="test-project-slug",
        description="A project to test views by slug.",
        stage=ProjectStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
    )
    project = ProjectService.create_project(db, user.id, project_in)
    project_slug = project.slug

    # Views should initially be 0
    assert project.views == 0

    # Request the project by slug
    response = client.get(f"/api/projects/slug/{project_slug}")
    assert response.status_code == 200
    assert response.json()["views"] == 1

    # Request the project again by slug
    response2 = client.get(f"/api/projects/slug/{project_slug}")
    assert response2.status_code == 200
    assert response2.json()["views"] == 2

    db.close()


def test_list_projects_does_not_increment_views():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = _create_user(db, "owner3@example.com", "owner3")

    project_in = ProjectCreate(
        title="Test Project List",
        slug="test-project-list",
        description="A project to test views in list.",
        stage=ProjectStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
    )
    project = ProjectService.create_project(db, user.id, project_in)

    # List projects
    response = client.get("/api/projects/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    # The view count should remain 0 in the list response
    list_project = next(p for p in data if p["slug"] == "test-project-list")
    assert list_project["views"] == 0

    # Refresh from DB to ensure it wasn't modified
    db.refresh(project)
    assert project.views == 0

    db.close()


import uuid  # noqa: E402

import pytest  # noqa: E402


def test_create_project(client: TestClient, register_and_login):
    _, token = register_and_login("proj1@example.com", "proj1user")

    response = client.post(
        "/api/projects/",
        json={
            "title": "My Awesome Project",
            "slug": "my-awesome-project",
            "description": "A very awesome project.",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Awesome Project"
    assert data["slug"] == "my-awesome-project"
    assert "id" in data


def test_create_project_duplicate_slug(client: TestClient, register_and_login):
    _, token = register_and_login("projdup@example.com", "projdupuser")
    payload = {
        "title": "Dup Project",
        "slug": "dup-project",
        "description": "Desc",
        "status": "active",
        "visibility": "public",
    }
    client.post(
        "/api/projects/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )

    response = client.post(
        "/api/projects/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "slug already exists" in response.json()["detail"].lower()


def test_get_project(client: TestClient, register_and_login):
    _, token = register_and_login("getproj@example.com", "getprojuser")
    create_resp = client.post(
        "/api/projects/",
        json={
            "title": "Get Proj",
            "slug": "get-proj",
            "description": "Desc",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    proj_id = create_resp.json()["id"]

    response = client.get(f"/api/projects/{proj_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Get Proj"


def test_get_project_not_found(client: TestClient):
    response = client.get(f"/api/projects/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_project_by_slug(client: TestClient, register_and_login):
    _, token = register_and_login("slugproj@example.com", "slugprojuser")
    client.post(
        "/api/projects/",
        json={
            "title": "Slug Proj",
            "slug": "slug-proj",
            "description": "Desc",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get("/api/projects/slug/slug-proj")
    assert response.status_code == 200
    assert response.json()["title"] == "Slug Proj"


def test_get_project_by_slug_not_found(client: TestClient):
    response = client.get("/api/projects/slug/nonexistent-slug")
    assert response.status_code == 404


def test_list_projects(client: TestClient, register_and_login):
    _, token = register_and_login("listproj@example.com", "listprojuser")
    client.post(
        "/api/projects/",
        json={
            "title": "List 1",
            "slug": "list-1",
            "description": "Desc",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/api/projects/",
        json={
            "title": "List 2",
            "slug": "list-2",
            "description": "Desc",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get("/api/projects/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_my_projects(client: TestClient, register_and_login):
    _, token1 = register_and_login("myproj1@example.com", "myproj1")
    _, token2 = register_and_login("myproj2@example.com", "myproj2")

    client.post(
        "/api/projects/",
        json={
            "title": "P1",
            "slug": "p-1",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    client.post(
        "/api/projects/",
        json={
            "title": "P2",
            "slug": "p-2",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    client.post(
        "/api/projects/",
        json={
            "title": "P3",
            "slug": "p-3",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token2}"},
    )

    response = client.get(
        "/api/projects/me/list", headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for p in data:
        assert p["title"] in ["P1", "P2"]


def test_update_project(client: TestClient, register_and_login):
    _, token = register_and_login("updproj@example.com", "updprojuser")
    c_resp = client.post(
        "/api/projects/",
        json={
            "title": "U",
            "slug": "u",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = c_resp.json()["id"]

    u_resp = client.put(
        f"/api/projects/{pid}",
        json={"title": "U2", "slug": "u2"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert u_resp.status_code == 200
    assert u_resp.json()["title"] == "U2"
    assert u_resp.json()["slug"] == "u2"


def test_update_project_not_found(client: TestClient, register_and_login):
    _, token = register_and_login("updnf@example.com", "updnf")
    response = client.put(
        f"/api/projects/{uuid.uuid4()}",
        json={"title": "X"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_update_project_permission_denied(client: TestClient, register_and_login):
    _, token1 = register_and_login("updperm1@example.com", "updperm1")
    _, token2 = register_and_login("updperm2@example.com", "updperm2")
    c_resp = client.post(
        "/api/projects/",
        json={
            "title": "U",
            "slug": "u-perm",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    pid = c_resp.json()["id"]

    u_resp = client.put(
        f"/api/projects/{pid}",
        json={"title": "U2"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert u_resp.status_code == 403


def test_archive_project(client: TestClient, register_and_login):
    _, token = register_and_login("arch@example.com", "arch")
    c = client.post(
        "/api/projects/",
        json={
            "title": "A",
            "slug": "a-arch",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = c.json()["id"]

    a = client.patch(
        f"/api/projects/{pid}/archive", headers={"Authorization": f"Bearer {token}"}
    )
    assert a.status_code == 200
    # status becomes "archived" typically, check implementation

    # Try archiving a not found project
    nf = client.patch(
        f"/api/projects/{uuid.uuid4()}/archive",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert nf.status_code == 404

    # Permission denied
    _, token2 = register_and_login("arch2@example.com", "arch2")
    pd = client.patch(
        f"/api/projects/{pid}/archive", headers={"Authorization": f"Bearer {token2}"}
    )
    assert pd.status_code == 403


def test_restore_project(client: TestClient, register_and_login):
    _, token = register_and_login("rest@example.com", "rest")
    c = client.post(
        "/api/projects/",
        json={
            "title": "R",
            "slug": "r-rest",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = c.json()["id"]

    client.patch(
        f"/api/projects/{pid}/archive", headers={"Authorization": f"Bearer {token}"}
    )
    r = client.patch(
        f"/api/projects/{pid}/restore", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200

    nf = client.patch(
        f"/api/projects/{uuid.uuid4()}/restore",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert nf.status_code == 404

    _, token2 = register_and_login("rest2@example.com", "rest2")
    pd = client.patch(
        f"/api/projects/{pid}/restore", headers={"Authorization": f"Bearer {token2}"}
    )
    assert pd.status_code == 403


def test_feature_project(client: TestClient, register_and_login):
    _, token = register_and_login("feat@example.com", "feat")
    c = client.post(
        "/api/projects/",
        json={
            "title": "F",
            "slug": "f-feat",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = c.json()["id"]

    f = client.patch(f"/api/projects/{pid}/feature")
    assert f.status_code == 200

    nf = client.patch(f"/api/projects/{uuid.uuid4()}/feature")
    assert nf.status_code == 404


def test_star_unstar_project(client: TestClient, register_and_login):
    _, token = register_and_login("star@example.com", "star")
    c = client.post(
        "/api/projects/",
        json={
            "title": "S",
            "slug": "s-star",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = c.json()["id"]

    s = client.post(f"/api/projects/{pid}/star")
    assert s.status_code == 200

    us = client.delete(f"/api/projects/{pid}/star")
    assert us.status_code == 200

    nf1 = client.post(f"/api/projects/{uuid.uuid4()}/star")
    assert nf1.status_code == 404

    nf2 = client.delete(f"/api/projects/{uuid.uuid4()}/star")
    assert nf2.status_code == 404


def test_get_project_stats(client: TestClient, register_and_login):
    _, token = register_and_login("stats@example.com", "stats")
    c = client.post(
        "/api/projects/",
        json={
            "title": "St",
            "slug": "st-stats",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = c.json()["id"]

    s = client.get(
        f"/api/projects/{pid}/stats", headers={"Authorization": f"Bearer {token}"}
    )
    assert s.status_code == 200
    assert "views" in s.json()  # Assuming it returns views/stars etc

    nf = client.get(
        f"/api/projects/{uuid.uuid4()}/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert nf.status_code == 404

    _, token2 = register_and_login("stats2@example.com", "stats2")
    pd = client.get(
        f"/api/projects/{pid}/stats", headers={"Authorization": f"Bearer {token2}"}
    )
    assert pd.status_code == 403


def test_delete_project(client: TestClient, register_and_login):
    _, token = register_and_login("del@example.com", "del")
    c = client.post(
        "/api/projects/",
        json={
            "title": "D",
            "slug": "d-del",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = c.json()["id"]

    d = client.delete(
        f"/api/projects/{pid}", headers={"Authorization": f"Bearer {token}"}
    )
    assert d.status_code == 204

    nf = client.delete(
        f"/api/projects/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"}
    )
    assert nf.status_code == 404


def test_delete_project_permission_denied(client: TestClient, register_and_login):
    _, token1 = register_and_login("delpd1@example.com", "delpd1")
    _, token2 = register_and_login("delpd2@example.com", "delpd2")
    c = client.post(
        "/api/projects/",
        json={
            "title": "D",
            "slug": "d-delpd",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    pid = c.json()["id"]

    d = client.delete(
        f"/api/projects/{pid}", headers={"Authorization": f"Bearer {token2}"}
    )
    assert d.status_code == 403


def test_invite_user(client: TestClient, register_and_login):
    uid1, token1 = register_and_login("inv1@example.com", "inv1")
    uid2, token2 = register_and_login("inv2@example.com", "inv2")

    c = client.post(
        "/api/projects/",
        json={
            "title": "I",
            "slug": "i-inv",
            "description": "D",
            "status": "active",
            "visibility": "public",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    pid = c.json()["id"]

    i = client.post(
        f"/api/projects/{pid}/invite/{uid2}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert i.status_code == 201

    # duplicate invite
    i_dup = client.post(
        f"/api/projects/{pid}/invite/{uid2}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert i_dup.status_code == 400

    # project not found
    nf = client.post(
        f"/api/projects/{uuid.uuid4()}/invite/{uid2}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert nf.status_code == 404

    # permission denied
    pd = client.post(
        f"/api/projects/{pid}/invite/{uid1}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert pd.status_code == 403
