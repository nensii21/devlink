"""
Tests for issue #1399: post likes and comments.

`Post` carried `likes_count` and `comments_count` and nothing else, so the
engagement endpoints were counter arithmetic:

  * `POST /like` incremented, without asking who was asking, so one account
    could like a post a hundred times;
  * `DELETE /like` decremented, without asking whether the caller had ever
    liked it, so anyone could walk a post's count to zero;
  * `POST /comment` validated the body, incremented `comments_count`, and
    dropped the text.

Most of what follows is the negative space of that: liking twice, unliking
something you never liked, and reading back a comment that used to go
nowhere.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.post_comment import PostComment
from app.models.post_like import PostLike

pytestmark = pytest.mark.usefixtures("setup_db")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_post(client: TestClient, token: str, content: str = "hello feed") -> str:
    response = client.post(
        "/api/posts/",
        json={"content": content, "status": "published"},
        headers=_auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.fixture
def author(register_and_login):
    return register_and_login("author@example.com", "post_author")


@pytest.fixture
def reader(register_and_login):
    return register_and_login("reader@example.com", "post_reader")


@pytest.fixture
def third(register_and_login):
    return register_and_login("third@example.com", "post_third")


# --------------------------------------------------------------------------
# Liking is idempotent
# --------------------------------------------------------------------------


def test_a_like_is_recorded_against_the_user(client, author, db: Session):
    _, token = author
    post_id = _create_post(client, token)

    response = client.post(f"/api/posts/{post_id}/like", headers=_auth(token))
    assert response.status_code == 200
    body = response.json()
    assert body["likes"] == 1
    assert body["liked_by_me"] is True
    assert body["changed"] is True

    assert db.query(PostLike).count() == 1


def test_liking_twice_leaves_one_like(client, author):
    """
    The bug in one assertion. `likes_count += 1` with no record of who liked
    meant N calls were N likes from one account.
    """
    _, token = author
    post_id = _create_post(client, token)

    first = client.post(f"/api/posts/{post_id}/like", headers=_auth(token)).json()
    second = client.post(f"/api/posts/{post_id}/like", headers=_auth(token)).json()

    assert first["likes"] == 1
    assert second["likes"] == 1
    assert first["changed"] is True
    # A repeat is a success that changed nothing, not an error.
    assert second["changed"] is False
    assert second["liked_by_me"] is True


def test_ten_likes_from_one_account_are_still_one_like(client, author):
    _, token = author
    post_id = _create_post(client, token)

    for _ in range(10):
        response = client.post(f"/api/posts/{post_id}/like", headers=_auth(token))
        assert response.status_code == 200

    assert response.json()["likes"] == 1


def test_likes_from_different_users_accumulate(client, author, reader, third):
    _, author_token = author
    _, reader_token = reader
    _, third_token = third
    post_id = _create_post(client, author_token)

    client.post(f"/api/posts/{post_id}/like", headers=_auth(author_token))
    client.post(f"/api/posts/{post_id}/like", headers=_auth(reader_token))
    final = client.post(f"/api/posts/{post_id}/like", headers=_auth(third_token))

    assert final.json()["likes"] == 3


def test_liking_a_missing_post_is_404(client, author):
    _, token = author
    missing = "00000000-0000-0000-0000-000000000000"
    response = client.post(f"/api/posts/{missing}/like", headers=_auth(token))
    assert response.status_code == 404


def test_liking_requires_authentication(client, author):
    _, token = author
    post_id = _create_post(client, token)
    assert client.post(f"/api/posts/{post_id}/like").status_code in (401, 403)


# --------------------------------------------------------------------------
# Unliking only removes your own like
# --------------------------------------------------------------------------


def test_unlike_removes_the_callers_like(client, author):
    _, token = author
    post_id = _create_post(client, token)
    client.post(f"/api/posts/{post_id}/like", headers=_auth(token))

    response = client.delete(f"/api/posts/{post_id}/like", headers=_auth(token))
    body = response.json()

    assert body["likes"] == 0
    assert body["liked_by_me"] is False
    assert body["changed"] is True


def test_unliking_without_a_like_changes_nothing(client, author, reader):
    """
    The old handler did `max(0, likes_count - 1)` unconditionally, so any
    authenticated user could take a post's count down one call at a time.
    """
    _, author_token = author
    _, reader_token = reader
    post_id = _create_post(client, author_token)
    client.post(f"/api/posts/{post_id}/like", headers=_auth(author_token))

    response = client.delete(f"/api/posts/{post_id}/like", headers=_auth(reader_token))
    body = response.json()

    assert body["likes"] == 1
    assert body["changed"] is False


def test_a_stranger_cannot_drive_the_count_to_zero(client, author, reader, third):
    _, author_token = author
    _, reader_token = reader
    _, third_token = third
    post_id = _create_post(client, author_token)

    client.post(f"/api/posts/{post_id}/like", headers=_auth(author_token))
    client.post(f"/api/posts/{post_id}/like", headers=_auth(reader_token))

    for _ in range(5):
        client.delete(f"/api/posts/{post_id}/like", headers=_auth(third_token))

    listing = client.get("/api/posts/").json()
    assert listing[0]["likes"] == 2


def test_like_then_unlike_then_like_settles_at_one(client, author):
    _, token = author
    post_id = _create_post(client, token)

    client.post(f"/api/posts/{post_id}/like", headers=_auth(token))
    client.delete(f"/api/posts/{post_id}/like", headers=_auth(token))
    final = client.post(f"/api/posts/{post_id}/like", headers=_auth(token))

    assert final.json()["likes"] == 1
    assert final.json()["liked_by_me"] is True


# --------------------------------------------------------------------------
# liked_by_me on listings
# --------------------------------------------------------------------------


def test_listing_reports_liked_by_me_for_the_caller(client, author, reader):
    _, author_token = author
    _, reader_token = reader
    post_id = _create_post(client, author_token)
    client.post(f"/api/posts/{post_id}/like", headers=_auth(author_token))

    as_author = client.get("/api/posts/", headers=_auth(author_token)).json()
    as_reader = client.get("/api/posts/", headers=_auth(reader_token)).json()

    assert as_author[0]["liked_by_me"] is True
    assert as_reader[0]["liked_by_me"] is False
    # Both see the same count; only the personal flag differs.
    assert as_author[0]["likes"] == as_reader[0]["likes"] == 1


def test_anonymous_listing_reports_liked_by_me_false(client, author):
    _, token = author
    post_id = _create_post(client, token)
    client.post(f"/api/posts/{post_id}/like", headers=_auth(token))

    anonymous = client.get("/api/posts/").json()
    assert anonymous[0]["liked_by_me"] is False
    assert anonymous[0]["likes"] == 1


def test_drafts_listing_reports_liked_by_me(client, author):
    _, token = author
    response = client.post(
        "/api/posts/",
        json={"content": "draft", "status": "draft"},
        headers=_auth(token),
    )
    post_id = response.json()["id"]
    client.post(f"/api/posts/{post_id}/like", headers=_auth(token))

    drafts = client.get("/api/posts/drafts", headers=_auth(token)).json()
    assert drafts[0]["liked_by_me"] is True


# --------------------------------------------------------------------------
# Comments are stored
# --------------------------------------------------------------------------


def test_a_comment_is_stored_and_returned(client, author, db: Session):
    """
    The body used to be validated and dropped: only the counter moved.
    """
    _, token = author
    post_id = _create_post(client, token)

    response = client.post(
        f"/api/posts/{post_id}/comment",
        json={"comment": "this is the comment body"},
        headers=_auth(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["content"] == "this is the comment body"
    assert body["post_id"] == post_id
    assert body["author"]["handle"] == "post_author"

    assert db.query(PostComment).count() == 1
    assert db.query(PostComment).one().content == "this is the comment body"


def test_comments_can_be_read_back(client, author, reader):
    _, author_token = author
    _, reader_token = reader
    post_id = _create_post(client, author_token)

    client.post(
        f"/api/posts/{post_id}/comment",
        json={"comment": "first"},
        headers=_auth(author_token),
    )
    client.post(
        f"/api/posts/{post_id}/comment",
        json={"comment": "second"},
        headers=_auth(reader_token),
    )

    comments = client.get(f"/api/posts/{post_id}/comments").json()
    assert [c["content"] for c in comments] == ["first", "second"]
    assert comments[1]["author"]["handle"] == "post_reader"


def test_comment_count_matches_the_stored_comments(client, author):
    _, token = author
    post_id = _create_post(client, token)

    for i in range(3):
        client.post(
            f"/api/posts/{post_id}/comment",
            json={"comment": f"comment {i}"},
            headers=_auth(token),
        )

    listing = client.get("/api/posts/").json()
    assert listing[0]["comments"] == 3
    assert len(client.get(f"/api/posts/{post_id}/comments").json()) == 3


@pytest.mark.parametrize("body", ["", "   ", "\n\t "])
def test_blank_comments_are_rejected(client, author, body):
    _, token = author
    post_id = _create_post(client, token)

    response = client.post(
        f"/api/posts/{post_id}/comment",
        json={"comment": body},
        headers=_auth(token),
    )
    assert response.status_code == 422


def test_overlong_comments_are_rejected(client, author):
    _, token = author
    post_id = _create_post(client, token)

    response = client.post(
        f"/api/posts/{post_id}/comment",
        json={"comment": "x" * 2001},
        headers=_auth(token),
    )
    assert response.status_code == 422


def test_commenting_on_a_missing_post_is_404(client, author):
    _, token = author
    missing = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/api/posts/{missing}/comment",
        json={"comment": "hi"},
        headers=_auth(token),
    )
    assert response.status_code == 404


# --------------------------------------------------------------------------
# Comment deletion
# --------------------------------------------------------------------------


def test_a_commenter_can_delete_their_own_comment(client, author, reader):
    _, author_token = author
    _, reader_token = reader
    post_id = _create_post(client, author_token)

    comment_id = client.post(
        f"/api/posts/{post_id}/comment",
        json={"comment": "mine"},
        headers=_auth(reader_token),
    ).json()["id"]

    response = client.delete(
        f"/api/posts/{post_id}/comment/{comment_id}", headers=_auth(reader_token)
    )
    assert response.status_code == 204
    assert client.get(f"/api/posts/{post_id}/comments").json() == []


def test_the_post_author_can_delete_a_comment_on_their_post(client, author, reader):
    _, author_token = author
    _, reader_token = reader
    post_id = _create_post(client, author_token)

    comment_id = client.post(
        f"/api/posts/{post_id}/comment",
        json={"comment": "someone else's"},
        headers=_auth(reader_token),
    ).json()["id"]

    response = client.delete(
        f"/api/posts/{post_id}/comment/{comment_id}", headers=_auth(author_token)
    )
    assert response.status_code == 204


def test_a_third_party_cannot_delete_a_comment(client, author, reader, third):
    _, author_token = author
    _, reader_token = reader
    _, third_token = third
    post_id = _create_post(client, author_token)

    comment_id = client.post(
        f"/api/posts/{post_id}/comment",
        json={"comment": "not yours"},
        headers=_auth(reader_token),
    ).json()["id"]

    response = client.delete(
        f"/api/posts/{post_id}/comment/{comment_id}", headers=_auth(third_token)
    )
    assert response.status_code == 403


def test_deleting_a_comment_updates_the_count(client, author):
    _, token = author
    post_id = _create_post(client, token)

    comment_id = client.post(
        f"/api/posts/{post_id}/comment",
        json={"comment": "one"},
        headers=_auth(token),
    ).json()["id"]

    client.delete(f"/api/posts/{post_id}/comment/{comment_id}", headers=_auth(token))

    assert client.get("/api/posts/").json()[0]["comments"] == 0


# --------------------------------------------------------------------------
# Cascades
# --------------------------------------------------------------------------


def test_deleting_a_post_removes_its_likes_and_comments(
    client, author, reader, db: Session
):
    _, author_token = author
    _, reader_token = reader
    post_id = _create_post(client, author_token)

    client.post(f"/api/posts/{post_id}/like", headers=_auth(reader_token))
    client.post(
        f"/api/posts/{post_id}/comment",
        json={"comment": "bye"},
        headers=_auth(reader_token),
    )

    assert client.delete(f"/api/posts/{post_id}", headers=_auth(author_token)).status_code == 204

    assert db.query(PostLike).count() == 0
    assert db.query(PostComment).count() == 0


# --------------------------------------------------------------------------
# Status validation and the draft trap
# --------------------------------------------------------------------------


@pytest.mark.parametrize("bad", ["Published", "archived", "", "deleted"])
def test_unknown_status_values_are_rejected(client, author, bad):
    """
    `status` was a bare `str` on a `String(20)` column, so any string was
    writable -- and a status nothing filters on makes the post invisible
    everywhere rather than rejected at the door.
    """
    _, token = author
    response = client.post(
        "/api/posts/", json={"content": "x", "status": bad}, headers=_auth(token)
    )
    assert response.status_code == 422


def test_a_draft_with_a_publish_date_stays_a_draft(client, author):
    """
    The old handler recomputed status from `publish_at` unconditionally, so
    scheduling a draft published it instead.
    """
    _, token = author
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    response = client.post(
        "/api/posts/",
        json={"content": "still a draft", "status": "draft", "publish_at": past},
        headers=_auth(token),
    )

    assert response.status_code == 201
    assert response.json()["status"] == "draft"
    assert client.get("/api/posts/").json() == []


def test_a_published_post_can_be_returned_to_draft(client, author):
    """
    Once `publish_at` was set, `{"status": "draft"}` was overwritten on the
    next line, so a post could never be unpublished.
    """
    _, token = author
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    post_id = client.post(
        "/api/posts/",
        json={"content": "scheduled", "publish_at": future},
        headers=_auth(token),
    ).json()["id"]

    response = client.put(
        f"/api/posts/{post_id}", json={"status": "draft"}, headers=_auth(token)
    )

    assert response.status_code == 200
    assert response.json()["status"] == "draft"


def test_blank_content_is_rejected(client, author):
    _, token = author
    response = client.post(
        "/api/posts/", json={"content": "   "}, headers=_auth(token)
    )
    assert response.status_code == 422


def test_tags_are_deduplicated_and_stripped(client, author):
    _, token = author
    response = client.post(
        "/api/posts/",
        json={"content": "x", "tags": [" python ", "python", "", "fastapi"]},
        headers=_auth(token),
    )
    assert response.json()["tags"] == ["python", "fastapi"]


def test_too_many_tags_are_rejected(client, author):
    _, token = author
    response = client.post(
        "/api/posts/",
        json={"content": "x", "tags": [f"t{i}" for i in range(11)]},
        headers=_auth(token),
    )
    assert response.status_code == 422


# --------------------------------------------------------------------------
# Pagination
# --------------------------------------------------------------------------


def test_the_feed_is_paginated(client, author, db: Session):
    """
    `list_posts` used to end in `.all()`, so the response was every published
    post in the table -- and that response was then cached.
    """
    _, token = author
    for i in range(25):
        _create_post(client, token, content=f"post {i}")

    first_page = client.get("/api/posts/", params={"limit": 10}).json()
    second_page = client.get("/api/posts/", params={"limit": 10, "page": 2}).json()

    assert len(first_page) == 10
    assert len(second_page) == 10
    assert {p["id"] for p in first_page}.isdisjoint({p["id"] for p in second_page})


def test_default_page_size_is_bounded(client, author):
    _, token = author
    for i in range(25):
        _create_post(client, token, content=f"post {i}")

    assert len(client.get("/api/posts/").json()) == 20


def test_page_size_above_the_maximum_is_rejected(client):
    assert client.get("/api/posts/", params={"limit": 500}).status_code == 422


def test_page_below_one_is_rejected(client):
    assert client.get("/api/posts/", params={"page": 0}).status_code == 422
