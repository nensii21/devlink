"""
One follow, one notification, and a duplicate that does not take the request
with it (#1317).

Two faults lived in this flow. `FollowerService.follow_user` sent a
notification and then the router sent a second one of its own -- same event,
different title, different link, two rows in the recipient's list. And
`follow_user` inserted unconditionally, so a duplicate raised `IntegrityError`
from the unique constraint with nothing to catch it; the `Session` went into a
rolled-back state and every later statement in the request failed with
`PendingRollbackError`, including ones with nothing to do with following
anybody.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.follower import Follower
from app.models.user import User
from app.services.follower_service import FollowerService
from app.services.notification_service import NotificationService


def _user(db, username: str) -> User:
    user = User(
        first_name=username.capitalize(),
        last_name="User",
        username=username,
        email=f"{username}@example.com",
        password_hash="hashed",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def enqueued(monkeypatch) -> list[dict]:
    """
    Record every notification handed to `NotificationService.enqueue`.

    Counted at the enqueue rather than by reading rows back, because the fault
    is at the enqueue -- the service sent one and the router sent another. It
    also keeps these tests off the dispatch path, which reaches for Celery,
    falls back to running the task inline against `SessionLocal`, and is
    therefore sensitive to whatever the previous test in the session did to
    that engine.
    """
    calls: list[dict] = []

    def record(db, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(NotificationService, "enqueue", staticmethod(record))
    return calls


def _relationships(
    db, follower_id: uuid.UUID, following_id: uuid.UUID
) -> list[Follower]:
    return list(
        db.scalars(
            select(Follower).where(
                Follower.follower_id == follower_id,
                Follower.following_id == following_id,
            )
        )
    )


# ---------------------------------------------------------------------------
# One follow, one notification
# ---------------------------------------------------------------------------


def test_a_follow_notifies_once(db, enqueued):
    alice = _user(db, "alice")
    bob = _user(db, "bob")

    FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)

    assert len(enqueued) == 1
    assert enqueued[0]["recipient_id"] == bob.id
    assert enqueued[0]["sender_id"] == alice.id


def test_the_notification_carries_the_service_wording(db, enqueued):
    """
    The router's copy said "New follower" and linked to `/users/<uuid>`; the
    service says "New Follower" and links to the profile. Two spellings of the
    same event is how you notice there are two of them.
    """
    alice = _user(db, "alice")
    bob = _user(db, "bob")

    FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)

    assert enqueued[0]["title"] == "New Follower"
    assert enqueued[0]["action_url"] == "/profile/alice"


def test_following_over_the_api_notifies_once(client, register_and_login, enqueued):
    """
    The end the bug was reported from. The router used to add its own enqueue
    on the line after the service call, so this was 2.
    """
    _, alice_token = register_and_login("alice@example.com", "alice")
    bob_id, _ = register_and_login("bob@example.com", "bob")

    response = client.post(
        f"/api/followers/{bob_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )

    assert response.status_code == 201
    assert len(enqueued) == 1
    assert enqueued[0]["recipient_id"] == uuid.UUID(bob_id)


# ---------------------------------------------------------------------------
# Duplicates
# ---------------------------------------------------------------------------


def test_following_twice_creates_one_relationship(db):
    alice = _user(db, "alice")
    bob = _user(db, "bob")

    first = FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)
    second = FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)
    db.commit()

    assert first.id == second.id
    assert len(_relationships(db, alice.id, bob.id)) == 1


def test_following_twice_notifies_once(db, enqueued):
    alice = _user(db, "alice")
    bob = _user(db, "bob")

    FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)
    FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)

    assert len(enqueued) == 1


def test_following_twice_leaves_the_session_usable(db):
    """
    The `PendingRollbackError` this pins is raised by the *next* statement, not
    the failing one -- which is why the symptom was a 500 from somewhere else
    entirely.
    """
    alice = _user(db, "alice")
    bob = _user(db, "bob")

    FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)
    FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)

    assert FollowerService.follower_count(db, user_id=bob.id) == 1
    assert db.get(User, alice.id) is not None


def test_losing_the_insert_race_returns_the_winning_row(db, monkeypatch, enqueued):
    """
    The router's `SELECT` before the insert is check-then-act, and so is the
    one inside `follow_user`. Two concurrent requests both pass it; one of them
    hits the unique constraint.

    Simulated by making the existence check answer "no" while the row is there,
    which is exactly what the losing request sees.
    """
    alice = _user(db, "alice")
    bob = _user(db, "bob")

    winner = Follower(follower_id=alice.id, following_id=bob.id)
    db.add(winner)
    db.commit()
    db.refresh(winner)

    real_get_relationship = FollowerService.get_relationship
    calls = {"n": 0}

    def blind_once(session, follower_id, following_id):
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return real_get_relationship(session, follower_id, following_id)

    monkeypatch.setattr(FollowerService, "get_relationship", staticmethod(blind_once))

    result = FollowerService.follow_user(db, follower_id=alice.id, following_id=bob.id)

    assert result.id == winner.id
    assert len(_relationships(db, alice.id, bob.id)) == 1
    assert enqueued == []
    # And the session is still good afterwards, which is the whole point.
    assert FollowerService.follower_count(db, user_id=bob.id) == 1


def test_an_integrity_error_that_is_not_a_duplicate_still_propagates(db, monkeypatch):
    """
    The `except IntegrityError` is for one specific collision. A dangling
    foreign key is a different problem and swallowing it would hide it.
    """
    alice = _user(db, "alice")

    monkeypatch.setattr(
        FollowerService, "get_relationship", staticmethod(lambda *a, **k: None)
    )

    with pytest.raises(IntegrityError):
        FollowerService.follow_user(db, follower_id=alice.id, following_id=uuid.uuid4())
