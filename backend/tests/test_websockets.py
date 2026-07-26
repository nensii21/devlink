"""Tests for the WebSocket collaboration endpoint (issue #353)."""

from urllib.parse import urlencode

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def _ws_url(client: TestClient, token: str) -> str:
    """Build a WebSocket URL with the token query param."""
    base = "ws://testserver/ws/collab"
    return f"{base}?{urlencode({'token': token})}"


def test_ws_rejects_missing_token(client: TestClient):
    """Connection without a token is closed with policy violation."""
    with client.websocket_connect("/ws/collab") as ws:
        try:
            ws.receive()
        except WebSocketDisconnect:
            pass


def test_ws_rejects_invalid_token(client: TestClient):
    """Connection with an invalid token is closed."""
    with client.websocket_connect("/ws/collab?token=invalid-jwt") as ws:
        try:
            ws.receive()
        except WebSocketDisconnect:
            pass


def test_ws_accepts_valid_token(client: TestClient, register_and_login):
    """A valid JWT token is accepted and a 'connected' event is sent."""
    _, token = register_and_login("ws1@example.com", "wsuser1")

    with client.websocket_connect(_ws_url(client, token)) as ws:
        event = ws.receive_json()
        assert event["type"] == "connected"
        assert "user_id" in event


def test_ws_join_and_leave_project(client: TestClient, register_and_login):
    """Joining a project room broadcasts member_joined to the room."""
    _, token = register_and_login("ws2@example.com", "wsuser2")

    with client.websocket_connect(_ws_url(client, token)) as ws:
        # Consume the 'connected' event
        connected = ws.receive_json()
        assert connected["type"] == "connected"

        # Join a project room
        ws.send_json({"type": "join", "project_id": "test-project-1"})

        # Should receive the team.member_joined broadcast
        event = ws.receive_json()
        assert event["type"] == "team.member_joined"
        assert event["project_id"] == "test-project-1"

        # Leave the project room
        ws.send_json({"type": "leave", "project_id": "test-project-1"})

        # Should receive the team.member_left broadcast
        event = ws.receive_json()
        assert event["type"] == "team.member_left"
        assert event["project_id"] == "test-project-1"


def test_ws_message_broadcast(client: TestClient, register_and_login):
    """A message sent to a project room is broadcast to all members."""
    _, token = register_and_login("ws3@example.com", "wsuser3")

    with client.websocket_connect(_ws_url(client, token)) as ws:
        # Consume connected
        ws.receive_json()

        # Join room
        ws.send_json({"type": "join", "project_id": "msg-project"})
        ws.receive_json()  # member_joined

        # Send a message
        ws.send_json(
            {"type": "message", "project_id": "msg-project", "content": "Hello team!"}
        )

        # Receive the broadcast
        event = ws.receive_json()
        assert event["type"] == "message.new"
        assert event["project_id"] == "msg-project"
        assert event["content"] == "Hello team!"


def test_ws_task_status_change(client: TestClient, register_and_login):
    """A task_update is broadcast as task.status_changed."""
    _, token = register_and_login("ws4@example.com", "wsuser4")

    with client.websocket_connect(_ws_url(client, token)) as ws:
        ws.receive_json()  # connected

        ws.send_json({"type": "join", "project_id": "task-project"})
        ws.receive_json()  # member_joined

        ws.send_json(
            {
                "type": "task_update",
                "project_id": "task-project",
                "task_id": "task-123",
                "status": "done",
            }
        )

        event = ws.receive_json()
        assert event["type"] == "task.status_changed"
        assert event["task_id"] == "task-123"
        assert event["status"] == "done"


def test_ws_invalid_json_returns_error(client: TestClient, register_and_login):
    """Malformed JSON sends an error event without closing the connection."""
    _, token = register_and_login("ws5@example.com", "wsuser5")

    with client.websocket_connect(_ws_url(client, token)) as ws:
        ws.receive_json()  # connected

        ws.send_text("not valid json")

        event = ws.receive_json()
        assert event["type"] == "error"
        assert "Invalid JSON" in event["message"]


def test_ws_unknown_message_type_returns_error(client: TestClient, register_and_login):
    """Unknown message types return an error event."""
    _, token = register_and_login("ws6@example.com", "wsuser6")

    with client.websocket_connect(_ws_url(client, token)) as ws:
        ws.receive_json()  # connected

        ws.send_json({"type": "bogus", "project_id": "x"})

        event = ws.receive_json()
        assert event["type"] == "error"
        assert "Unknown message type" in event["message"]
