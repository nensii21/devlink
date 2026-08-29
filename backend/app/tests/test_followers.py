"""
Tests for the User Follow/Unfollow System (Issue #583).

Covers:
- Follow and unfollow users
- Prevent duplicate follows
- Prevent self-follows
- Real-time follower/following count updates
- is-following status check
- Mutual followers
"""

from fastapi.testclient import TestClient

from app.models.follower import Follower  # noqa: F401
from app.models.user import User
from app.services.follower_service import FollowerService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def create_user(db, email: str, username: str) -> User:
    user = User(
        first_name="Test",
        last_name="User",
        username=username,
        email=email,
        password_hash="secret_hashed",
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Service-level unit tests (no HTTP, faster feedback)
# ---------------------------------------------------------------------------


def test_follow_user_service(db):
    """FollowerService.follow_user creates a relationship."""
    alice = create_user(db, "alice@example.com", "alice")
    bob = create_user(db, "bob@example.com", "bob")

    follow = FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)

    assert follow is not None
    assert follow.follower_id == alice.id
    assert follow.following_id == bob.id


def test_prevent_duplicate_follow(db):
    """Following the same user twice does not create a duplicate row."""
    alice = create_user(db, "alice@example.com", "alice")
    bob = create_user(db, "bob@example.com", "bob")

    FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)

    # Second follow attempt – the service should either raise or return the
    # existing row; a duplicate row must NOT be created.
    try:
        FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)
    except Exception:
        pass  # It's acceptable to raise on duplicate

    count = FollowerService.follower_count(db, user_id=bob.id)
    assert count == 1, "Duplicate follow must not increase count beyond 1"


def test_unfollow_user_service(db):
    """FollowerService.unfollow_user removes the relationship."""
    alice = create_user(db, "alice@example.com", "alice")
    bob = create_user(db, "bob@example.com", "bob")

    FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)
    relationship = FollowerService.get_relationship(db, alice.id, bob.id)
    assert relationship is not None

    FollowerService.unfollow_user(db, relationship)

    relationship_after = FollowerService.get_relationship(db, alice.id, bob.id)
    assert relationship_after is None


def test_follower_and_following_count(db):
    """Counts increment on follow and decrement on unfollow."""
    alice = create_user(db, "alice@example.com", "alice")
    bob = create_user(db, "bob@example.com", "bob")
    carol = create_user(db, "carol@example.com", "carol")

    # alice follows bob and carol
    FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)
    FollowerService.follow_user(db, follower_id=alice.id, following_id=carol.id)
    # bob follows alice
    FollowerService.follow_user(db, follower_id=bob.id, following_id=alice.id)

    assert FollowerService.follower_count(db, bob.id) == 1
    assert FollowerService.following_count(db, alice.id) == 2
    assert FollowerService.follower_count(db, alice.id) == 1

    # alice unfollows bob
    rel = FollowerService.get_relationship(db, alice.id, bob.id)
    FollowerService.unfollow_user(db, rel)

    assert FollowerService.following_count(db, alice.id) == 1
    assert FollowerService.follower_count(db, bob.id) == 0


def test_is_following_service(db):
    """is_following returns correct boolean before and after follow."""
    alice = create_user(db, "alice@example.com", "alice")
    bob = create_user(db, "bob@example.com", "bob")

    assert FollowerService.is_following(db, alice.id, bob.id) is False

    FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)
    assert FollowerService.is_following(db, alice.id, bob.id) is True

    rel = FollowerService.get_relationship(db, alice.id, bob.id)
    FollowerService.unfollow_user(db, rel)
    assert FollowerService.is_following(db, alice.id, bob.id) is False


