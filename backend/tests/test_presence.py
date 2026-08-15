from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import pytest
from fastapi.testclient import TestClient
from app.routers.websockets import manager


def _ws_url(client: TestClient, token: str) -> str:
    base = "ws://testserver/ws/collab"
    return f"{base}?{urlencode({'token': token})}"


def test_presence_connect_disconnect(client: TestClient, register_and_login):
    # Ensure manager state is clean
    manager.active_connections.clear()
    manager.presence_states.clear()
    manager.last_activity.clear()

    user_id, token = register_and_login("p1@example.com", "puser1")

    # Connect
    with client.websocket_connect(_ws_url(client, token)) as ws:
        # Connected event
        event = ws.receive_json()
        assert event["type"] == "connected"
        assert event["user_id"] == user_id

        # Verify manager holds "online" presence
        assert manager.presence_states.get(user_id) == "online"
        assert user_id in manager.last_activity

        # Fetch status via GET REST endpoint
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get(f"/ws/presence/{user_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "online"

    # Disconnected!
    # Verify status changed to offline and cleaned up
    assert user_id not in manager.active_connections
    assert user_id not in manager.presence_states
    assert user_id not in manager.last_activity

    # Fetch status via GET REST endpoint should return "offline"
    resp = client.get(f"/ws/presence/{user_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "offline"


def test_presence_manual_update(client: TestClient, register_and_login):
    manager.active_connections.clear()
    manager.presence_states.clear()
    manager.last_activity.clear()

    user_id, token = register_and_login("p2@example.com", "puser2")

    with client.websocket_connect(_ws_url(client, token)) as ws:
        ws.receive_json()  # connected

        # Update status to busy
        ws.send_json({"type": "presence_update", "status": "busy"})

        # Should receive broadcast status changed event
        event = ws.receive_json()
        assert event["type"] == "presence.status_changed"
        assert event["user_id"] == user_id
        assert event["status"] == "busy"

        # Verify manager holds "busy"
        assert manager.presence_states.get(user_id) == "busy"

        # Try invalid status update, should return error message
        ws.send_json({"type": "presence_update", "status": "invalid_status"})
        err_event = ws.receive_json()
        assert err_event["type"] == "error"
        assert "Invalid presence status" in err_event["message"]


def test_presence_query(client: TestClient, register_and_login):
    manager.active_connections.clear()
    manager.presence_states.clear()
    manager.last_activity.clear()

    user_id1, token1 = register_and_login("p3@example.com", "puser3")
    user_id2, token2 = register_and_login("p4@example.com", "puser4")

    # Connect user 2 first
    with client.websocket_connect(_ws_url(client, token2)) as ws2:
        ws2.receive_json()  # connected

        # Connect user 1
        with client.websocket_connect(_ws_url(client, token1)) as ws1:
            ws1.receive_json()  # connected

            # Query all presences
            ws1.send_json({"type": "presence_query"})
            response = ws1.receive_json()
            assert response["type"] == "presence.query_response"
            assert response["presences"][user_id1] == "online"
            assert response["presences"][user_id2] == "online"

            # Query specific user
            ws1.send_json({"type": "presence_query", "user_ids": [user_id2]})
            response2 = ws1.receive_json()
            assert response2["type"] == "presence.query_response"
            assert user_id2 in response2["presences"]
            assert response2["presences"][user_id2] == "online"
            assert user_id1 not in response2["presences"]


@pytest.mark.asyncio
async def test_presence_timeout():
    manager.active_connections.clear()
    manager.presence_states.clear()
    manager.last_activity.clear()

    user_id = "test-user-id"
    manager.presence_states[user_id] = "online"
    # Set activity to 6 minutes ago
    manager.last_activity[user_id] = datetime.now(timezone.utc) - timedelta(minutes=6)

    # Run check timeouts (default threshold is 5 mins / 300 secs)
    await manager.check_timeouts(timeout_seconds=300)

    # Should transition to away
    assert manager.presence_states.get(user_id) == "away"

    # Any new activity should transition back to online
    await manager.update_activity(user_id)
    assert manager.presence_states.get(user_id) == "online"


def test_presence_broadcast_to_others(client: TestClient, register_and_login):
    manager.active_connections.clear()
    manager.presence_states.clear()
    manager.last_activity.clear()

    user_id_a, token_a = register_and_login("pa@example.com", "user_a")
    user_id_b, token_b = register_and_login("pb@example.com", "user_b")

    with client.websocket_connect(_ws_url(client, token_a)) as ws_a:
        ws_a.receive_json()  # connected event for A

        # Now B connects
        with client.websocket_connect(_ws_url(client, token_b)) as ws_b:
            ws_b.receive_json()  # connected event for B

            # A should receive the presence status changed event for B
            event = ws_a.receive_json()
            assert event["type"] == "presence.status_changed"
            assert event["user_id"] == user_id_b
            assert event["status"] == "online"
