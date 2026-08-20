"""Conversation membership is enforced on every /messages route (issue #1234).

Three routes -- list, count and per-conversation search -- were reachable with
no `Authorization` header at all, because the router declared no dependency and
those handlers took no `current_user`. The rest authenticated the caller and
then never asked whether that caller belonged to the conversation they were
addressing, so a conversation id was the only thing standing between a
stranger and a private thread.

Each route is checked three ways: anonymous, authenticated-but-not-a-member,
and member. The third matters as much as the first two -- an authorization fix
that quietly breaks the people who *are* allowed in is not a fix.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationType
from app.models.conversation_member import ConversationMember


@pytest.fixture
def private_thread(db: Session, register_and_login) -> dict:
    """Alice and Bob in a conversation; Eve registered but outside it."""
    alice_id, alice_token = register_and_login("authz.alice@example.com", "authzalice")
    bob_id, bob_token = register_and_login("authz.bob@example.com", "authzbob")
    eve_id, eve_token = register_and_login("authz.eve@example.com", "authzeve")

    conversation = Conversation(
        title="Offer discussion",
        type=ConversationType.DIRECT,
        created_by=uuid.UUID(alice_id),
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    db.add(
        ConversationMember(
            conversation_id=conversation.id, user_id=uuid.UUID(alice_id)
        )
    )
    db.add(
        ConversationMember(conversation_id=conversation.id, user_id=uuid.UUID(bob_id))
    )
    db.commit()

    return {
        "conversation_id": conversation.id,
        "alice_id": alice_id,
        "alice": {"Authorization": f"Bearer {alice_token}"},
        "bob_id": bob_id,
        "bob": {"Authorization": f"Bearer {bob_token}"},
        "eve_id": eve_id,
        "eve": {"Authorization": f"Bearer {eve_token}"},
    }


@pytest.fixture
def thread_with_message(client: TestClient, private_thread: dict) -> dict:
    """The same thread, with one message from Alice in it."""
    response = client.post(
        "/api/messages/",
        json={
            "conversation_id": str(private_thread["conversation_id"]),
            "content": "The offer is 250k, keep it between us",
        },
        headers=private_thread["alice"],
    )
    assert response.status_code == 201, response.text

    return {**private_thread, "message_id": response.json()["id"]}


SECRET = "250k"


def _conversation_routes(conversation_id) -> list[tuple[str, str, dict | None]]:
    """(method, path, json body) for every conversation-scoped route."""
    cid = str(conversation_id)
    return [
        ("GET", f"/api/messages/conversation/{cid}", None),
        ("GET", f"/api/messages/conversation/{cid}/count", None),
        ("GET", f"/api/messages/conversation/{cid}/pinned", None),
        ("GET", f"/api/messages/search/{cid}?keyword=offer", None),
        ("GET", f"/api/messages/conversation/{cid}/typing", None),
        ("POST", f"/api/messages/conversation/{cid}/typing", None),
        ("DELETE", f"/api/messages/conversation/{cid}/typing", None),
        ("POST", f"/api/messages/conversation/{cid}/read", None),
    ]


def _call(client: TestClient, method: str, path: str, body, headers):
    return client.request(method, path, json=body, headers=headers)


# ------------------------------------------------------------------
# Anonymous callers
# ------------------------------------------------------------------


@pytest.mark.parametrize(
    "method,path_template",
    [
        ("GET", "/api/messages/conversation/{cid}"),
        ("GET", "/api/messages/conversation/{cid}/count"),
        ("GET", "/api/messages/search/{cid}?keyword=offer"),
    ],
)
def test_unauthenticated_read_routes_are_closed(
    client: TestClient, thread_with_message: dict, method: str, path_template: str
) -> None:
    """The three routes that used to answer 200 with no credentials.

    This is the core of the report: `curl` with no header returned message
    bodies. Anything other than a 2xx is a pass here, but the body is checked
    too -- a handler that 500s *after* serialising the messages would still be
    a leak.
    """
    path = path_template.format(cid=thread_with_message["conversation_id"])

    response = _call(client, method, path, None, headers=None)

    assert response.status_code in (401, 403), (
        f"{method} {path} answered {response.status_code} to an anonymous caller"
    )
    assert SECRET not in response.text


def test_anonymous_caller_cannot_send(
    client: TestClient, private_thread: dict
) -> None:
    response = client.post(
        "/api/messages/",
        json={
            "conversation_id": str(private_thread["conversation_id"]),
            "content": "anyone home",
        },
    )

    assert response.status_code in (401, 403)


# ------------------------------------------------------------------
# Authenticated non-members
# ------------------------------------------------------------------


def test_non_member_is_refused_every_conversation_route(
    client: TestClient, thread_with_message: dict
) -> None:
    """Eve is a real user with a real token, and still gets nothing."""
    refused = []

    for method, path, body in _conversation_routes(
        thread_with_message["conversation_id"]
    ):
        response = _call(client, method, path, body, thread_with_message["eve"])
        refused.append((method, path, response.status_code))

        assert response.status_code == 403, (
            f"{method} {path} answered {response.status_code} to a non-member"
        )
        assert SECRET not in response.text

    assert len(refused) == 8, "route list drifted; update the test"


def test_non_member_cannot_send_into_the_conversation(
    client: TestClient, private_thread: dict
) -> None:
    """The send route reads the conversation id out of the body.

    `require_conversation_member` cannot see it there, so this is the case a
    path-parameter dependency would have missed.
    """
    response = client.post(
        "/api/messages/",
        json={
            "conversation_id": str(private_thread["conversation_id"]),
            "content": "eve was here",
        },
        headers=private_thread["eve"],
    )

    assert response.status_code == 403


def test_non_member_cannot_read_a_single_message(
    client: TestClient, thread_with_message: dict
) -> None:
    response = client.get(
        f"/api/messages/{thread_with_message['message_id']}",
        headers=thread_with_message["eve"],
    )

    assert response.status_code == 403
    assert SECRET not in response.text


def test_non_member_cannot_pin_or_unpin(
    client: TestClient, thread_with_message: dict
) -> None:
    """Pinning is a write into someone else's thread.

    It also surfaces in the conversation for everyone in it, so this was a way
    to put content in front of people who never accepted anything from you.
    """
    message_id = thread_with_message["message_id"]

    pin = client.patch(
        f"/api/messages/{message_id}/pin", headers=thread_with_message["eve"]
    )
    unpin = client.patch(
        f"/api/messages/{message_id}/unpin", headers=thread_with_message["eve"]
    )

    assert pin.status_code == 403
    assert unpin.status_code == 403


def test_non_member_cannot_mark_messages_read_or_delivered(
    client: TestClient, thread_with_message: dict
) -> None:
    """Read state is visible to the sender, so writing it is not harmless."""
    message_id = thread_with_message["message_id"]
    eve = thread_with_message["eve"]
    cid = str(thread_with_message["conversation_id"])

    assert client.patch(f"/api/messages/{message_id}/read", headers=eve).status_code == 403
    assert (
        client.post(f"/api/messages/{message_id}/deliver", headers=eve).status_code
        == 403
    )
    assert (
        client.post(
            "/api/messages/read/bulk", json={"conversation_id": cid}, headers=eve
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/messages/bulk-deliver", json={"conversation_id": cid}, headers=eve
        ).status_code
        == 403
    )


def test_bulk_read_by_message_id_ignores_foreign_messages(
    client: TestClient, thread_with_message: dict
) -> None:
    """The by-id bulk path is scoped, not refused.

    A caller may legitimately pass ids spanning several of their own
    conversations, so the service filters to conversations they belong to
    rather than rejecting the whole request. Nothing outside is touched.
    """
    response = client.post(
        "/api/messages/read/bulk",
        json={"message_ids": [thread_with_message["message_id"]]},
        headers=thread_with_message["eve"],
    )

    assert response.status_code == 200
    assert response.json()["updated_count"] == 0


def test_non_member_cannot_edit_or_delete(
    client: TestClient, thread_with_message: dict
) -> None:
    message_id = thread_with_message["message_id"]
    eve = thread_with_message["eve"]

    assert (
        client.put(
            f"/api/messages/{message_id}", json={"content": "edited"}, headers=eve
        ).status_code
        == 403
    )
    assert client.delete(f"/api/messages/{message_id}", headers=eve).status_code == 403


def test_global_search_does_not_reach_foreign_conversations(
    client: TestClient, thread_with_message: dict
) -> None:
    """The cross-conversation search was already scoped; keep it that way."""
    response = client.get(
        "/api/messages/search?q=offer", headers=thread_with_message["eve"]
    )

    assert response.status_code == 200
    assert response.json() == []


# ------------------------------------------------------------------
# Members still get through
# ------------------------------------------------------------------


def test_member_can_use_every_conversation_route(
    client: TestClient, thread_with_message: dict
) -> None:
    """Bob is in the conversation and nothing above gets in his way."""
    for method, path, body in _conversation_routes(
        thread_with_message["conversation_id"]
    ):
        response = _call(client, method, path, body, thread_with_message["bob"])

        assert response.status_code < 400, (
            f"{method} {path} refused a member with {response.status_code}: "
            f"{response.text[:200]}"
        )


def test_member_can_read_send_and_pin(
    client: TestClient, thread_with_message: dict
) -> None:
    cid = str(thread_with_message["conversation_id"])
    bob = thread_with_message["bob"]

    listing = client.get(f"/api/messages/conversation/{cid}", headers=bob)
    assert listing.status_code == 200
    assert SECRET in listing.text

    sent = client.post(
        "/api/messages/",
        json={"conversation_id": cid, "content": "understood"},
        headers=bob,
    )
    assert sent.status_code == 201

    pin = client.patch(
        f"/api/messages/{thread_with_message['message_id']}/pin", headers=bob
    )
    assert pin.status_code == 200
    assert pin.json()["is_pinned"] is True


def test_author_can_still_edit_and_delete_their_own_message(
    client: TestClient, thread_with_message: dict
) -> None:
    message_id = thread_with_message["message_id"]
    alice = thread_with_message["alice"]

    edited = client.put(
        f"/api/messages/{message_id}", json={"content": "revised"}, headers=alice
    )
    assert edited.status_code == 200

    deleted = client.delete(f"/api/messages/{message_id}", headers=alice)
    assert deleted.status_code in (200, 204)


def test_member_cannot_edit_another_members_message(
    client: TestClient, thread_with_message: dict
) -> None:
    """Membership is not authorship.

    Bob belongs to the conversation, so he passes the new check and then has
    to fail the older ownership one. Both are load-bearing.
    """
    response = client.put(
        f"/api/messages/{thread_with_message['message_id']}",
        json={"content": "not mine to edit"},
        headers=thread_with_message["bob"],
    )

    assert response.status_code == 403


def test_removed_member_loses_access_to_their_own_messages(
    client: TestClient, db: Session, thread_with_message: dict
) -> None:
    """Authorship outlives membership, and must not outlive access.

    `sender_id` still points at Alice after she leaves, so an ownership-only
    check would have let her keep editing and deleting inside a thread she is
    no longer part of.
    """
    membership = (
        db.query(ConversationMember)
        .filter(
            ConversationMember.conversation_id == thread_with_message["conversation_id"],
            ConversationMember.user_id == uuid.UUID(thread_with_message["alice_id"]),
        )
        .one()
    )
    db.delete(membership)
    db.commit()

    message_id = thread_with_message["message_id"]
    alice = thread_with_message["alice"]

    assert client.get(f"/api/messages/{message_id}", headers=alice).status_code == 403
    assert (
        client.put(
            f"/api/messages/{message_id}", json={"content": "still mine"}, headers=alice
        ).status_code
        == 403
    )
    assert client.delete(f"/api/messages/{message_id}", headers=alice).status_code == 403


def test_unknown_conversation_is_refused_not_leaked(
    client: TestClient, private_thread: dict
) -> None:
    """A conversation that does not exist looks the same as one you are not in."""
    response = client.get(
        f"/api/messages/conversation/{uuid.uuid4()}", headers=private_thread["eve"]
    )

    assert response.status_code == 403