def test_mutual_followers_service(db):
    """mutual_followers returns users who follow each other."""
    alice = create_user(db, "alice@example.com", "alice")
    bob = create_user(db, "bob@example.com", "bob")
    carol = create_user(db, "carol@example.com", "carol")

    # alice ↔ bob (mutual)
    FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)
    FollowerService.follow_user(db, follower_id=bob.id, following_id=alice.id)
    # alice → carol (one-way only)
    FollowerService.follow_user(db, follower_id=alice.id, following_id=carol.id)

    mutuals = FollowerService.mutual_followers(db, alice.id, bob.id)
    # Alice and Bob are mutual followers of each other
    mutual_ids = {m.follower_id for m in mutuals} | {m.following_id for m in mutuals}
    assert alice.id in mutual_ids or bob.id in mutual_ids


# ---------------------------------------------------------------------------
# HTTP endpoint integration tests
# ---------------------------------------------------------------------------


def test_api_follow_user(client: TestClient, db, register_and_login):
    """POST /api/followers/{user_id} – happy path."""
    alice_id, alice_token = register_and_login("alice@example.com", "alice")
    bob_id, _ = register_and_login("bob@example.com", "bob")

    response = client.post(
        f"/api/followers/{bob_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 201


def test_api_cannot_follow_self(client: TestClient, db, register_and_login):
    """POST /api/followers/{own_id} must return 400."""
    alice_id, alice_token = register_and_login("alice@example.com", "alice")

    response = client.post(
        f"/api/followers/{alice_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 400
    assert "yourself" in response.json()["detail"].lower()


def test_api_prevent_duplicate_follow(client: TestClient, db, register_and_login):
    """Second follow of the same user returns 400."""
    alice_id, alice_token = register_and_login("alice@example.com", "alice")
    bob_id, _ = register_and_login("bob@example.com", "bob")

    client.post(
        f"/api/followers/{bob_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    response = client.post(
        f"/api/followers/{bob_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 400
    assert "already following" in response.json()["detail"].lower()


def test_api_unfollow_user(client: TestClient, db, register_and_login):
    """DELETE /api/followers/{user_id} – happy path."""
    alice_id, alice_token = register_and_login("alice@example.com", "alice")
    bob_id, _ = register_and_login("bob@example.com", "bob")

    client.post(
        f"/api/followers/{bob_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    response = client.delete(
        f"/api/followers/{bob_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 204


def test_api_unfollow_not_following(client: TestClient, db, register_and_login):
    """DELETE when not following returns 404."""
    alice_id, alice_token = register_and_login("alice@example.com", "alice")
    bob_id, _ = register_and_login("bob@example.com", "bob")

    response = client.delete(
        f"/api/followers/{bob_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 404


def test_api_follower_count_endpoint(client: TestClient, db, register_and_login):
    """GET /api/followers/{user_id}/count returns accurate count."""
    alice_id, alice_token = register_and_login("alice@example.com", "alice")
    bob_id, _ = register_and_login("bob@example.com", "bob")

    # Before follow
    r = client.get(f"/api/followers/{bob_id}/count")
    assert r.status_code == 200
    assert r.json()["count"] == 0

    # After follow
    client.post(
        f"/api/followers/{bob_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    r = client.get(f"/api/followers/{bob_id}/count")
    assert r.json()["count"] == 1


def test_api_is_following_endpoint(client: TestClient, db, register_and_login):
    """GET /api/followers/{user_id}/is-following reports status correctly."""
    alice_id, alice_token = register_and_login("alice@example.com", "alice")
    bob_id, _ = register_and_login("bob@example.com", "bob")

    r = client.get(
        f"/api/followers/{bob_id}/is-following",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r.status_code == 200
    assert r.json()["following"] is False

    client.post(
        f"/api/followers/{bob_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )

    r = client.get(
        f"/api/followers/{bob_id}/is-following",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r.json()["following"] is True


def test_api_follow_requires_auth(client: TestClient, db, register_and_login):
    """POST /api/followers/{user_id} without a token returns 401/403."""
    bob_id, _ = register_and_login("bob@example.com", "bob")

    response = client.post(f"/api/followers/{bob_id}")
    assert response.status_code in (401, 403)
