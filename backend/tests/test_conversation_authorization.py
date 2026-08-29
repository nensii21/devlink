"""
Authorization for the conversation routes.

Seven routes under `/api/conversations` took a `conversation_id` and no caller.
The worst of them was `POST /{id}/members/{user_id}`: membership is exactly the
predicate `app/routers/messages.py` checks before returning a thread, so an
open add-member route let anyone join a private conversation and then read all
of it through the correctly-guarded messages API.

The tests are organised as:

* `TestAnonymousAccess`      -- no token, every route
* `TestNonMemberAccess`      -- a token, but not in the conversation
* `TestPlainMemberAccess`    -- in the conversation, no role
* `TestAdminAccess`          -- promoted to admin
* `TestOwnerAccess`          -- created it
* `TestLeaving`              -- removing yourself
* `TestPrivateThreadIsNotReadable` -- the end-to-end exploit, blocked
* `TestGetDirectConversation`      -- the `or_` bug in the lookup

Status codes are deliberate and asserted as such: a non-member gets 404 so the
routes cannot be used to confirm that a conversation id is real; a member
without the role gets 403.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.models.conversation import Conversation, ConversationType
from app.models.conversation_member import ConversationMember, ConversationRole
from app.models.user import User
from app.schemas.conversation import ConversationCreate
from app.services.conversation_service import ConversationService

PASSWORD = "Vermilion-Kestrel97!"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _account(register_and_login, email: str, username: str) -> dict:
    uid, token = register_and_login(email, username)
    return {
        "id": uid,
        "uuid": uuid.UUID(uid),
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def owner(register_and_login):
    return _account(register_and_login, "owner@example.com", "convowner")


@pytest.fixture
def insider(register_and_login):
    """A plain member of the conversation."""
    return _account(register_and_login, "insider@example.com", "convinsider")


@pytest.fixture
def outsider(register_and_login):
    """Authenticated, but has nothing to do with the conversation."""
    return _account(register_and_login, "outsider@example.com", "convoutsider")


@pytest.fixture
def conversation(client: TestClient, owner, insider, db):
    """A group conversation with an owner and one plain member."""
    created = client.post(
        "/api/conversations/",
        json={"type": "group", "title": "Roadmap"},
        headers=owner["headers"],
    )
    assert created.status_code == 201, created.text
    conv_id = created.json()["id"]

    db.add(
        ConversationMember(
            conversation_id=uuid.UUID(conv_id),
            user_id=insider["uuid"],
            role=ConversationRole.MEMBER,
        )
    )
    db.commit()
    return conv_id


def _promote(db, conv_id: str, user_uuid: uuid.UUID, role: ConversationRole) -> None:
    member = (
        db.query(ConversationMember)
        .filter(
            ConversationMember.conversation_id == uuid.UUID(conv_id),
            ConversationMember.user_id == user_uuid,
        )
        .one()
    )
    member.role = role
    db.add(member)
    db.commit()


def _all_routes(conv_id: str, target_id: str) -> list[tuple[str, str]]:
    """(method, path) for every route that names a conversation."""
    return [
        ("GET", f"/api/conversations/{conv_id}"),
        ("PUT", f"/api/conversations/{conv_id}"),
        ("POST", f"/api/conversations/{conv_id}/members/{target_id}"),
        ("DELETE", f"/api/conversations/{conv_id}/members/{target_id}"),
        ("PATCH", f"/api/conversations/{conv_id}/archive"),
        ("PATCH", f"/api/conversations/{conv_id}/restore"),
        ("DELETE", f"/api/conversations/{conv_id}"),
    ]


def _call(client: TestClient, method: str, path: str, headers: dict | None = None):
    kwargs = {"headers": headers} if headers else {}
    if method == "PUT":
        kwargs["json"] = {"title": "renamed"}
    return client.request(method, path, **kwargs)


# ---------------------------------------------------------------------------
# Anonymous
# ---------------------------------------------------------------------------


class TestAnonymousAccess:
    def test_every_route_rejects_an_anonymous_caller(
        self, client: TestClient, conversation, outsider
    ):
        for method, path in _all_routes(conversation, outsider["id"]):
            response = _call(client, method, path)
            assert response.status_code == 401, f"{method} {path} returned {response.status_code}"

    def test_anonymous_add_member_does_not_create_a_membership(
        self, client: TestClient, conversation, outsider, db
    ):
        """The original report, stated directly."""
        client.post(f"/api/conversations/{conversation}/members/{outsider['id']}")

        assert not ConversationService.is_member(
            db, uuid.UUID(conversation), outsider["uuid"]
        )

    def test_anonymous_delete_does_not_destroy_the_thread(
        self, client: TestClient, conversation, db
    ):
        client.delete(f"/api/conversations/{conversation}")

        assert db.get(Conversation, uuid.UUID(conversation)) is not None


# ---------------------------------------------------------------------------
# Authenticated non-member
# ---------------------------------------------------------------------------


class TestNonMemberAccess:
    def test_every_route_returns_404_for_a_non_member(
        self, client: TestClient, conversation, outsider
    ):
        for method, path in _all_routes(conversation, outsider["id"]):
            response = _call(client, method, path, outsider["headers"])
            assert response.status_code == 404, f"{method} {path} returned {response.status_code}"

    def test_a_real_id_is_indistinguishable_from_a_missing_one(
        self, client: TestClient, conversation, outsider
    ):
        """404 rather than 403, so the routes are not an id oracle."""
        real = client.get(
            f"/api/conversations/{conversation}", headers=outsider["headers"]
        )
        fake = client.get(
            f"/api/conversations/{uuid.uuid4()}", headers=outsider["headers"]
        )

        assert real.status_code == fake.status_code == 404
        assert real.json()["detail"] == fake.json()["detail"]

    def test_non_member_cannot_add_themselves(
        self, client: TestClient, conversation, outsider, db
    ):
        response = client.post(
            f"/api/conversations/{conversation}/members/{outsider['id']}",
            headers=outsider["headers"],
        )
        assert response.status_code == 404
        assert not ConversationService.is_member(
            db, uuid.UUID(conversation), outsider["uuid"]
        )


# ---------------------------------------------------------------------------
# Plain member
# ---------------------------------------------------------------------------


class TestPlainMemberAccess:
    def test_member_can_read_the_conversation(
        self, client: TestClient, conversation, insider
    ):
        response = client.get(
            f"/api/conversations/{conversation}", headers=insider["headers"]
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Roadmap"

    @pytest.mark.parametrize(
        "method,suffix",
        [
            ("PUT", ""),
            ("PATCH", "/archive"),
            ("PATCH", "/restore"),
            ("DELETE", ""),
        ],
    )
    def test_member_cannot_administer(
        self, client: TestClient, conversation, insider, method, suffix
    ):
        response = _call(
            client,
            method,
            f"/api/conversations/{conversation}{suffix}",
            insider["headers"],
        )
        assert response.status_code == 403

    def test_member_cannot_add_someone(
        self, client: TestClient, conversation, insider, outsider, db
    ):
        response = client.post(
            f"/api/conversations/{conversation}/members/{outsider['id']}",
            headers=insider["headers"],
        )
        assert response.status_code == 403
        assert not ConversationService.is_member(
            db, uuid.UUID(conversation), outsider["uuid"]
        )

    def test_member_cannot_remove_someone_else(
        self, client: TestClient, conversation, insider, owner, db
    ):
        response = client.delete(
            f"/api/conversations/{conversation}/members/{owner['id']}",
            headers=insider["headers"],
        )
        assert response.status_code == 403
        assert ConversationService.is_member(
            db, uuid.UUID(conversation), owner["uuid"]
        )


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------


class TestAdminAccess:
    @pytest.fixture(autouse=True)
    def _promote_insider(self, db, conversation, insider):
        _promote(db, conversation, insider["uuid"], ConversationRole.ADMIN)

    def test_admin_can_rename(self, client: TestClient, conversation, insider):
        response = client.put(
            f"/api/conversations/{conversation}",
            json={"title": "Roadmap Q3"},
            headers=insider["headers"],
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Roadmap Q3"

    def test_admin_can_archive_and_restore(
        self, client: TestClient, conversation, insider
    ):
        archived = client.patch(
            f"/api/conversations/{conversation}/archive", headers=insider["headers"]
        )
        assert archived.status_code == 200
        assert archived.json()["archived"] is True

        restored = client.patch(
            f"/api/conversations/{conversation}/restore", headers=insider["headers"]
        )
        assert restored.status_code == 200
        assert restored.json()["archived"] is False

    def test_admin_can_add_a_member(
        self, client: TestClient, conversation, insider, outsider, db
    ):
        response = client.post(
            f"/api/conversations/{conversation}/members/{outsider['id']}",
            headers=insider["headers"],
        )
        assert response.status_code == 201
        assert ConversationService.is_member(
            db, uuid.UUID(conversation), outsider["uuid"]
        )

    def test_admin_cannot_delete_the_conversation(
        self, client: TestClient, conversation, insider, db
    ):
        """Deletion is irreversible and cascades to every message.

        A promoted admin should not be able to do that to the person who
        started the thread.
        """
        response = client.delete(
            f"/api/conversations/{conversation}", headers=insider["headers"]
        )
        assert response.status_code == 403
        assert db.get(Conversation, uuid.UUID(conversation)) is not None


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------


class TestOwnerAccess:
    def test_creator_is_stamped_owner(self, client: TestClient, conversation, owner, db):
        member = ConversationService.get_membership(
            db, uuid.UUID(conversation), owner["uuid"]
        )
        assert member is not None
        assert member.role == ConversationRole.OWNER

    def test_owner_can_rename(self, client: TestClient, conversation, owner):
        response = client.put(
            f"/api/conversations/{conversation}",
            json={"title": "Renamed by owner"},
            headers=owner["headers"],
        )
        assert response.status_code == 200

    def test_owner_can_add_and_remove_members(
        self, client: TestClient, conversation, owner, outsider, db
    ):
        added = client.post(
            f"/api/conversations/{conversation}/members/{outsider['id']}",
            headers=owner["headers"],
        )
        assert added.status_code == 201

        removed = client.delete(
            f"/api/conversations/{conversation}/members/{outsider['id']}",
            headers=owner["headers"],
        )
        assert removed.status_code == 204
        assert not ConversationService.is_member(
            db, uuid.UUID(conversation), outsider["uuid"]
        )

    def test_owner_can_delete(self, client: TestClient, conversation, owner, db):
        response = client.delete(
            f"/api/conversations/{conversation}", headers=owner["headers"]
        )
        assert response.status_code == 204
        assert db.get(Conversation, uuid.UUID(conversation)) is None


# ---------------------------------------------------------------------------
# Leaving
# ---------------------------------------------------------------------------


class TestLeaving:
    def test_a_plain_member_can_leave(
        self, client: TestClient, conversation, insider, db
    ):
        """Leaving is not an administrative act.

        Requiring an admin role to remove yourself would trap a member in a
        thread they want no part of, with no route out.
        """
        response = client.delete(
            f"/api/conversations/{conversation}/members/{insider['id']}",
            headers=insider["headers"],
        )
        assert response.status_code == 204
        assert not ConversationService.is_member(
            db, uuid.UUID(conversation), insider["uuid"]
        )

    def test_leaving_a_conversation_you_are_not_in_is_404(
        self, client: TestClient, conversation, outsider
    ):
        response = client.delete(
            f"/api/conversations/{conversation}/members/{outsider['id']}",
            headers=outsider["headers"],
        )
        assert response.status_code == 404

    def test_after_leaving_the_conversation_is_no_longer_readable(
        self, client: TestClient, conversation, insider
    ):
        client.delete(
            f"/api/conversations/{conversation}/members/{insider['id']}",
            headers=insider["headers"],
        )

        response = client.get(
            f"/api/conversations/{conversation}", headers=insider["headers"]
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# The end-to-end exploit
# ---------------------------------------------------------------------------


class TestPrivateThreadIsNotReadable:
    def test_outsider_cannot_join_and_then_read_the_messages(
        self, client: TestClient, conversation, owner, insider, outsider
    ):
        """The two-request attack from the report, end to end.

        Step 1 used to succeed with no token at all; step 2 then passed the
        messages API's membership check legitimately, because step 1 had made
        it true.
        """
        sent = client.post(
            "/api/messages/",
            json={"conversation_id": conversation, "content": "internal only"},
            headers=owner["headers"],
        )
        assert sent.status_code == 201, sent.text

        # Step 1: try to join, anonymously and then as a logged-in stranger.
        anonymous = client.post(
            f"/api/conversations/{conversation}/members/{outsider['id']}"
        )
        assert anonymous.status_code == 401

        authenticated = client.post(
            f"/api/conversations/{conversation}/members/{outsider['id']}",
            headers=outsider["headers"],
        )
        assert authenticated.status_code == 404

        # Step 2: the messages API still refuses them.
        read = client.get(
            f"/api/messages/conversation/{conversation}",
            headers=outsider["headers"],
        )
        assert read.status_code == 403

    def test_a_real_member_can_still_read(
        self, client: TestClient, conversation, owner, insider
    ):
        """The guard must not have broken the legitimate path."""
        client.post(
            "/api/messages/",
            json={"conversation_id": conversation, "content": "hello team"},
            headers=owner["headers"],
        )

        read = client.get(
            f"/api/messages/conversation/{conversation}",
            headers=insider["headers"],
        )
        assert read.status_code == 200
        assert [m["content"] for m in read.json()] == ["hello team"]


# ---------------------------------------------------------------------------
# get_direct_conversation
# ---------------------------------------------------------------------------


def _user(db, email: str, username: str) -> User:
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


def _direct(db, a: User, b: User) -> Conversation:
    conv = ConversationService.create_conversation(
        db, a.id, ConversationCreate(type=ConversationType.DIRECT)
    )
    db.add(
        ConversationMember(
            conversation_id=conv.id,
            user_id=b.id,
            role=ConversationRole.MEMBER,
        )
    )
    db.commit()
    return conv


class TestGetDirectConversation:
    def test_finds_the_thread_between_exactly_those_two(self, db):
        alice = _user(db, "alice@example.com", "alice")
        bob = _user(db, "bob@example.com", "bob")
        conv = _direct(db, alice, bob)

        found = ConversationService.get_direct_conversation(db, alice.id, bob.id)
        assert found is not None
        assert found.id == conv.id

    def test_returns_none_when_there_is_no_shared_thread(self, db):
        """The `or_` bug: this used to return one of alice's other threads.

        The old predicate matched any conversation where *either* user was a
        member and took the first row, so a user with an existing conversation
        got an arbitrary unrelated one back -- typically one the other party
        was not in at all.
        """
        alice = _user(db, "alice@example.com", "alice")
        bob = _user(db, "bob@example.com", "bob")
        carol = _user(db, "carol@example.com", "carol")

        # alice already talks to carol; she has never talked to bob.
        _direct(db, alice, carol)

        assert ConversationService.get_direct_conversation(db, alice.id, bob.id) is None

    def test_does_not_match_a_group_thread_containing_both(self, db):
        alice = _user(db, "alice@example.com", "alice")
        bob = _user(db, "bob@example.com", "bob")

        group = ConversationService.create_conversation(
            db,
            alice.id,
            ConversationCreate(type=ConversationType.GROUP, title="Team"),
        )
        db.add(
            ConversationMember(
                conversation_id=group.id,
                user_id=bob.id,
                role=ConversationRole.MEMBER,
            )
        )
        db.commit()

        assert ConversationService.get_direct_conversation(db, alice.id, bob.id) is None

    def test_is_symmetric(self, db):
        alice = _user(db, "alice@example.com", "alice")
        bob = _user(db, "bob@example.com", "bob")
        conv = _direct(db, alice, bob)

        forward = ConversationService.get_direct_conversation(db, alice.id, bob.id)
        backward = ConversationService.get_direct_conversation(db, bob.id, alice.id)

        assert forward.id == backward.id == conv.id

    def test_a_user_has_no_direct_conversation_with_themselves(self, db):
        alice = _user(db, "alice@example.com", "alice")
        _direct(db, alice, _user(db, "bob@example.com", "bob"))

        assert ConversationService.get_direct_conversation(db, alice.id, alice.id) is None
