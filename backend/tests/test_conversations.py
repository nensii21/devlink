from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.models.user import User
from app.models.conversation import ConversationType
from app.models.conversation_member import ConversationMember, ConversationRole
from app.schemas.conversation import ConversationCreate
from app.services.conversation_service import ConversationService


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


def test_create_conversation_auto_adds_owner(db):
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


def test_add_creator_to_direct_fails(db):
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


def test_add_duplicate_member_fails(db):
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


def test_add_third_member_to_direct_fails(db):
    user1 = _create_user(db, "user1@example.com", "user1")
    user2 = _create_user(db, "user2@example.com", "user2")
    user3 = _create_user(db, "user3@example.com", "user3")

    conv_in = ConversationCreate(
        type=ConversationType.DIRECT,
        title="Direct Chat",
    )

    conv = ConversationService.create_conversation(db, user1.id, conv_in)
    # Creator user1 is auto-added as member. Let's add user2 (2nd member).
    ConversationService.add_member(db, conv.id, user2.id)

    # Adding user3 (3rd member) to direct conversation should fail
    with pytest.raises(HTTPException) as exc_info:
        ConversationService.add_member(db, conv.id, user3.id)

    assert exc_info.value.status_code == 400
    assert "cannot have more than 2 members" in exc_info.value.detail.lower()


def test_router_prevent_self_messaging_integration(client):

    # Register and login a user
    client.post(
        "/api/auth/register",
        json={
            "first_name": "Charlie",
            "last_name": "Test",
            "email": "charlie@example.com",
            "username": "charlie",
            "password": "Vermilion-Kestrel97!",
        },
    )

    login_resp = client.post(
        "/api/auth/login",
        json={
            "email": "charlie@example.com",
            "password": "Vermilion-Kestrel97!",
        },
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create direct conversation via router. The router is mounted under
    # `/api` (app/main.py), so the un-prefixed path this used to post to was a
    # 404 and the assertion below had never actually run.
    conv_resp = client.post(
        "/api/conversations/",
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
        f"/api/conversations/{conv_id}/members/{creator_id}",
        headers=headers,
    )
    assert add_resp.status_code == 400
    assert "cannot add yourself" in add_resp.json()["detail"].lower()
