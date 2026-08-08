import pytest
import uuid

def test_message_draft_lifecycle(client, register_and_login, db):
    user_id, token = register_and_login("draft_user@example.com", "draft_user")
    headers = {"Authorization": f"Bearer {token}"}

    from app.models.conversation import Conversation
    conv = Conversation(title="Test Draft Conversation", created_by=uuid.UUID(str(user_id)))
    db.add(conv)
    db.commit()
    db.refresh(conv)
    conv_id = str(conv.id)

    # 1. Check no draft exists initially
    res = client.get(f"/api/messages/drafts/{conv_id}", headers=headers)
    assert res.status_code == 200
    assert res.json() is None

    # 2. Save auto-saved draft
    save_payload = {"conversation_id": conv_id, "content": "Hello, this is an auto-saved draft message"}
    res = client.post("/api/messages/drafts/", json=save_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["content"] == "Hello, this is an auto-saved draft message"

    # 3. Retrieve saved draft
    res = client.get(f"/api/messages/drafts/{conv_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["content"] == "Hello, this is an auto-saved draft message"

    # 4. List all drafts
    res = client.get("/api/messages/drafts/", headers=headers)
    assert res.status_code == 200
    drafts = res.json()
    assert len(drafts) >= 1
    assert any(d["conversation_id"] == conv_id for d in drafts)

    # 5. Clear draft explicitly
    res = client.delete(f"/api/messages/drafts/{conv_id}", headers=headers)
    assert res.status_code == 204

    # 6. Verify cleared draft
    res = client.get(f"/api/messages/drafts/{conv_id}", headers=headers)
    assert res.status_code == 200
    assert res.json() is None
