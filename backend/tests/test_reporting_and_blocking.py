import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_database,
)
from app.main import app
from app.models.post import Post
from app.models.user import User
from app.models.user_block import UserBlock
from app.models.user_report import UserReport

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


def _create_user(db, email: str, username: str) -> User:
    user = User(
        email=email,
        username=username,
        first_name="User",
        last_name=username,
        password_hash="fakehash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_post(db, author: User, content: str = "Test post") -> Post:
    post = Post(
        author_id=author.id,
        content=content,
        status="published",
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def test_report_profile_success(db_session):
    user_a = _create_user(db_session, "usera@test.com", "usera")
    user_b = _create_user(db_session, "userb@test.com", "userb")

    def override_get_database():
        return db_session

    def override_get_current_user():
        return user_a

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_db] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_optional] = override_get_current_user

    try:
        client = TestClient(app)
        headers = {"Origin": "http://localhost:3000"}
        payload = {
            "reason": "Harassment",
            "description": "Inappropriate comments on profile",
        }
        res = client.post(f"/api/users/{user_b.id}/report", json=payload, headers=headers)
        assert res.status_code == 201, res.text
        data = res.json()
        assert data["reporter_id"] == str(user_a.id)
        assert data["reported_id"] == str(user_b.id)
        assert data["reason"] == "Harassment"
    finally:
        app.dependency_overrides.clear()


def test_report_post_success(db_session):
    author = _create_user(db_session, "author@test.com", "postauthor")
    reporter = _create_user(db_session, "reporter@test.com", "postreporter")
    post = _create_post(db_session, author, "Suspicious content")

    def override_get_database():
        return db_session

    def override_get_current_user():
        return reporter

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_db] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_optional] = override_get_current_user

    try:
        client = TestClient(app)
        headers = {"Origin": "http://localhost:3000"}
        payload = {
            "reason": "Spam",
            "description": "Unwanted spam link in post",
        }
        res = client.post(f"/api/posts/{post.id}/report", json=payload, headers=headers)
        assert res.status_code == 201, res.text
        data = res.json()
        assert data["reporter_id"] == str(reporter.id)
        assert data["reported_id"] == str(author.id)
        assert data["post_id"] == str(post.id)
        assert data["reason"] == "Spam"
    finally:
        app.dependency_overrides.clear()


def test_block_unblock_user(db_session):
    blocker = _create_user(db_session, "blocker@test.com", "blocker")
    blocked = _create_user(db_session, "blocked@test.com", "blocked")

    def override_get_database():
        return db_session

    def override_get_current_user():
        return blocker

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_db] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_optional] = override_get_current_user

    try:
        client = TestClient(app)
        headers = {"Origin": "http://localhost:3000"}

        # Block user
        res_block = client.post(f"/api/blocks/{blocked.id}", headers=headers)
        assert res_block.status_code == 201, res_block.text
        assert res_block.json()["blocked_id"] == str(blocked.id)

        # List blocked users
        res_list = client.get("/api/blocks/", headers=headers)
        assert res_list.status_code == 200, res_list.text
        assert len(res_list.json()) == 1
        assert res_list.json()[0]["username"] == "blocked"

        # Check block status
        res_status = client.get(f"/api/blocks/{blocked.id}/status", headers=headers)
        assert res_status.status_code == 200, res_status.text
        assert res_status.json()["is_blocked_by_me"] is True

        # Unblock user
        res_unblock = client.delete(f"/api/blocks/{blocked.id}", headers=headers)
        assert res_unblock.status_code == 204, res_unblock.text

        # List blocked users again
        res_list_after = client.get("/api/blocks/", headers=headers)
        assert res_list_after.status_code == 200, res_list_after.text
        assert len(res_list_after.json()) == 0
    finally:
        app.dependency_overrides.clear()


def test_hidden_content_from_blocked_users(db_session):
    viewer = _create_user(db_session, "viewer@test.com", "vieweruser")
    blocked_user = _create_user(db_session, "baduser@test.com", "baduser")
    good_user = _create_user(db_session, "gooduser@test.com", "gooduser")

    post_blocked = _create_post(db_session, blocked_user, "Post from blocked user")
    post_good = _create_post(db_session, good_user, "Post from friendly user")

    # Viewer blocks baduser
    block = UserBlock(blocker_id=viewer.id, blocked_id=blocked_user.id)
    db_session.add(block)
    db_session.commit()

    def override_get_database():
        return db_session

    def override_get_current_user():
        return viewer

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_db] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_optional] = override_get_current_user

    try:
        client = TestClient(app)
        headers = {"Origin": "http://localhost:3000"}
        res = client.get("/api/posts/", headers=headers)
        assert res.status_code == 200, res.text
        posts = res.json()
        post_ids = [p["id"] for p in posts]
        assert str(post_good.id) in post_ids
        assert str(post_blocked.id) not in post_ids
    finally:
        app.dependency_overrides.clear()
