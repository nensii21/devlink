import pytest
from fastapi import status

from app.routers.websockets import manager


@pytest.fixture(autouse=True)
def _reset_ws_manager():
    manager.collaboration_states.clear()
    yield
    manager.collaboration_states.clear()


def test_get_collaboration_status_default(client, register_and_login):
    user_id, token = register_and_login(
        email="status@example.com", username="status_default"
    )
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/users/me/collaboration-status", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["user_id"] == user_id
    assert body["status"] == "available"


def test_set_collaboration_status(client, register_and_login):
    user_id, token = register_and_login(
        email="status@example.com", username="status_set"
    )
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        "/api/v1/users/me/collaboration-status",
        params={"status_val": "coding"},
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "coding"

    get_response = client.get("/api/v1/users/me/collaboration-status", headers=headers)
    assert get_response.json()["status"] == "coding"


def test_set_collaboration_status_invalid(client, register_and_login):
    _, token = register_and_login(email="status@example.com", username="status_invalid")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        "/api/v1/users/me/collaboration-status",
        params={"status_val": "not_a_status"},
        headers=headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_set_collaboration_status_broadcasts_to_ws(client, register_and_login):
    user_id, token = register_and_login(
        email="status@example.com", username="status_ws"
    )
    headers = {"Authorization": f"Bearer {token}"}

    client.put(
        "/api/v1/users/me/collaboration-status",
        params={"status_val": "reviewing_pr"},
        headers=headers,
    )

    assert manager.collaboration_states.get(user_id) == "reviewing_pr"
