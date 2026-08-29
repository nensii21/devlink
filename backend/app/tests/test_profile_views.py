import uuid
import pytest
from fastapi.testclient import TestClient

from app.models.user import User
from app.services.profile_view_service import ProfileViewService


def create_test_user(db, email: str, username: str) -> User:
    user = User(
        first_name="Test",
        last_name="User",
        username=username,
        email=email,
        password_hash="secret_hash",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_record_profile_view_service(db):
    user1 = create_test_user(db, "pv1@example.com", "pvuser1")
    user2 = create_test_user(db, "pv2@example.com", "pvuser2")

    view = ProfileViewService.record_view(
        db, viewed_user_id=user2.id, viewer_id=user1.id
    )
    assert view is not None
    assert view.viewed_user_id == user2.id
    assert view.viewer_id == user1.id
    assert view.is_anonymous is False
    assert view.visit_count == 1

    # Record second visit - should increment visit frequency
    view_again = ProfileViewService.record_view(
        db, viewed_user_id=user2.id, viewer_id=user1.id
    )
    assert view_again.id == view.id
    assert view_again.visit_count == 2


def test_ignore_self_profile_view(db):
    user1 = create_test_user(db, "pvself@example.com", "pvself")

    view = ProfileViewService.record_view(
        db, viewed_user_id=user1.id, viewer_id=user1.id
    )
    assert view is None


def test_paginated_profile_views_with_privacy_and_frequency(db):
    host = create_test_user(db, "host@example.com", "host")
    visitor1 = create_test_user(db, "v1@example.com", "v1")
    visitor2 = create_test_user(db, "v2@example.com", "v2")

    # Visitor 1 visits twice normally
    ProfileViewService.record_view(db, viewed_user_id=host.id, viewer_id=visitor1.id)
    ProfileViewService.record_view(db, viewed_user_id=host.id, viewer_id=visitor1.id)

    # Visitor 2 visits anonymously
    ProfileViewService.record_view(
        db, viewed_user_id=host.id, viewer_id=visitor2.id, is_anonymous_override=True
    )

    history = ProfileViewService.get_profile_views(db, user_id=host.id, page=1, size=10)
    assert history.total == 2
    assert len(history.items) == 2

    v1_item = next(i for i in history.items if not i.is_anonymous)
    assert v1_item.viewer_username == "v1"
    assert v1_item.visit_count == 2

    anon_item = next(i for i in history.items if i.is_anonymous)
    assert anon_item.viewer_name == "Anonymous Developer"
    assert anon_item.viewer_id is None
    assert anon_item.visit_count == 1


def test_profile_views_http_endpoints(client: TestClient, db, register_and_login):
    host_id, host_token = register_and_login("target@example.com", "targetuser")
    visitor_id, visitor_token = register_and_login("visitor@example.com", "visitoruser")

    # Record view via HTTP
    response = client.post(
        f"/api/profile-views/{host_id}",
        headers={"Authorization": f"Bearer {visitor_token}"},
    )
    assert response.status_code == 201

    # Privacy toggle via HTTP
    privacy_res = client.put(
        "/api/profile-views/privacy",
        json={"hide_profile_views": True},
        headers={"Authorization": f"Bearer {visitor_token}"},
    )
    assert privacy_res.status_code == 200
    assert privacy_res.json()["hide_profile_views"] is True

    # History endpoint - non-premium should be 403 Forbidden
    history_res = client.get(
        "/api/profile-views/history",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert history_res.status_code == 403

    # Upgrade host to premium
    host_user = db.get(User, uuid.UUID(str(host_id)))
    host_user.premium = True
    db.commit()

    # History endpoint - premium should be 200 OK
    history_res_premium = client.get(
        "/api/profile-views/history",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert history_res_premium.status_code == 200
    assert history_res_premium.json()["total"] == 1
