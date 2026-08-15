from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.conversation import Conversation
from app.models.conversation_member import ConversationMember
from app.models.follower import Follower
from app.models.user import User


@pytest.fixture
def test_users(db: Session):
    user1 = User(
        id=uuid.uuid4(),
        email="blocker@example.com",
        username="blocker_user",
        first_name="Blocker",
        last_name="User",
        password_hash="hashed_password",
        is_active=True,
        is_private=False,
    )
    user2 = User(
        id=uuid.uuid4(),
        email="blocked@example.com",
        username="blocked_user",
        first_name="Blocked",
        last_name="User",
        password_hash="hashed_password",
        is_active=True,
        is_private=False,
    )
    user3 = User(
        id=uuid.uuid4(),
        email="privateuser@example.com",
        username="private_user",
        first_name="Private",
        last_name="User",
        password_hash="hashed_password",
        is_active=True,
        is_private=True,
    )
    db.add_all([user1, user2, user3])
    db.commit()
    return user1, user2, user3


@pytest.fixture
def auth_headers(test_users):
    user1, user2, user3 = test_users
    token1 = create_access_token(str(user1.id))
    token2 = create_access_token(str(user2.id))
    token3 = create_access_token(str(user3.id))
    return (
        {"Authorization": f"Bearer {token1}"},
        {"Authorization": f"Bearer {token2}"},
        {"Authorization": f"Bearer {token3}"},
    )


def test_block_and_unblock_user(
    client: TestClient, db: Session, test_users, auth_headers
):
    user1, user2, _ = test_users
    headers1, headers2, _ = auth_headers

    # User 1 blocks User 2
    res = client.post(f"/api/blocks/{user2.id}", headers=headers1)
    assert res.status_code == 201
    data = res.json()
    assert data["blocker_id"] == str(user1.id)
    assert data["blocked_id"] == str(user2.id)

    # Check status
    res = client.get(f"/api/blocks/{user2.id}/status", headers=headers1)
    assert res.status_code == 200
    status_data = res.json()
    assert status_data["is_blocked_by_me"] is True
    assert status_data["has_block_relationship"] is True

    # List blocked users for User 1
    res = client.get("/api/blocks", headers=headers1)
    assert res.status_code == 200
    blocked_list = res.json()
    assert len(blocked_list) == 1
    assert blocked_list[0]["id"] == str(user2.id)

    # User 1 unblocks User 2
    res = client.delete(f"/api/blocks/{user2.id}", headers=headers1)
    assert res.status_code == 204

    # Verify status after unblocking
    res = client.get(f"/api/blocks/{user2.id}/status", headers=headers1)
    assert res.status_code == 200
    assert res.json()["is_blocked_by_me"] is False


def get_error_msg(res) -> str:
    body = res.json()
    if isinstance(body, dict) and "error" in body:
        return body["error"].get("message", "").lower()
    if isinstance(body, dict) and "detail" in body:
        return str(body["detail"]).lower()
    return ""


def test_cannot_block_self(client: TestClient, test_users, auth_headers):
    user1, _, _ = test_users
    headers1, _, _ = auth_headers

    res = client.post(f"/api/blocks/{user1.id}", headers=headers1)
    assert res.status_code == 400
    assert "cannot block yourself" in get_error_msg(res)


def test_block_removes_follow_relationship(
    client: TestClient, db: Session, test_users, auth_headers
):
    user1, user2, _ = test_users
    headers1, _, _ = auth_headers

    # Create follow relationships
    f1 = Follower(follower_id=user1.id, following_id=user2.id)
    f2 = Follower(follower_id=user2.id, following_id=user1.id)
    db.add_all([f1, f2])
    db.commit()

    # User 1 blocks User 2
    res = client.post(f"/api/blocks/{user2.id}", headers=headers1)
    assert res.status_code == 201

    # Verify follows were deleted
    follows = db.query(Follower).all()
    assert len(follows) == 0


def test_blocked_user_cannot_follow(
    client: TestClient, db: Session, test_users, auth_headers
):
    user1, user2, _ = test_users
    headers1, headers2, _ = auth_headers

    # User 1 blocks User 2
    client.post(f"/api/blocks/{user2.id}", headers=headers1)

    # User 2 tries to follow User 1
    res = client.post(f"/api/followers/{user1.id}", headers=headers2)
    assert res.status_code == 403
    assert "cannot follow" in get_error_msg(res)


def test_blocked_user_cannot_send_message(
    client: TestClient, db: Session, test_users, auth_headers
):
    user1, user2, _ = test_users
    headers1, headers2, _ = auth_headers

    # Create conversation between User 1 and User 2
    conv = Conversation(id=uuid.uuid4(), title="Test Conv", created_by=user1.id)
    m1 = ConversationMember(conversation_id=conv.id, user_id=user1.id)
    m2 = ConversationMember(conversation_id=conv.id, user_id=user2.id)
    db.add_all([conv, m1, m2])
    db.commit()

    # User 1 blocks User 2
    client.post(f"/api/blocks/{user2.id}", headers=headers1)

    # User 2 tries to send message in conversation
    msg_payload = {
        "conversation_id": str(conv.id),
        "content": "Hello user 1",
    }
    res = client.post("/api/messages/", json=msg_payload, headers=headers2)
    assert res.status_code == 403
    assert "cannot send message" in get_error_msg(res)


def test_blocked_user_cannot_view_private_profile(
    client: TestClient, db: Session, test_users, auth_headers
):
    _, user2, user3 = test_users
    _, headers2, headers3 = auth_headers

    # User 3 (private user) blocks User 2
    client.post(f"/api/blocks/{user2.id}", headers=headers3)

    # User 2 tries to view User 3's profile
    res = client.get(f"/api/users/{user3.id}", headers=headers2)
    assert res.status_code == 403
    assert "permission to view this private profile" in get_error_msg(res)
