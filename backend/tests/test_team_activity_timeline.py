from fastapi.testclient import TestClient


def test_get_team_activity_timeline_unauthenticated(client: TestClient):
    response = client.get("/api/projects/1/activity-timeline")
    assert response.status_code == 401


def test_get_team_activity_timeline(client: TestClient, register_and_login):
    _, token = register_and_login("teamuser1@example.com", "pass123456")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        "/api/projects/1/activity-timeline?page=1&limit=5", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == 1
    assert "items" in data
    assert len(data["items"]) <= 5
    assert "total" in data
    assert "has_more" in data


def test_team_activity_timeline_filter_by_type(client: TestClient, register_and_login):
    _, token = register_and_login("teamuser2@example.com", "pass123456")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        "/api/projects/1/activity-timeline?activity_type=member_joined", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["activity_type"] == "member_joined"


def test_create_team_activity_event(client: TestClient, register_and_login):
    _, token = register_and_login("teamuser3@example.com", "pass123456")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "activity_type": "file_uploaded",
        "title": "Uploaded mock_spec.pdf",
        "description": "Mock specification document for testing",
        "actor_name": "Test User",
        "metadata_info": {"size_bytes": 1024},
    }

    response = client.post(
        "/api/projects/1/activity-timeline", json=payload, headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Uploaded mock_spec.pdf"
    assert data["activity_type"] == "file_uploaded"
