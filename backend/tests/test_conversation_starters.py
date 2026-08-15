from __future__ import annotations

import uuid

from app.models.user import User
from app.services.conversation_starter_service import ConversationStarterService


def _make_user(db, username: str, email: str) -> User:
    user = User(
        id=uuid.uuid4(),
        first_name="Test",
        last_name="User",
        username=username,
        email=email,
        password_hash="hashed",
        headline="Full Stack Developer",
        bio="I build web apps with FastAPI and React.",
    )
    db.add(user)
    db.commit()
    return user


def test_conversation_starters_endpoint_returns_suggestions(client, register_and_login):
    """POST /api/conversation-starters returns 3-5 suggestions with confidence."""
    current_user_id, token = register_and_login(
        "starter_sender@example.com", "starter_sender"
    )
    target_id, _ = register_and_login("starter_target@example.com", "starter_target")

    r = client.post(
        "/api/conversation-starters",
        json={"target_user_id": target_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert 3 <= len(body["suggestions"]) <= 5
    assert body["target_user_id"] == target_id
    assert body["target_user_name"]
    for suggestion in body["suggestions"]:
        assert suggestion["text"]
        assert 0.0 <= suggestion["confidence"] <= 1.0


def test_conversation_starters_rejects_self(client, register_and_login):
    """Generating starters for yourself returns 400."""
    current_user_id, token = register_and_login(
        "starter_self@example.com", "starter_self"
    )
    r = client.post(
        "/api/conversation-starters",
        json={"target_user_id": current_user_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400


def test_conversation_starters_rejects_missing_user(client, register_and_login):
    """Generating starters for a non-existent user returns 404."""
    _, token = register_and_login("starter_miss@example.com", "starter_miss")
    r = client.post(
        "/api/conversation-starters",
        json={"target_user_id": str(uuid.uuid4())},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


def test_conversation_starters_requires_auth(client, register_and_login):
    """The endpoint requires authentication."""
    target_id, _ = register_and_login("starter_noauth@example.com", "starter_noauth")
    r = client.post(
        "/api/conversation-starters",
        json={"target_user_id": target_id},
    )
    assert r.status_code == 401


def test_conversation_starters_service_fallback_without_api_key(db, monkeypatch):
    """Service falls back to default starters when no OpenAI key is set."""
    monkeypatch.setattr(
        "app.services.conversation_starter_service.settings.OPENAI_API_KEY", ""
    )
    current_user = _make_user(db, "svc_cur", "svc_cur@example.com")
    target_user = _make_user(db, "svc_tgt", "svc_tgt@example.com")

    suggestions = ConversationStarterService.generate_conversation_starters(
        db=db,
        current_user_id=str(current_user.id),
        target_user_id=str(target_user.id),
    )
    assert 3 <= len(suggestions) <= 5
    for suggestion in suggestions:
        assert suggestion.text
        assert 0.0 <= suggestion.confidence <= 1.0
