import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, ConversationType
from app.models.conversation_member import ConversationMember


@pytest.fixture
def test_conversation(db: Session, register_and_login):
    uid1, token1 = register_and_login("conv1@example.com", "conv1")
    uid2, token2 = register_and_login("conv2@example.com", "conv2")

    conv = Conversation(
        title="Test Chat", type=ConversationType.DIRECT, created_by=uuid.UUID(uid1)
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    m1 = ConversationMember(conversation_id=conv.id, user_id=uuid.UUID(uid1))
    m2 = ConversationMember(conversation_id=conv.id, user_id=uuid.UUID(uid2))
    db.add(m1)
    db.add(m2)
    db.commit()

    return {"id": conv.id, "u1": uid1, "token1": token1, "u2": uid2, "token2": token2}


def test_send_message(client: TestClient, test_conversation):
    cid = test_conversation["id"]
    token = test_conversation["token1"]

    response = client.post(
        "/api/messages/",
        json={"conversation_id": str(cid), "content": "Hello world!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["content"] == "Hello world!"
    assert response.json()["conversation_id"] == str(cid)


def test_get_message(client: TestClient, test_conversation):
    cid = test_conversation["id"]
    token = test_conversation["token1"]

    c = client.post(
        "/api/messages/",
        json={"conversation_id": str(cid), "content": "H1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    mid = c.json()["id"]

    response = client.get(
        f"/api/messages/{mid}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["content"] == "H1"


def test_get_message_not_found(client: TestClient, test_conversation):
    token = test_conversation["token1"]
    response = client.get(
        f"/api/messages/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_list_conversation_messages(client: TestClient, test_conversation):
    cid = test_conversation["id"]
    token = test_conversation["token1"]

    client.post(
        "/api/messages/",
        json={"conversation_id": str(cid), "content": "M1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/api/messages/",
        json={"conversation_id": str(cid), "content": "M2"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        f"/api/messages/conversation/{cid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_my_messages(client: TestClient, test_conversation):
    cid = test_conversation["id"]
    token = test_conversation["token1"]

    client.post(
        "/api/messages/",
        json={"conversation_id": str(cid), "content": "My M1"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/api/messages/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_search_messages(client: TestClient, test_conversation):
    cid = test_conversation["id"]
    token = test_conversation["token1"]

    client.post(
        "/api/messages/",
        json={"conversation_id": str(cid), "content": "Unicorn"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        f"/api/messages/search/{cid}?keyword=Unicorn",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["content"] == "Unicorn"


def test_count_messages(client: TestClient, test_conversation):
    cid = test_conversation["id"]
    token = test_conversation["token1"]

    client.post(
        "/api/messages/",
        json={"conversation_id": str(cid), "content": "C1"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        f"/api/messages/conversation/{cid}/count",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["count"] >= 1


def test_update_message(client: TestClient, test_conversation):
    cid = test_conversation["id"]
    token = test_conversation["token1"]

    c = client.post(
        "/api/messages/",
        json={"conversation_id": str(cid), "content": "C1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    mid = c.json()["id"]

    response = client.put(
        f"/api/messages/{mid}",
        json={"content": "Updated"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Updated"


def test_update_message_not_found(client: TestClient, test_conversation):
    token = test_conversation["token1"]
    response = client.put(
        f"/api/messages/{uuid.uuid4()}",
        json={"content": "U"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_delete_message(client: TestClient, test_conversation):
    cid = test_conversation["id"]
    token = test_conversation["token1"]

    c = client.post(
        "/api/messages/",
        json={"conversation_id": str(cid), "content": "D1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    mid = c.json()["id"]

    response = client.delete(
        f"/api/messages/{mid}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_deleted"] is True
    assert response.json()["content"] == "[Message deleted]"


def test_delete_message_not_found(client: TestClient, test_conversation):
    token = test_conversation["token1"]
    response = client.delete(
        f"/api/messages/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_restore_message(client: TestClient, test_conversation):
    cid = test_conversation["id"]
    token = test_conversation["token1"]

    c = client.post(
        "/api/messages/",
        json={"conversation_id": str(cid), "content": "R1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    mid = c.json()["id"]

    client.delete(f"/api/messages/{mid}", headers={"Authorization": f"Bearer {token}"})

    response = client.patch(
        f"/api/messages/{mid}/restore", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_deleted"] is False


def test_restore_message_not_found(client: TestClient, test_conversation):
    token = test_conversation["token1"]
    response = client.patch(
        f"/api/messages/{uuid.uuid4()}/restore",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
# ------------------------------------------------------------------
# Typing indicator  (issue #337)
# ------------------------------------------------------------------


def test_set_typing_returns_204(client: TestClient, test_conversation):
    cid = test_conversation["id"]
    token = test_conversation["token1"]

    response = client.post(
        f"/api/messages/conversation/{cid}/typing",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


def test_get_typing_returns_other_user(client: TestClient, test_conversation):
    """When user 1 is typing, user 2's GET should report user 1's id."""
    from app.services.message_service import MessageService

    # Clear any leftover state from previous tests so this is deterministic.
    MessageService._typing_store.clear()

    cid = test_conversation["id"]
    token1 = test_conversation["token1"]
    token2 = test_conversation["token2"]
    uid1 = test_conversation["u1"]

    # User 1 says they're typing.
    client.post(
        f"/api/messages/conversation/{cid}/typing",
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User 2 asks who's typing — should see user 1.
    response = client.get(
        f"/api/messages/conversation/{cid}/typing",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"] == str(cid)
    assert uid1 in body["typing_user_ids"]


def test_get_typing_excludes_self(client: TestClient, test_conversation):
    """A user should never see their own typing indicator echoed back."""
    from app.services.message_service import MessageService

    MessageService._typing_store.clear()

    cid = test_conversation["id"]
    token1 = test_conversation["token1"]
    uid1 = test_conversation["u1"]

    client.post(
        f"/api/messages/conversation/{cid}/typing",
        headers={"Authorization": f"Bearer {token1}"},
    )

    response = client.get(
        f"/api/messages/conversation/{cid}/typing",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert response.status_code == 200
    assert uid1 not in response.json()["typing_user_ids"]


def test_stop_typing_clears_state(client: TestClient, test_conversation):
    """DELETE /typing immediately removes the user from the typing set."""
    from app.services.message_service import MessageService

    MessageService._typing_store.clear()

    cid = test_conversation["id"]
    token1 = test_conversation["token1"]
    token2 = test_conversation["token2"]

    client.post(
        f"/api/messages/conversation/{cid}/typing",
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User 1 stops typing.
    stop = client.delete(
        f"/api/messages/conversation/{cid}/typing",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert stop.status_code == 204

    # User 2 should now see an empty typing list.
    response = client.get(
        f"/api/messages/conversation/{cid}/typing",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 200
    assert response.json()["typing_user_ids"] == []


def test_get_typing_empty_when_nobody_typing(client: TestClient, test_conversation):
    from app.services.message_service import MessageService

    MessageService._typing_store.clear()

    cid = test_conversation["id"]
    token1 = test_conversation["token1"]

    response = client.get(
        f"/api/messages/conversation/{cid}/typing",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert response.status_code == 200
    assert response.json()["typing_user_ids"] == []
