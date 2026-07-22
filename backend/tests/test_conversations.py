from __future__ import annotations

import pytest
from app.database.base import Base
from app.dependencies import get_database
from app.main import app
from app.models.conversation import ConversationType
from app.models.conversation_member import ConversationMember, ConversationRole
from app.models.user import User
from app.schemas.conversation import ConversationCreate
from app.services.conversation_service import ConversationService
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
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


def test_create_conversation_auto_adds_owner():
    db = TestingSessionLocal()
    user = _create_user(db, "owner@example.com", "owner")

    conv_in = ConversationCreate(
        type=ConversationType.DIRECT,
        title="Direct Chat",
    )

    conv = ConversationService.create_conversation(db, user.id, conv_in)

    assert conv.id is not None
    assert conv.created_by == user.id

    # Verify owner is a member
    members = db.query(ConversationMember).filter_by(conversation_id=conv.id).all()
    assert len(members) == 1
    assert members[0].user_id == user.id
    assert members[0].role == ConversationRole.OWNER

    db.close()


def test_add_creator_to_direct_fails():
    db = TestingSessionLocal()
    user = _create_user(db, "owner@example.com", "owner")

    conv_in = ConversationCreate(
        type=ConversationType.DIRECT,
        title="Direct Chat",
    )

    conv = ConversationService.create_conversation(db, user.id, conv_in)

    # Adding the creator to their own direct conversation should fail
    with pytest.raises(HTTPException) as exc_info:
        ConversationService.add_member(db, conv.id, user.id)

    assert exc_info.value.status_code == 400
    assert "cannot add yourself" in exc_info.value.detail.lower()

    db.close()


def test_add_duplicate_member_fails():
    db = TestingSessionLocal()
    user1 = _create_user(db, "user1@example.com", "user1")
    user2 = _create_user(db, "user2@example.com", "user2")

    conv_in = ConversationCreate(
        type=ConversationType.GROUP,
        title="Group Chat",
    )

    conv = ConversationService.create_conversation(db, user1.id, conv_in)
    # Creator user1 is auto-added as member. Let's add user2.
    ConversationService.add_member(db, conv.id, user2.id)

    # Adding user2 again should fail
    with pytest.raises(HTTPException) as exc_info:
        ConversationService.add_member(db, conv.id, user2.id)

    assert exc_info.value.status_code == 400
    assert "already a member" in exc_info.value.detail.lower()

    db.close()


def test_add_third_member_to_direct_fails():
    db = TestingSessionLocal()
    user1 = _create_user(db, "user1@example.com", "user1")
    user2 = _create_user(db, "user2@example.com", "user2")
    user3 = _create_user(db, "user3@example.com", "user3")

    conv_in = ConversationCreate(
        type=ConversationType.DIRECT,
        title="Direct Chat",
    )

    conv = ConversationService.create_conversation(db, user1.id, conv_in)
    # user1 is creator/member. Adding user2.
    ConversationService.add_member(db, conv.id, user2.id)

    # Adding user3 should fail because direct conversation is full (has 2 members already)
    with pytest.raises(HTTPException) as exc_info:
        ConversationService.add_member(db, conv.id, user3.id)

    assert exc_info.value.status_code == 400
    assert "cannot have more than 2 members" in exc_info.value.detail.lower()

    db.close()


def test_router_prevent_self_messaging_integration():
    client = TestClient(app)

    # Register and login a user
    client.post(
        "/api/auth/register",
        json={
            "first_name": "Charlie",
            "last_name": "Test",
            "email": "charlie@example.com",
            "username": "charlie",
            "password": "Passw0rd!",
        },
    )

    login_resp = client.post(
        "/api/auth/login",
        json={
            "email": "charlie@example.com",
            "password": "Passw0rd!",
        },
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create direct conversation via router
    conv_resp = client.post(
        "/conversations/",
        json={
            "type": "direct",
        },
        headers=headers,
    )
    assert conv_resp.status_code == 201
    conv_id = conv_resp.json()["id"]
    creator_id = conv_resp.json()["created_by"]

    # Try to add creator as member (which represents self-messaging)
    add_resp = client.post(
        f"/conversations/{conv_id}/members/{creator_id}",
        headers=headers,
    )
    assert add_resp.status_code == 400
    assert "cannot add yourself" in add_resp.json()["detail"].lower()
