from fastapi.testclient import TestClient


def test_get_project_collaboration_metrics_unauthenticated(client: TestClient):
    response = client.get("/api/projects/1/collaboration-metrics")
    assert response.status_code == 401


def test_get_project_collaboration_metrics(client: TestClient, register_and_login):
    _, token = register_and_login("collabuser1@example.com", "pass123456")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/projects/1/collaboration-metrics", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["project_id"] == 1
    assert "active_members" in data
    assert "avg_response_time_hours" in data
    assert "messages_exchanged" in data
    assert "tasks_completed" in data
    assert "applications_received" in data
    assert "collaboration_score" in data
    assert "daily_activity" in data
