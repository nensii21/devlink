import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.main import app
from app.dependencies import get_database, get_current_user
from app.models.user import User

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="test_client")
def fixture_test_client(db_session):
    # Setup mock current user
    mock_user = User(
        first_name="Post",
        last_name="Author",
        username="post_author",
        email="author@devlink.io",
        is_active=True,
    )
    db_session.add(mock_user)
    db_session.commit()
    db_session.refresh(mock_user)

    def override_get_database():
        return db_session

    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


def test_create_and_list_published_post(test_client, db_session):
    # 1. Create a published post
    payload = {
        "content": "Hello published feed! #python",
        "status": "published",
        "tags": ["python"],
    }
    response = test_client.post("/api/posts/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Hello published feed! #python"
    assert data["status"] == "published"
    assert "id" in data

    # 2. Verify it shows up in public list
    response = test_client.get("/api/posts/")
    assert response.status_code == 200
    posts = response.json()
    assert len(posts) == 1
    assert posts[0]["content"] == "Hello published feed! #python"


def test_create_and_manage_draft_post(test_client, db_session):
    # 1. Create a draft post
    payload = {"content": "This is a draft. #wip", "status": "draft", "tags": ["wip"]}
    response = test_client.post("/api/posts/", json=payload)
    assert response.status_code == 201
    draft_id = response.json()["id"]

    # 2. Verify it does NOT show up in public feed
    response = test_client.get("/api/posts/")
    posts = response.json()
    assert len(posts) == 0

    # 3. Verify it shows up in drafts list
    response = test_client.get("/api/posts/drafts")
    assert response.status_code == 200
    drafts = response.json()
    assert len(drafts) == 1
    assert drafts[0]["content"] == "This is a draft. #wip"
    assert drafts[0]["status"] == "draft"

    # 4. Edit draft
    update_payload = {"content": "This is an edited draft. #updated"}
    response = test_client.put(f"/api/posts/{draft_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["content"] == "This is an edited draft. #updated"

    # 5. Publish draft
    publish_payload = {"status": "published"}
    response = test_client.put(f"/api/posts/{draft_id}", json=publish_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "published"

    # 6. Verify it now appears in public feed
    response = test_client.get("/api/posts/")
    posts = response.json()
    assert len(posts) == 1
    assert posts[0]["content"] == "This is an edited draft. #updated"


def test_scheduled_post_flow(test_client, db_session):
    # 1. Create a scheduled post to publish 1 hour in the future
    future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    payload = {
        "content": "Scheduled feed post! #scheduled",
        "status": "published",
        "publish_at": future_time,
    }
    response = test_client.post("/api/posts/", json=payload)
    assert response.status_code == 201
    scheduled_id = response.json()["id"]
    assert response.json()["status"] == "scheduled"

    # 2. Verify it does NOT show in public list
    response = test_client.get("/api/posts/")
    assert len(response.json()) == 0

    # 3. Verify it shows up in drafts/scheduled list
    response = test_client.get("/api/posts/drafts")
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == scheduled_id

    # 4. Delete the scheduled post
    response = test_client.delete(f"/api/posts/{scheduled_id}")
    assert response.status_code == 204

    # 5. Verify it is gone from drafts
    response = test_client.get("/api/posts/drafts")
    assert len(response.json()) == 0
